# coding: utf-8

import gevent.monkey
gevent.monkey.patch_all()
from yuan.app import create_app

__all__ = ['app']

app = create_app()
