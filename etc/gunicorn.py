#!/usr/bin/env python

import multiprocessing

bind = 'unix:/tmp/yuan.sock'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'egg:gunicorn#gevent'

# maybe you should change this
user = 'www'

# maybe you like error
loglevel = 'warning'

secure_scheme_headers = {
    'X-SCHEME': 'https',
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on',
}
x_forwarded_for_header = 'X-FORWARDED-FOR'
