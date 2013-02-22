# coding: utf-8

from flask import Blueprint
from flask import g, url_for
from flask import render_template, redirect, abort
from ..helpers import require_user
from ..models import Account
from ..forms import OrgSettingForm, OrgForm

bp = Blueprint('organization', __name__)


@bp.route('/', methods=['GET', 'POST'])
@require_user
def home():
    form = OrgForm()
    if form.validate_on_submit():
        org = form.save(g.user.id)
        return redirect(url_for('.organization', name=org.name))
    return render_template('organization/home.html', form=form)


@bp.route('/<name>', methods=['GET', 'POST', 'DELETE'])
@require_user
def organization(name):
    org = Account.query.filter_by(name=name).first_or_404()

    if org.account_type != 'org':
        return abort(404)
    if org.permission_admin.can():
        form = OrgSettingForm(obj=org)
    else:
        form = None

    if form and form.validate_on_submit():
        form.populate_obj(org)
        org.save()
        return redirect(url_for('.organization', name=org.name))

    dct = {'org': org, 'form': form}
    return render_template('organization/organization.html', **dct)
