# coding: utf-8

from flask import json
from .suite import BaseSuite


class TestNoFamilyCase(BaseSuite):
    """We didn't have any user"""
    def test_get(self):
        rv = self.client.get('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 404
        assert "Project not found" in rv.data

    def test_post(self):
        rv = self.client.post('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 401

    def test_put(self):
        rv = self.client.put('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 404

    def test_delete(self):
        rv = self.client.delete('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 404


class TestNoProjectCase(BaseSuite):
    def prehook(self):
        self.create_account()

    def test_get(self):
        rv = self.client.get('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 404
        assert "not found" in rv.data

    def test_put(self):
        rv = self.client.put('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 404
        assert "not found" in rv.data

    def test_delete(self):
        rv = self.client.delete('/repository/lepture/arale/1.0.1/')
        assert rv.status_code == 404
        assert "not found" in rv.data

    def test_post(self):
        rv = self.client.post('/repository/lepture/arale/1.0.1/')
        assert "Authorization required" in rv.data

        headers = self.login_account()
        rv = self.client.post(
            '/repository/lepture/arale/1.0.1/', headers=headers,
            content_type='application/json',
            data=json.dumps(dict())
        )
        print rv.data


class TestUploadCase(BaseSuite):
    def prehook(self):
        self.create_account()

    def test_upload(self):
        # 1. create project
        headers = self.login_account()
        headers['X-Yuan-Force'] = 'true'
        rv = self.client.post(
            '/repository/lepture/arale/1.0.0/', headers=headers,
            content_type='application/json',
            data=json.dumps(dict())
        )
        assert rv.status_code in (200, 201)
        print rv.data

        headers['CONTENT-ENCODING'] = 'x-gzip'
        rv = self.client.put(
            '/repository/lepture/arale/1.0.0/', headers=headers,
            content_type='application/x-tar',
            data='a'
        )
        print rv.data
