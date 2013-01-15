# coding: utf-8


from yuan.models import Account, Team

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
        assert Team.query.count() == 1

        team = Team(name='Developer', owner_id=org.id, _permission=3)
        team.members.append(user)
        team.save()
        assert Team.query.count() == 2

        robot = Account(name='robot')
        robot.save()
        team.members.append(robot)
        assert len(org.permission_read.needs) == 3
        assert len(org.permission_own.needs) == 2
