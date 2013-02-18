# coding: utf-8

import os
import gevent.monkey
gevent.monkey.patch_all()
from yuan.app import create_app

__all__ = ['app']

app = create_app(os.path.abspath('./etc/config.py'))
