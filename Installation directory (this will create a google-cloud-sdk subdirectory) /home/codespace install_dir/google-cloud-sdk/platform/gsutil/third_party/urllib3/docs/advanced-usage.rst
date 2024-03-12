Advanced Usage
==============

.. currentmodule:: urllib3


Customizing Pool Behavior
-------------------------

The :class:`~poolmanager.PoolManager` class automatically handles creating
:class:`~connectionpool.ConnectionPool` instances for each host as needed. By
default, it will keep a maximum of 10 :class:`~connectionpool.ConnectionPool`
instances. If you're making requests to many different hosts it might improve
performance to increase this number::

    >>> import urllib3
    >>> http = urllib3.PoolManager(num_pools=50)

However, keep in mind that this does increase memory and socket consumption.

Similarly, the :class:`~connectionpool.ConnectionPool` class keeps a pool
of individual :class:`~connection.HTTPConnection` instances. These connections
are used during an individual request and returned to the pool when the request
is complete. By default only one connection will be saved for re-use. If you
are making many requests to the same host simultaneously it might improve
performance to increase this number::

    >>> import urllib3
    >>> http = urllib3.PoolManager(maxsize=10)
    # Alternatively
    >>> http = urllib3.HTTPConnectionPool('google.com', maxsize=10)

The behavior of the pooling for :class:`~connectionpool.ConnectionPool` is
different from :class:`~poolmanager.PoolManager`. By default, if a new
request is made and there is no free connection in the pool then a new
connection will be created. However, this connection will not be saved if more
than ``maxsize`` connections exist. This means that ``maxsize`` does not
determine the maximum number of connections that can be open to a particular
host, just the maximum number of connections to keep in the pool. However, if you specify ``block=True`` then there can be at most ``maxsize`` connections
open to a particular host::

    >>> http = urllib3.PoolManager(maxsize=10, block=True)
    # Alternatively
    >>> http = urllib3.HTTPConnectionPool('google.com', maxsize=10, block=True)

Any new requests will block until a connection is available from the pool.
This is a great way to prevent flooding a host with too many connections in
multi-threaded applications.

.. _stream:
.. _streaming_and_io:

Streaming and I/O
-----------------

When dealing with large responses it's often better to stream the response
content::

    >>> import urllib3
    >>> http = urllib3.PoolManager()
    >>> r = http.request(
    ...     'GET',
    ...     'http://httpbin.org/bytes/1024',
    ...     preload_content=False)
    >>> for chunk in r.stream(32):
    ...     print(chunk)
    b'...'
    b'...'
    ...
    >>> r.release_conn()

Setting ``preload_content`` to ``False`` means that urllib3 will stream the
response content. :meth:`~response.HTTPResponse.stream` lets you iterate over
chunks of the response content.

.. note:: When using ``preload_content=False``, you should call
    :meth:`~response.HTTPResponse.release_conn` to release the http connection
    back to the connection pool so that it can be re-used.

However, you can also treat the :class:`~response.HTTPResponse` instance as
a file-like object. This allows you to do buffering::

    >>> r = http.request(
    ...     'GET',
    ...     'http://httpbin.org/bytes/1024',
    ...     preload_content=False)
    >>> r.read(4)
    b'\x88\x1f\x8b\xe5'

Calls to :meth:`~response.HTTPResponse.read()` will block until more response
data is available.

    >>> import io
    >>> reader = io.BufferedReader(r, 8)
    >>> reader.read(4)
    >>> r.release_conn()

You can use this file-like object to do things like decode the content using
:mod:`codecs`::

    >>> import codecs
    >>> reader = codecs.getreader('utf-8')
    >>> r = http.request(
    ...     'GET',
    ...     'http://httpbin.org/ip',
    ...     preload_content=False)
    >>> json.load(reader(r))
    {'origin': '127.0.0.1'}
    >>> r.release_conn()

.. _proxies:

Proxies
-------

You can use :class:`~poolmanager.ProxyManager` to tunnel requests through an
HTTP proxy::

    >>> import urllib3
    >>> proxy = urllib3.ProxyManager('http://localhost:3128/')
    >>> proxy.request('GET', 'http://google.com/')

The usage of :class:`~poolmanager.ProxyManager` is the same as
:class:`~poolmanager.PoolManager`.

You can connect to a proxy using HTTP, HTTPS or SOCKS. urllib3's behavior will
be different depending on the type of proxy you selected and the destination
you're contacting.

HTTP and HTTPS Proxies
~~~~~~~~~~~~~~~~~~~~~~

Both HTTP/HTTPS proxies support HTTP and HTTPS destinations. The only
difference between them is if you need to establish a TLS connection to the
proxy first. You can specify which proxy you need to contact by specifying the
proper proxy scheme. (i.e ``http://`` or ``https://``)

urllib3's behavior will be different depending on your proxy and destination:

* HTTP proxy + HTTP destination
   Your request will be forwarded with the `absolute URI
   <https://tools.ietf.org/html/rfc7230#section-5.3.2>`_.

* HTTP proxy + HTTPS destination
    A TCP tunnel will be established with a `HTTP
    CONNECT <https://tools.ietf.org/html/rfc7231#section-4.3.6>`_. Afterward a
    TLS connection will be established with the destination and your request
    will be sent.

* HTTPS proxy + HTTP destination
    A TLS connection will be established to the proxy and later your request
    will be forwarded with the `absolute URI
    <https://tools.ietf.org/html/rfc7230#section-5.3.2>`_.

* HTTPS proxy + HTTPS destination
    A TLS-in-TLS tunnel will be established.  An initial TLS connection will be
    established to the proxy, then an `HTTP CONNECT
    <https://tools.ietf.org/html/rfc7231#section-4.3.6>`_ will be sent to
    establish a TCP connection to the destination and finally a second TLS
    connection will be established to the destination. You can customize the
    :class:`ssl.SSLContext` used for the proxy TLS connection through the
    ``proxy_ssl_context`` argument of the :class:`~poolmanager.ProxyManager`
    class.

For HTTPS proxies we also support forwarding your requests to HTTPS destinations with
an `absolute URI <https://tools.ietf.org/html/rfc7230#section-5.3.2>`_ if the
``use_forwarding_for_https`` argument is set to ``True``. We strongly recommend you
**only use this option with trusted or corporate proxies** as the proxy will have
full visibility of your requests.

.. _https_proxy_error_http_proxy:

Your proxy appears to only use HTTP and not HTTPS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're receiving the :class:`~urllib3.exceptions.ProxyError` and it mentions
your proxy only speaks HTTP and not HTTPS here's what to do to solve your issue:

If you're using ``urllib3`` directly, make sure the URL you're passing into :class:`urllib3.ProxyManager`
starts with ``http://`` instead of ``https://``:

.. code-block:: python

     # Do this:
     http = urllib3.ProxyManager("http://...")

     # Not this:
     http = urllib3.ProxyManager("https://...")

If instead you're using ``urllib3`` through another library like Requests
there are multiple ways your proxy could be mis-configured. You need to figure out
where the configuration isn't correct and make the fix there. Some common places
to look are environment variables like ``HTTP_PROXY``, ``HTTPS_PROXY``, and ``ALL_PROXY``.

Ensure that the values for all of these environment variables starts with ``http://``
and not ``https://``:

.. code-block:: bash

     # Check your existing environment variables in bash
     $ env | grep "_PROXY"
     HTTP_PROXY=http://127.0.0.1:8888
     HTTPS_PROXY=https://127.0.0.1:8888  # <--- This setting is the problem!

     # Make the fix in your current session and test your script
     $ export HTTPS_PROXY="http://127.0.0.1:8888"
     $ python test-proxy.py  # This should now pass.

     # Persist your change in your shell 'profile' (~/.bashrc, ~/.profile, ~/.bash_profile, etc)
     # You may need to logout and log back in to ensure this works across all programs.
     $ vim ~/.bashrc

If you're on Windows or macOS your proxy may be getting set at a system level.
To check this first ensure that the above environment variables aren't set
then run the following:

.. code-block:: bash

    $ python -c 'import urllib.request; print(urllib.request.getproxies())'

If the output of the above command isn't empty and looks like this:

.. code-block:: python

    {
      "http": "http://127.0.0.1:8888",
      "https": "https://127.0.0.1:8888"  # <--- This setting is the problem!
    }

Search how to configure proxies on your operating system and change the ``https://...`` URL into ``http://``.
After you make the change the return value of ``urllib.request.getproxies()`` should be:

.. code-block:: python

    {  # Everything is good here! :)
      "http": "http://127.0.0.1:8888",
      "https": "http://127.0.0.1:8888"
    }

If you still can't figure out how to configure your proxy after all these steps
please `join our community Discord <https://discord.gg/urllib3>`_ and we'll try to help you with your issue.

SOCKS Proxies
~~~~~~~~~~~~~


For SOCKS, you can use :class:`~contrib.socks.SOCKSProxyManager` to connect to
SOCKS4 or SOCKS5 proxies. In order to use SOCKS proxies you will need to
install `PySocks <https://pypi.org/project/PySocks/>`_ or install urllib3 with
the ``socks`` extra::

     python -m pip install urllib3[socks]

Once PySocks is installed, you can use
:class:`~contrib.socks.SOCKSProxyManager`::

    >>> from urllib3.contrib.socks import SOCKSProxyManager
    >>> proxy = SOCKSProxyManager('socks5h://localhost:8889/')
    >>> proxy.request('GET', 'http://google.com/')

.. note::
      It is recommended to use ``socks5h://`` or ``socks4a://`` schemes in
      your ``proxy_url`` to ensure that DNS resolution is done from the remote
      server instead of client-side when connecting to a domain name.

.. _ssl_custom:
.. _custom_ssl_certificates:

Custom TLS Certificates
-----------------------

Instead of using `certifi <https://certifi.io/>`_ you can provide your
own certificate authority bundle. This is useful for cases where you've
generated your own certificates or when you're using a private certificate
authority. Just provide the full path to the certificate bundle when creating a
:class:`~poolmanager.PoolManager`::

    >>> import urllib3
    >>> http = urllib3.PoolManager(
    ...     cert_reqs='CERT_REQUIRED',
    ...     ca_certs='/path/to/your/certificate_bundle')

When you specify your own certificate bundle only requests that can be
verified with that bundle will succeed. It's recommended to use a separate
:class:`~poolmanager.PoolManager` to make requests to URLs that do not need
the custom certificate.

.. _sni_custom:

Custom SNI Hostname
-------------------

If you want to create a connection to a host over HTTPS which uses SNI, there
are two places where the hostname is expected. It must be included in the Host
header sent, so that the server will know which host is being requested. The
hostname should also match the certificate served by the server, which is
checked by urllib3.

Normally, urllib3 takes care of setting and checking these values for you when
you connect to a host by name. However, it's sometimes useful to set a
connection's expected Host header and certificate hostname (subject),
especially when you are connecting without using name resolution. For example,
you could connect to a server by IP using HTTPS like so::

    >>> import urllib3
    >>> pool = urllib3.HTTPSConnectionPool(
    ...     "10.0.0.10",
    ...     assert_hostname="example.org",
    ...     server_hostname="example.org"
    ... )
    >>> pool.urlopen(
    ...     "GET",
    ...     "/",
    ...     headers={"Host": "example.org"},
    ...     assert_same_host=False
    ... )


Note that when you use a connection in this way, you must specify
``assert_same_host=False``.

This is useful when DNS resolution for ``example.org`` does not match the
address that you would like to use. The IP may be for a private interface, or
you may want to use a specific host under round-robin DNS.


.. _ssl_client:

Client Certificates
-------------------

You can also specify a client certificate. This is useful when both the server
and the client need to verify each other's identity. Typically these
certificates are issued from the same authority. To use a client certificate,
provide the full path when creating a :class:`~poolmanager.PoolManager`::

    >>> http = urllib3.PoolManager(
    ...     cert_file='/path/to/your/client_cert.pem',
    ...     cert_reqs='CERT_REQUIRED',
    ...     ca_certs='/path/to/your/certificate_bundle')

If you have an encrypted client certificate private key you can use
the ``key_password`` parameter to specify a password to decrypt the key. ::

    >>> http = urllib3.PoolManager(
    ...     cert_file='/path/to/your/client_cert.pem',
    ...     cert_reqs='CERT_REQUIRED',
    ...     key_file='/path/to/your/client.key',
    ...     key_password='keyfile_password')

If your key isn't encrypted the ``key_password`` parameter isn't required.

.. _ssl_mac:
.. _certificate_validation_and_mac_os_x:

Certificate Validation and macOS
--------------------------------

Apple-provided Python and OpenSSL libraries contain a patches that make them
automatically check the system keychain's certificates. This can be
surprising if you specify custom certificates and see requests unexpectedly
succeed. For example, if you are specifying your own certificate for validation
and the server presents a different certificate you would expect the connection
to fail. However, if that server presents a certificate that is in the system
keychain then the connection will succeed.

`This article <https://hynek.me/articles/apple-openssl-verification-surprises/>`_
has more in-depth analysis and explanation.

.. _ssl_warnings:

TLS Warnings
------------

urllib3 will issue several different warnings based on the level of certificate
verification support. These warnings indicate particular situations and can
be resolved in different ways.

* :class:`~exceptions.InsecureRequestWarning`
    This happens when a request is made to an HTTPS URL without certificate
    verification enabled. Follow the :ref:`certificate verification <ssl>`
    guide to resolve this warning.
* :class:`~exceptions.InsecurePlatformWarning`
    This happens on Python 2 platforms that have an outdated :mod:`ssl` module.
    These older :mod:`ssl` modules can cause some insecure requests to succeed
    where they should fail and secure requests to fail where they should
    succeed. Follow the :ref:`pyOpenSSL <ssl_py2>` guide to resolve this
    warning.

.. _sni_warning:

* :class:`~exceptions.SNIMissingWarning`
    This happens on Python 2 versions older than 2.7.9. These older versions
    lack `SNI <https://en.wikipedia.org/wiki/Server_Name_Indication>`_ support.
    This can cause servers to present a certificate that the client thinks is
    invalid. Follow the :ref:`pyOpenSSL <ssl_py2>` guide to resolve this
    warning.

.. _disable_ssl_warnings:

Making unverified HTTPS requests is **strongly** discouraged, however, if you
understand the risks and wish to disable these warnings, you can use :func:`~urllib3.disable_warnings`:

.. code-block:: pycon

    >>> import urllib3
    >>> urllib3.disable_warnings()

Alternatively you can capture the warnings with the standard :mod:`logging` module:

.. code-block:: pycon

    >>> logging.captureWarnings(True)

Finally, you can suppress the warnings at the interpreter level by setting the
``PYTHONWARNINGS`` environment variable or by using the
`-W flag <https://docs.python.org/3/using/cmdline.html#cmdoption-w>`_.

Google App Engine
-----------------

urllib3 supports `Google App Engine <https://cloud.google.com/appengine>`_ with
some caveats.

If you're using the `Flexible environment
<https://cloud.google.com/appengine/docs/flexible/>`_, you do not have to do
any configuration- urllib3 will just work. However, if you're using the
`Standard environment <https://cloud.google.com/appengine/docs/python/>`_ then
you either have to use :mod:`urllib3.contrib.appengine`'s
:class:`~urllib3.contrib.appengine.AppEngineManager` or use the `Sockets API
<https://cloud.google.com/appengine/docs/python/sockets/>`_

To use :class:`~urllib3.contrib.appengine.AppEngineManager`:

.. code-block:: pycon

    >>> from urllib3.contrib.appengine import AppEngineManager
    >>> http = AppEngineManager()
    >>> http.request('GET', 'https://google.com/')

To use the Sockets API, add the following to your app.yaml and use
:class:`~urllib3.poolmanager.PoolManager` as usual:

.. code-block:: yaml

    env_variables:
        GAE_USE_SOCKETS_HTTPLIB : 'true'

For more details on the limitations and gotchas, see
:mod:`urllib3.contrib.appengine`.

Brotli Encoding
---------------

Brotli is a compression algorithm created by Google with better compression
than gzip and deflate and is supported by urllib3 if the
`Brotli <https://pypi.org/Brotli>`_ package or
`brotlicffi <https://github.com/python-hyper/brotlicffi>`_ package is installed.
You may also request the package be installed via the ``urllib3[brotli]`` extra:

.. code-block:: bash

    $ python -m pip install urllib3[brotli]

Here's an example using brotli encoding via the ``Accept-Encoding`` header:

.. code-block:: pycon

    >>> from urllib3 import PoolManager
    >>> http = PoolManager()
    >>> http.request('GET', 'https://www.google.com/', headers={'Accept-Encoding': 'br'})

Decrypting Captured TLS Sessions with Wireshark
-----------------------------------------------
Python 3.8 and higher support logging of TLS pre-master secrets.
With these secrets tools like `Wireshark <https://wireshark.org>`_ can decrypt captured
network traffic.

To enable this simply define environment variable `SSLKEYLOGFILE`:

.. code-block:: bash

    export SSLKEYLOGFILE=/path/to/keylogfile.txt

Then configure the key logfile in `Wireshark <https://wireshark.org>`_, see
`Wireshark TLS Decryption <https://wiki.wireshark.org/TLS#TLS_Decryption>`_ for instructions.
