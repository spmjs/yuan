Yuan
=====

yuan is a distributed packaging system for spmjs.org.


Installation
-------------

Make sure you have Python 2.7.x installed.

Clone this repo::

    $ git clone git://github.com/lepture/yuan.git yuan

Install every requirements we need::

    $ pip install -r conf/reqs-pro.txt

If you don't have pip, install pip first::

    $ easy_install pip


Configuration
-------------

Make a directory called `etc` in this repo, copy a basic config file and edit it::

    $ mkdir etc
    $ cp conf/base_config.py etc/config.py
    $ vim etc/config.py





Find Account Password
------------------------------

::

    $ python manager.py shell

.. sourcecode:: python

    >>> from yuan.models import Account
    >>> Account.query.all()
    >>> jq = Account.query.filter_by(name="jquery").first()
    >>> jq.password = jq.create_password("alipay")
    >>> jq.save()
