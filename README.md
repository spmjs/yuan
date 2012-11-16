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
GET /request/search?name=yuan
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
GET /request/fetch?name=yuan
```

Server response:

```json
{
    "status": "fail",
    "message": "found more than one package"
}
```


Client request:

```
GET /request/fetch?name=lepture/yuan
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
3. client should check the md5 value of the package, if it doesn't match, client should show a warnning.


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
    dependencies
    description
    md5
    file
```

Server will do:

1. authentication and permission check
2. check md5
3. save information in database then save the file
