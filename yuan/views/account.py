# coding: utf-8

import werkzeug
from flask import Blueprint
from flask import g, request, flash
from flask import url_for, current_app
from flask import render_template, redirect, jsonify
from flask.ext.babel import gettext as _
from ..models import Account, Member
from ..helpers import login_user, logout_user, require_login
from ..helpers import create_auth_token, verify_auth_token
from ..forms import SignupForm, SigninForm, SettingForm
from ..forms import FindForm, ResetForm
from ..tasks.mail import signup_mail, find_mail

bp = Blueprint('account', __name__)


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    next_url = request.args.get('next', url_for('.setting'))
    token = request.args.get('token')
    if token:
        user = verify_auth_token(token, expires=1)
        if not user:
            flash(_('Invalid or expired token.'), 'error')
            return redirect(next_url)
        user.role = 2
        user.save()
        login_user(user)
        flash(_('This account is verified.'), 'info')
        return redirect(next_url)

    form = SignupForm()
    if form.validate_on_submit():
        user = form.save()
        login_user(user)
        # send signup mail to user
        msg = signup_mail(user)
        if current_app.debug:
            return msg.html
        flash(_('We have sent you an activate email, check your inbox.'),
              'info')
        return redirect(next_url)
    return render_template('signup.html', form=form)


@bp.route('/signin', methods=['GET', 'POST'])
def signin():
    next_url = request.args.get('next', '/')
    if g.user:
        return redirect(next_url)
    form = SigninForm()
    if form.validate_on_submit():
        login_user(form.user, form.permanent.data)
        return redirect(next_url)
    return render_template('signin.html', form=form)


@bp.route('/signout')
def signout():
    next_url = request.args.get('next', '/')
    logout_user()
    return redirect(next_url)


@bp.route('/setting', methods=['GET', 'POST'])
@require_login
def setting():
    form = SettingForm(obj=g.user)
    next_url = request.args.get('next', url_for('.setting'))
    if form.validate_on_submit():
        user = Account.query.get(g.user.id)
        form.populate_obj(user)
        user.save()
        return redirect(next_url)
    return render_template('setting.html', form=form)


@bp.route('/member')
@require_login
def member():
    name = request.args.get('name')
    user = Account.query.filter_by(name=name).first()
    if not user:
        flash(_('This user or family does not exist.'), 'warn')
        return redirect(url_for('.setting'))

    action = request.args.get('action', 'add')
    if action == 'quit':
        relation = Member.query.filter_by(
            master_id=user.id, member_id=g.user.id
        ).first()
    else:
        relation = Member.query.filter_by(
            master_id=g.user.id, member_id=user.id
        ).first()
    if action == 'add' and not relation:
        relation = Member(master_id=g.user.id, member_id=user.id)
        relation.save()
    elif action == 'remove' and relation:
        relation.delete()
    elif action == 'quit' and relation:
        relation.delete()
    return redirect(url_for('.setting'))


@bp.route('/find', methods=['GET', 'POST'])
def find():
    if g.user:
        return redirect('/')
    form = FindForm()
    if form.validate_on_submit():
        msg = find_mail(form.user)
        if current_app.debug:
            return msg.html
        flash(_('We have sent you an email, check your inbox.'), 'info')
        return redirect(url_for('.find'))
    return render_template('find.html', form=form)


@bp.route('/reset', methods=['GET', 'POST'])
def reset():
    if g.user:
        return redirect('/')
    token = request.values.get('token')
    if not token:
        flash(_('Token is missing.'), 'error')
        return redirect('/')
    user = verify_auth_token(token, expires=1)
    if not user:
        flash(_('Invalid or expired token.'), 'error')
        return redirect(url_for('.find'))
    form = ResetForm()
    if form.validate_on_submit():
        user.password = user.create_password(form.password.data)
        user.save()
        login_user(user)
        flash(_('Your password is updated.'), 'info')
        return redirect(url_for('.setting'))
    return render_template('reset.html', form=form, token=token)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if not request.json:
        response = jsonify(
            status='error',
            message=_('Only application/json is allowed.')
        )
        response.status_code = 415
        return response
    data = werkzeug.datastructures.MultiDict(request.json)
    form = SignupForm(data, csrf_enabled=False)
    if not form.validate():
        message = []
        for name in form.errors:
            errors = form.errors[name]
            msg = '%s: ' % name
            for error in errors:
                msg = '%s %s' % (msg, error)
            message.append(msg)

        return jsonify(
            status='error',
            message='\n'.join(message)
        )

    user = form.save()
    signup_mail(user)
    auth = create_auth_token(user)
    return jsonify(
        status='success',
        data=auth,
    )


@bp.route('/login', methods=['POST'])
def login():
    if not request.json:
        response = jsonify(
            status='error',
            message=_('Only application/json is allowed.')
        )
        response.status_code = 415
        return response

    data = request.json
    if 'account' in data and 'password' in data:
        account = data['account']
        if '@' in account:
            user = Account.query.filter_by(email=account).first()
        else:
            user = Account.query.filter_by(name=account).first()
        if user and user.check_password(data['password']):
            auth = create_auth_token(user)
            return jsonify(status='success', data=auth)
        response = jsonify(
            status='error',
            message=_('Wrong account or password')
        )
        response.status_code = 403
        return response
    response = jsonify(
        status='error',
        message=_('Parameters missing.')
    )
    response.status_code = 403
    return response
