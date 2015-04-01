# coding: utf-8

from flask import g
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from ..models import db, Account, Member


class BaseView(ModelView):
    column_display_pk = True
    can_create = False
    can_edit = False

    def is_accessible(self):
        if not g.user:
            return False
        if g.user.id == 1:
            return True
        return g.user.role > 40


class HomeView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

    def is_accessible(self):
        if not g.user:
            return False
        if g.user.id == 1:
            return True
        return g.user.role > 40


class UserView(BaseView):
    can_edit = True
    column_exclude_list = ('password', 'token', 'description')
    form_excluded_columns = ('password', 'created', 'token')

    column_labels = dict(
        comment_service='Comment'
    )
    column_formatters = dict(
        created=lambda c, m, p: m.created.strftime('%Y-%m-%d %H:%M')
    )


class MemberView(BaseView):
    column_auto_select_related = True


admin = Admin(name='Yuan', index_view=HomeView())
admin.add_view(UserView(Account, db.session, endpoint='users'))
admin.add_view(MemberView(Member, db.session))
