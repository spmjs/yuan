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


Information
------------


Register
--------


Publish
--------


Documentation
--------------
