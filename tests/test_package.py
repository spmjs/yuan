# coding: utf-8

from flask import json
from yuan.models import db, Account

from .suite import BaseSuite


class AuthSuite(BaseSuite):
    def prehook(self):
        # create account
        user = Account(name='lepture', password='demo', email='a@b.c')
        db.session.add(user)
        db.session.commit()

        group = Account(name='yuan', role=user.id)
        db.session.add(group)
        db.session.commit()

    def login(self):
        rv = self.client.post(
            '/account/login',
            content_type='application/json',
            data=json.dumps({'account': 'lepture', 'password': 'demo'})
        )
        data = json.loads(rv.data)
        auth = data['data']['auth']
        return {'X-YUAN-AUTH': auth}


class TestNoAccountCase(BaseSuite):
    """We didn't have any user"""
    def test_get(self):
        rv = self.client.get('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Account not found" in rv.data

    def test_post(self):
        rv = self.client.post('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Account not found" in rv.data

    def test_put(self):
        rv = self.client.put('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Account not found" in rv.data

    def test_delete(self):
        rv = self.client.delete('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404


class TestNoProjectCase(AuthSuite):
    def test_get(self):
        rv = self.client.get('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "not found" in rv.data

    def test_put(self):
        rv = self.client.put('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "not found" in rv.data

    def test_delete(self):
        rv = self.client.delete('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "not found" in rv.data

    def test_post(self):
        rv = self.client.post('/package/lepture/arale')
        assert "Authorization required" in rv.data

        headers = self.login()
        rv = self.client.post(
            '/package/lepture/arale', headers=headers,
            content_type='application/json',
            data=json.dumps(dict())
        )
        print rv.data


class TestUploadCase(AuthSuite):
    def test_upload(self):
        # 1. create project
        headers = self.login()
        rv = self.client.post(
            '/package/lepture/arale/1.0.0', headers=headers,
            content_type='application/json',
            data=json.dumps(dict())
        )
        assert rv.status_code in (200, 201)
        print rv.data

        headers['CONTENT-ENCODING'] = 'x-gzip'
        rv = self.client.put(
            '/package/lepture/arale/1.0.0', headers=headers,
            content_type='application/x-tar',
            data='a'
        )
        print rv.data
