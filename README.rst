Yuan
=====

yuan is a distributed packaging system for everything.

Client
-------

You should write your own client, and your client must follow our server's API.


Server
-------

The sever provides an authentication system and APIs for package management.

User System
~~~~~~~~~~~~

The authentication system should be simple, just basic auth for the client.
But it can support some social authentication such as GitHub or BitBucket.

Package will be uploaded to one's own (or group) storage, just like GitHub.
In this case two packages of two people can have the same name.

::

    GET /account/login

    {
        "status": "info",
        "data": {
            "auth": "GEZX......"
        }
    }

Search
~~~~~~~

Client request::

    GET /package/search?package=yuan

Server response::

    {
        "status": "success",
        "count": "2",
        "packages": [
            {
                "name": "yuan",
                "author": "lepture",
                "description": "yuan is a distributed packaging system"
            },
            {
                "name": "yuan",
                "author": "lifesinger",
                "description": "yuan is a seajs module"
            }
        ]
    }


Register Project
~~~~~~~~~~~~~~~~

Client request::

    POST /package/{{username}}/{{name}}

Server response::

    {
    }


1. authentication and permission check
2. check md5
3. save information in database
4. save the file (optional)


Version
~~~~~~~~

All these versions are valid::

    0.4    0.4.0
    0.5a1           alpha
    0.5b3           beta
    0.5
    0.9.6
    1.0
    1.0.4a3         alpha
    1.0.4b1         beta
    1.0.4r1         release candidate
    1.0.4

alpha, beta, and release candidate versions will be marked as unstable.

When client fetch a unspecified version package, the server will show
the very latest stable version.


Readme
~~~~~~~

We only support markdown for readme.


Mirror

Document Site
