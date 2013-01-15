# coding: utf-8


from yuan.models import db, Account

from .suite import BaseSuite


class TestNoAccountCase(BaseSuite):
    """We didn't have any user"""
    def test_get(self):
        rv = self.client.get('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Invalid account" in rv.data

    def test_post(self):
        rv = self.client.post('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Invalid account" in rv.data

    def test_put(self):
        rv = self.client.put('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Invalid account" in rv.data

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

    def test_not_post(self):
        rv = self.client.get('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Package not exists" in rv.data

        rv = self.client.put('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Package not exists" in rv.data

        rv = self.client.delete('/package/lepture/arale/1.0.1')
        assert rv.status_code == 404
        assert "Package not exists" in rv.data

        rv = self.client.post('/package/lepture/arale')
        print rv.data
