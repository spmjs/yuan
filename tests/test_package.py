# coding: utf-8

from flask import json
from yuan.models import db, Account

from .suite import BaseSuite


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


class TestNoProjectCase(BaseSuite):
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

    def test_not_post(self):
        rv = self.client.get('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "not found" in rv.data

        rv = self.client.put('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "not found" in rv.data

        rv = self.client.delete('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "not found" in rv.data

        rv = self.client.post('/package/lepture/arale')
        assert "Authorization required" in rv.data

        headers = self.login()
        rv = self.client.post(
            '/package/lepture/arale', headers=headers,
            content_type='application/json',
            data=json.dumps(dict())
        )
        print rv.data
