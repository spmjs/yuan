# coding: utf-8


from yuan.models import Account, Member

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

        member = Member(org_id=org.id, user_id=user.id)
        member.save()

        print Account.query.all()
        print Member.query.all()
        print user.organizations
        assert len(user.organizations) == 1
