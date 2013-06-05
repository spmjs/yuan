from fabric.api import env, cd, local, run

env.hosts = ['spmjs.org']


def push():
    local('git push')


def pull():
    # run remote commands
    with cd('~/apps/yuan'):
        run('git pull origin master')


def restart():
    run('supervisorctl restart yuan')


def index():
    with cd('~/apps/yuan'):
        run('python manager.py index')


def deploy():
    push()
    pull()
    restart()
