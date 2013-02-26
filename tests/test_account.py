# coding: utf-8


from flask import json
from yuan.models import Account

from .suite import BaseSuite


class TestAccount(BaseSuite):
    def prehook(self):
        user = Account(
            name='lepture', email='lepture@me.com', password='1'
        )
        user.save()

    def test_login(self):
        rv = self.client.post(
            '/account/login',
            content_type='application/json',
            data=json.dumps({'account': 'lepture', 'password': '1'})
        )
        data = json.loads(rv.data)
        assert 'data' in data

        auth = data['data']
        assert auth
        self.client.get('/', headers={'Authorization': 'Yuan ' + auth})

    def test_register(self):
        rv = self.client.post(
            '/account/register',
            content_type='application/json',
            data=json.dumps(
                {'name': 'lepture', 'password': '1'}
            )
        )
        assert 'message' in rv.data

        rv = self.client.post(
            '/account/register',
            content_type='application/json',
            data=json.dumps(
                {'name': 'lepture2', 'email': 'a@me.com', 'password': '1'}
            )
        )
        assert 'data' in rv.data
