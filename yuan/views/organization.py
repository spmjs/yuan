# coding: utf-8

from flask import Blueprint
from flask import g, url_for, request
from flask import render_template, redirect, abort
from ..helpers import require_user
from ..models import Account, Team
from ..forms import OrgForm, TeamForm

bp = Blueprint('organization', __name__)


@bp.route('/', methods=['GET', 'POST'])
@require_user
def home():
    form = OrgForm()
    if form.validate_on_submit():
        org = form.save(g.user)
        return redirect(url_for('.detail', name=org.name))
    user_id = g.user.id
    admins = Account.query.filter_by(role=user_id, account_type='org').all()
    dct = {'admins': admins, 'form': form}
    return render_template('organization/home.html', **dct)


@bp.route('/<name>', methods=['GET', 'POST', 'DELETE'])
@require_user
def detail(name):
    org = Account.query.filter_by(name=name).first_or_404()
    if org.account_type != 'org':
        return abort(404)
    if org.permission_edit.can():
        form = OrgForm(obj=org)
    else:
        form = None
    if form and form.validate_on_submit():
        form.populate_obj(org)
        org.save()
        return redirect(url_for('.detail', name=org.name))
    dct = {'organization': org, 'form': form}
    return render_template('organization/detail.html', **dct)


@bp.route('/<name>/team/', methods=['GET', 'POST'])
@require_user
def team_index(name):
    org = Account.query.filter_by(name=name).first_or_404()
    if org.permission_edit.can():
        form = TeamForm()
    else:
        form = None
    if form and form.validate_on_submit():
        team = form.save(org)
        return redirect(url_for('.team', name=name, ident=team.id))
    return render_template('organization/team-index.html', form=form)


@bp.route('/<name>/team/<int:ident>', methods=['GET', 'POST', 'DELETE'])
@require_user
def team(name, ident):
    org = Account.query.filter_by(name=name).first_or_404()
    team = Team.query.get_or_404(ident)
    if team.owner_id != org.id:
        return abort(404)
    if request.method == 'POST':
        username = request.form.get('username', None)
        user = None
        if username:
            user = Account.query.filter_by(name=username).first()
        if not user:
            #TODO flash message
            pass
        else:
            team.members.append(user)
            team.save()
        return redirect(url_for('.team', name=name, ident=ident))
    return render_template('organization/team.html', team=team)
