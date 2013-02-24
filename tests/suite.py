# coding: utf-8

import os
import tempfile
import unittest
from flask import json
from yuan.app import create_app
from yuan.models import db, Account


class BaseSuite(unittest.TestCase):
    def setUp(self):
        config = {'TESTING': True}
        config['SECRET_KEY'] = 'secret-key-for-test'
        config['PACKAGE_STORAGE'] = 'data'

        self.db_fd, self.db_file = tempfile.mkstemp()
        config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s' % self.db_file

        app = create_app(config)
        self.app = app

        self.client = app.test_client()

        db.create_all()

        if hasattr(self, 'prehook'):
            self.prehook()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_file)

        if hasattr(self, 'posthook'):
            self.posthook()

    def create_account(self):
        # create account
        user = Account(name='lepture', password='demo', email='a@b.c')
        user.save()

        group = Account(name='yuan', role=user.id)
        group.save()

    def login_account(self):
        rv = self.client.post(
            '/account/login',
            content_type='application/json',
            data=json.dumps({'account': 'lepture', 'password': 'demo'})
        )
        data = json.loads(rv.data)
        auth = data['data']
        return {'Authorization': 'Yuan ' + auth}
