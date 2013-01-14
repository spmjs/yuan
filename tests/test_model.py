# coding: utf-8


from yuan.models import Account

from .suite import BaseSuite


class TestAccount(BaseSuite):
    def test_membership(self):
        user = Account(name='lepture')
        user.save()

        org = Account(
            name='yuan',
            account_type='org',
            org_owner_id=user.id,
        )
        org.save()
