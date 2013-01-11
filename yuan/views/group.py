# coding: utf-8

from flask import Blueprint
from flask import g
from flask import render_template, redirect, url_for
from ..helpers import require_user
from ..models import Account, GroupMember
from ..forms import GroupForm

bp = Blueprint('group', __name__)


@bp.route('/', methods=['GET', 'POST'])
@require_user
def home():
    form = GroupForm()
    if form.validate_on_submit():
        group = form.save(g.user)
        return redirect(url_for('.group', name=group.name))
    user_id = g.user.id
    admins = Account.query.filter_by(role=user_id).all()
    joins = GroupMember.get_groups(user_id=user_id)
    dct = {'admins': admins, 'joins': joins, 'form': form}
    return render_template('group-home.html', **dct)


@bp.route('/<name>', methods=['GET', 'POST', 'DELETE'])
@require_user
def group(name):
    # POST is edit
    pass


@bp.route('/<name>/<userid>', methods=['POST', 'DELETE'])
@require_user
def member(name, userid):
    pass
