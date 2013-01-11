# coding: utf-8

from flask import Blueprint
from flask import g, url_for
from flask import render_template, redirect, abort
from ..helpers import require_user
from ..models import db, Account, GroupMember
from ..forms import GroupForm

bp = Blueprint('group', __name__)


@bp.route('/', methods=['GET', 'POST'])
@require_user
def home():
    form = GroupForm()
    if form.validate_on_submit():
        group = form.save(g.user)
        return redirect(url_for('.detail', name=group.name))
    user_id = g.user.id
    admins = Account.query.filter_by(role=user_id, account_type='org').all()
    joins = GroupMember.get_groups(user_id=user_id)
    dct = {'admins': admins, 'joins': joins, 'form': form}
    return render_template('group-home.html', **dct)


@bp.route('/<name>', methods=['GET', 'POST', 'DELETE'])
@require_user
def detail(name):
    group = Account.query.filter_by(name=name).first_or_404()
    if group.account_type != 'org':
        return abort(404)
    if group.role == g.user.id:
        # current user is the owner
        form = GroupForm(obj=group)
    else:
        form = None
    if form and form.validate_on_submit():
        form.populate_obj(group)
        db.session.add(group)
        db.session.commit()
        return redirect(url_for('.detail', name=group.name))
    members = GroupMember.get_members(group.id)
    dct = {'group': group, 'form': form, 'members': members}
    return render_template('group-detail.html', **dct)


@bp.route('/<name>/<userid>', methods=['POST', 'DELETE'])
@require_user
def member(name, userid):
    pass
