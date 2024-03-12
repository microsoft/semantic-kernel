Introduction
============

httplib2 is a comprehensive HTTP client library, httplib2.py supports many
features left out of other HTTP libraries.

### HTTP and HTTPS

HTTPS support is only available if the socket module was
compiled with SSL support.
    
### Keep-Alive

Supports HTTP 1.1 Keep-Alive, keeping the socket open and
performing multiple requests over the same connection if
possible.
    
### Authentication

The following three types of HTTP Authentication are
supported. These can be used over both HTTP and HTTPS.

* Digest
* Basic
* WSSE

### Caching

The module can optionally operate with a private cache that
understands the Cache-Control: header and uses both the ETag
and Last-Modified cache validators.
    
### All Methods

The module can handle any HTTP request method, not just GET
and POST.
    
### Redirects

Automatically follows 3XX redirects on GETs.
    
### Compression

Handles both 'deflate' and 'gzip' types of compression.
    
### Lost update support

Automatically adds back ETags into PUT requests to resources
we have already cached. This implements Section 3.2 of
Detecting the Lost Update Problem Using Unreserved Checkout.
    
### Unit Tested

A large and growing set of unit tests.


Installation
============


    $ pip install httplib2


Usage
=====

A simple retrieval:

```python
import httplib2
h = httplib2.Http(".cache")
(resp_headers, content) = h.request("http://example.org/", "GET")
```

The 'content' is the content retrieved from the URL. The content
is already decompressed or unzipped if necessary.

To PUT some content to a server that uses SSL and Basic authentication:

```python
import httplib2
h = httplib2.Http(".cache")
h.add_credentials('name', 'password')
(resp, content) = h.request("https://example.org/chapter/2",
                            "PUT", body="This is text",
                            headers={'content-type':'text/plain'} )
```

Use the Cache-Control: header to control how the caching operates.

```python
import httplib2
h = httplib2.Http(".cache")
(resp, content) = h.request("http://bitworking.org/", "GET")
...
(resp, content) = h.request("http://bitworking.org/", "GET",
                            headers={'cache-control':'no-cache'})
```

The first request will be cached and since this is a request
to bitworking.org it will be set to be cached for two hours,
because that is how I have my server configured. Any subsequent
GET to that URI will return the value from the on-disk cache
and no request will be made to the server. You can use the
Cache-Control: header to change the caches behavior and in
this example the second request adds the Cache-Control:
header with a value of 'no-cache' which tells the library
that the cached copy must not be used when handling this request.

More example usage can be found at:

 * https://github.com/httplib2/httplib2/wiki/Examples
 * https://github.com/httplib2/httplib2/wiki/Examples-Python3
