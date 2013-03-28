from fabric.api import env, cd, local, run

env.hosts = ['spmjs.org']


def commit():
    local('git add -p && git commit')


def push():
    local('git push')


def pull():
    # run remote commands
    with cd('~/apps/yuan'):
        run('git pull origin master')


def restart():
    run('supervisorctl restart yuan')


def deploy():
    commit()
    push()
    pull()
    restart()
