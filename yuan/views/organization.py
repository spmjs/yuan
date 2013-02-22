# coding: utf-8

from flask import Blueprint
from flask import g, url_for
from flask import render_template, redirect, abort
from ..helpers import require_user
from ..models import Account
from ..forms import OrgForm

bp = Blueprint('organization', __name__)


@bp.route('/', methods=['GET', 'POST'])
@require_user
def home():
    form = OrgForm()
    if form.validate_on_submit():
        org = form.save(g.user)
        return redirect(url_for('.detail', name=org.name))
    return render_template('organization/home.html', form=form)


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

    return render_template('organization/detail.html', form=form)
