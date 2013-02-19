# coding: utf-8

from flask.ext.wtf import TextField, BooleanField
from flask.ext.wtf.html5 import URLField
from flask.ext.wtf import Required, Length, Optional, URL
from flask.ext.babel import lazy_gettext as _

from ._base import BaseForm
from ..models import Project


class ProjectForm(BaseForm):
    name = TextField(
        _('Name'), validators=[Required(), Length(max=40)]
    )
    homepage = URLField(
        _('Homepage'), validators=[Optional(), URL()]
    )
    repository = TextField(
        _('Repository'), validators=[Optional()]
    )
    description = TextField(
        _('Description'), validators=[Optional(), Length(max=400)]
    )
    private = BooleanField(
        _('This is a private project.'),
        description=_('We encourage public projects.')
    )
    keywords = TextField(_('Keywords'))

    def __init__(self, *args, **kwargs):
        self._owner = kwargs.get('owner', None)
        super(ProjectForm, self).__init__(*args, **kwargs)

    def validate_name(self, field):
        if self._obj and self._obj.name == field.data:
            return
        count = Project.query.filter_by(
            owner_id=self._owner.id, name=field.data
        ).count()
        if count:
            raise ValueError(_('This name has been registered.'))

    def save(self, org=None):
        data = dict(self.data)
        if org:
            data['owner_id'] = org.id
        else:
            data['owner_id'] = self._owner.id
        proj = Project(**data)
        proj.save()
        return proj
