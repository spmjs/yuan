# coding: utf-8


from yuan.models import Account, Member, Project

from .suite import BaseSuite


class TestModel(BaseSuite):
    def test_account(self):
        user = Account(name='spm')
        user.save()

    def test_membership(self):
        user = Account(name='lepture')
        user.save()

        org = Account(
            name='yuan',
            account_type='org',
            org_owner_id=user.id,
        )
        org.save()

        member = Member(org_id=org.id, user_id=user.id)
        member.save()

        assert len(user.organizations) == 1
