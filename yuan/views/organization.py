# coding: utf-8

from flask import Blueprint
from flask import g, url_for, request, flash
from flask import render_template, redirect, abort
from flask.ext.babel import gettext as _
from ..helpers import require_user
from ..models import Account, Team, get_user_organizations
from ..forms import OrgForm, TeamForm

bp = Blueprint('organization', __name__)


@bp.route('/', methods=['GET', 'POST'])
@require_user
def home():
    form = OrgForm()
    if form.validate_on_submit():
        org = form.save(g.user)
        return redirect(url_for('.detail', name=org.name))
    orgs = get_user_organizations(g.user.id)
    dct = {'orgs': orgs, 'form': form}
    return render_template('organization/home.html', **dct)


@bp.route('/<name>', methods=['GET', 'POST', 'DELETE'])
@require_user
def detail(name):
    org = Account.query.filter_by(name=name).first_or_404()
    if org.account_type != 'org':
        return abort(404)
    if org.permission_admin.can():
        form = OrgForm(obj=org)
    else:
        form = None
    if form and form.validate_on_submit():
        form.populate_obj(org)
        org.save()
        return redirect(url_for('.detail', name=org.name))
    dct = {'org': org, 'form': form}
    dct['teams'] = Team.query.filter_by(owner_id=org.id).all()
    return render_template('organization/detail.html', **dct)


@bp.route('/<name>/team/', methods=['GET', 'POST'])
@require_user
def team_index(name):
    org = Account.query.filter_by(name=name).first_or_404()
    if org.permission_admin.can():
        form = TeamForm()
    else:
        form = None
    if form and form.validate_on_submit():
        team = form.save(org)
        return redirect(url_for('.team', name=name, ident=team.id))
    dct = {'org': org, 'form': form}
    dct['teams'] = Team.query.filter_by(owner_id=org.id).all()
    return render_template('organization/team-index.html', **dct)


@bp.route('/<name>/team/<int:ident>', methods=['GET', 'POST', 'DELETE'])
@require_user
def team(name, ident):
    org = Account.query.filter_by(name=name).first_or_404()
    team = Team.query.get_or_404(ident)
    if team.owner_id != org.id:
        return abort(404)
    if request.method == 'POST' and org.permission_admin.can():
        username = request.form.get('username', None)
        user = None
        if username:
            user = Account.query.filter_by(name=username).first()
        if user and user.account_type == 'user':
            team.members.append(user)
            team.save()
        else:
            flash(_('This user does not exist.'), 'error')
        return redirect(url_for('.team', name=name, ident=ident))
    dct = {'org': org, 'team': team}
    return render_template('organization/team.html', **dct)
