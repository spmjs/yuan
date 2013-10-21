# coding: utf-8

import os
import imp
import gevent.monkey
gevent.monkey.patch_all()
from yuan.app import create_app
import jieba

jieba.initialize()
application = create_app()

ROOTDIR = os.path.abspath(os.path.dirname(__file__))
HOOK = os.path.join(ROOTDIR, 'etc/hook.py')
if os.path.exists(HOOK):
    hook = imp.load_source('hook', HOOK)
    hook.main()
