# Yuan

-----------

yuan is a distributed packaging system for everything.

## Client

You should write your own client, and your client must follow our server's API.


## Server

The sever provides an authentication system and three main API for clients,
which are:

- search
- fetch
- upload


### User System

The authentication system should be simple, just basic auth for the client.
But it can support some social authentication such as GitHub or BitBucket.

Package will be uploaded to one's own (or group) storage, just like GitHub.
In this case two packages of two people can have the same name.

### Search

Client request:

```
GET /request/search?package=yuan
```

Server response:

```json
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
```


### Fetch

Client request:

```
GET /request/fetch?package=yuan
```

Server response:

```json
{
    "status": "fail",
    "message": "found more than one package",
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
```

**ATTTENTION** if the server just find one package, it will be success.

And yuan can be namespace-less with just a few configuration.


Client request:

```
GET /request/fetch?package=lepture/yuan

or with a version, like lepture/yuan==1.0.0 please encode it.
GET /request/fetch?package=lepture/yuan%3D%3D1.0.0
```

Server count the hit and then response:

```json
{
    "status": "success",
    "version": "1.0.0",
    "homepage": "http://lab.lepture.com/yuan/",
    "package": "http://download.yuan.org/lepture/yuan/yuan-1.0.0.tar.gz?md5=md5hash",
    "dependencies": ["lepture/chi", "lepture/doit>=2.0"]
}
```

Client should do:

1. if server responses with a homepage address, client should hit the homepage.
2. client should download the dependencies recursively until there is no dependency.
3. client should not rely only on the dependencies given by the server.
4. client should check the md5 value of the package, if it doesn't match, client should show a warnning.


### Upload

Client request:

```
POST /request/upload

Header:
    Authentication
    Content-Type
    Content-Length

Body:
    user/group
    name
    version
    homepage
    dependencies
    description
    readme
    classifier
    md5
    file/url
```

Server will do:

1. authentication and permission check
2. check md5
3. save information in database
4. save the file (optional)


#### version

All these versions are valid:

```
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
```

alpha, beta, and release candidate versions will be marked as unstable.

When client fetch a unspecified version package, the server will show
the very latest stable version.


#### readme

We only support markdown for readme.

#### classifier

We only support license and language classifier.

```
License :: Aladdin Free Public License (AFPL)
License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication
License :: DFSG approved
License :: Eiffel Forum License (EFL)
License :: Free For Educational Use
License :: Free For Home Use
License :: Free for non-commercial use
License :: Freely Distributable
License :: Free To Use But Restricted
License :: Freeware
License :: Netscape Public License (NPL)
License :: Nokia Open Source License (NOKOS)
License :: OSI Approved
License :: OSI Approved :: Academic Free License (AFL)
License :: OSI Approved :: Apache Software License
License :: OSI Approved :: Apple Public Source License
License :: OSI Approved :: Artistic License
License :: OSI Approved :: Attribution Assurance License
License :: OSI Approved :: BSD License
License :: OSI Approved :: Common Public License
License :: OSI Approved :: Eiffel Forum License
License :: OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)
License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)
License :: OSI Approved :: GNU Affero General Public License v3
License :: OSI Approved :: GNU Free Documentation License (FDL)
License :: OSI Approved :: GNU General Public License (GPL)
License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)
License :: OSI Approved :: IBM Public License
License :: OSI Approved :: Intel Open Source License
License :: OSI Approved :: ISC License (ISCL)
License :: OSI Approved :: Jabber Open Source License
License :: OSI Approved :: MIT License
License :: OSI Approved :: MITRE Collaborative Virtual Workspace License (CVW)
License :: OSI Approved :: Motosoto License
License :: OSI Approved :: Mozilla Public License 1.0 (MPL)
License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)
License :: OSI Approved :: Nethack General Public License
License :: OSI Approved :: Nokia Open Source License
License :: OSI Approved :: Open Group Test Suite License
License :: OSI Approved :: Python License (CNRI Python License)
License :: OSI Approved :: Python Software Foundation License
License :: OSI Approved :: Qt Public License (QPL)
License :: OSI Approved :: Ricoh Source Code Public License
License :: OSI Approved :: Sleepycat License
License :: OSI Approved :: Sun Industry Standards Source License (SISSL)
License :: OSI Approved :: Sun Public License
License :: OSI Approved :: University of Illinois/NCSA Open Source License
License :: OSI Approved :: Vovida Software License 1.0
License :: OSI Approved :: W3C License
License :: OSI Approved :: X.Net License
License :: OSI Approved :: zlib/libpng License
License :: OSI Approved :: Zope Public License
License :: Other/Proprietary License
License :: Public Domain
License :: Repoze Public License
Language :: Ada
Language :: APL
Language :: ASP
Language :: Assembly
Language :: Awk
Language :: Basic
Language :: C
Language :: C#
Language :: C++
Language :: Cold Fusion
Language :: Cython
Language :: Delphi/Kylix
Language :: Dylan
Language :: Eiffel
Language :: Emacs-Lisp
Language :: Erlang
Language :: Euler
Language :: Euphoria
Language :: Forth
Language :: Fortran
Language :: Haskell
Language :: Java
Language :: JavaScript
Language :: Lisp
Language :: Logo
Language :: ML
Language :: Modula
Language :: Objective C
Language :: Object Pascal
Language :: OCaml
Language :: Other
Language :: Other Scripting Engines
Language :: Pascal
Language :: Perl
Language :: PHP
Language :: Pike
Language :: Pliant
Language :: PL/SQL
Language :: PROGRESS
Language :: Prolog
Language :: Python
Language :: REBOL
Language :: Rexx
Language :: Ruby
Language :: Scheme
Language :: Simula
Language :: Smalltalk
Language :: SQL
Language :: Tcl
Language :: Unix Shell
Language :: Visual Basic
Language :: XBasic
Language :: YACC
Language :: Zope
```


## Mirror

## Document Site
