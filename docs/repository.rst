.. _repository:

Repository
===========

Repository is the place to store packages, you can download, upload and modify a package in the repository.


Authorization
--------------

Authorization is required to upload and modify a package, so it is with downloading a private package.

Get authorization code::

    POST /account/login
    {
        "account": "username or email",
        "password": "password"
    }

Example with curl::

    curl http://127.0.0.1:5000/account/login
        -H "Content-Type:application/json"
        -d '{
            "account": "username",
            "password": "password"
        }'

The response should be::

    {
        "status": "success",
        "data": "GEZTKOBZGIYDIMZTPQYXYODDGVSWGNRVGZSGKZRZG42TCZDFMQYDEMTDGBSTOMRUGRQTIZTEMEYTQMRZGJRGC==="
    }

When request resource, add authorization header::

    headers['Authorization'] = 'Yuan GEZTKOBZGIYDIMZTPQYXYODDGVSWGNRVGZSGKZRZG42TCZDFMQYDEMTDGBSTOMRUGRQTIZTEMEYTQMRZGJRGC==='


Status Code
-----------

Client should first detect status code of the response::


    200: 'Success.'
    201: 'Created.'
    400: 'Bad request.'
    401: 'Authorization required.'
    403: 'Permission denied.'
    404: 'Not found.'
    406: 'Not acceptable.'
    415: 'Unsupported media type.'
    426: 'Upgrade required.'
    444: 'Force option required.'

Reponse will be a ``content-type`` of ``application/json``, every response should contain a ``status``::

    {
        status: 'warn',
        message: 'this is a warnning message'
    }

If the response contains ``message``, client should log the message with a logging level that ``status`` said.

Account
-------

List projects in the account. If client requests with authorization, the response will contain private projects::

    GET /repository/arale/

    {
      "status": "success",
      "data": [
        "calendar",
        "base"
      ]
    }


Project
--------

Get information of a project, it this is a private project, authorization is required::

    GET /repository/arale/base/

    {
      "status": "success",
      "data": {
        "updated": "2013-01-23 10:16:44",
        "name": "base",
        "repository": "https://github.com/aralejs/base.git",
        "created": "2013-01-23 10:16:44",
        "download_base": "http://public.example.com",
        "account": "arale",
        "packages": [
          {
            "dependencies": [
              "arale/class",
              "arale/events"
            ],
            "version": "1.0.2",
            "md5": null,
            "download_url": "arale/base/base-1.0.2.tar.gz",
            "created": "2013-01-23 11:18:22"
          },
          {
            "dependencies": [
              "arale/class",
              "arale/events"
            ],
            "version": "1.0.1",
            "md5": null,
            "download_url": "arale/base/base-1.0.1.tar.gz",
            "created": "2013-01-23 10:16:44"
          },
          {
            "dependencies": [
              "arale/class",
              "arale/events"
            ],
            "version": "1.0.0",
            "md5": null,
            "download_url": "arale/base/base-1.0.0.tar.gz",
            "created": "2013-01-23 11:18:06"
          }
        ],
        "homepage": "http://aralejs.org/base",
        "description": "Base \u662f\u4e00\u4e2a\u57fa\u7840\u7c7b\uff0c\u63d0\u4f9b Class\u3001Events\u3001Attribute \u548c Aspect \u652f\u6301\u3002"
      }
    }

Create a project with **POST** method, authorization is required, content-type should be ``application/json``::

    POST /repository/arale/base/
    Content-Type: application/json
    Authorization: Yuan GEZTKOBZGIYDIMZTPQY...

    Body:
        {
            homepage:
            repository:
            description:
            keywords:
            private:
        }


Package
-------

Get information of a package, authorization is required to get information of a private project::

    GET /repository/arale/base/1.0.0

    {
      "status": "success",
      "data": {
        "account": "arale",
        "name": "base",
        "version": "1.0.0",
        "private": false,
        "tag": "stable",
        "repository": "https://github.com/aralejs/base.git",
        "updated": "2013-01-23 10:16:44",
        "created": "2013-01-23 10:16:44",
        "download_base": "http://public.example.com",
        "download_url": "arale/base/base-1.0.0.tar.gz",
        "dependencies": [
          "arale/class",
          "arale/events"
        ],
        "md5": null,
        "homepage": "http://aralejs.org/base",
        "description": "Base \u662f\u4e00\u4e2a\u57fa\u7840\u7c7b\uff0c\u63d0\u4f9b Class\u3001Events\u3001Attribute \u548c Aspect \u652f\u6301\u3002"
      }
    }


.. _create_package:

Create or update information of a package with **POST** method, content-type should be
``application/json``, if the project is not existed, it will create the project automaticly::

    POST /repository/arale/base/1.0.0
    Authorization: Yuan GEZ...
    Content-Type: application/json

    Body:
        {
            homepage:
            readme:
            md5value:
            ....
        }


Delete a package with **DELETE** method::

    DELETE /repository/arale/base/1.0.0
    Authorization: Yuan GEZ....


Publish a package with **PUT** method, content type should be ``application/x-tar-gz``::

    PUT /repository/arale/base/1.0.0
    Content-Type: application/x-tar-gz
    Content-Length: 2014
    Authorization: Yuan GEZTKOBZGIYDIMZTPQY....

Authorization is required, overwrite the package with additional header **X-Yuan-Force**::

    PUT /repository/arale/base/1.0.0
    Content-Type: application/x-tar-gz
    Content-Length: 2014
    Authorization: Yuan GEZTKOBZGIYDIMZTPQY....
    X-Yuan-Force: true


Search
--------

Our search engine is elasticsearch_

::

    GET /repository/search?s=jquery

    GET /repository/search?name=jquery

    GET /repository/search?keyword=jquery


.. _elasticsearch: http://elasticsearch.org
