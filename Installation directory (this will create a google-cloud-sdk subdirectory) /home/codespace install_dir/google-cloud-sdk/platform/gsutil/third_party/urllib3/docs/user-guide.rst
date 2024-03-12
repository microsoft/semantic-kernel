User Guide
==========

.. currentmodule:: urllib3

Installing
----------

urllib3 can be installed with `pip <https://pip.pypa.io>`_

.. code-block:: bash

  $ python -m pip install urllib3


Making Requests
---------------

First things first, import the urllib3 module:

.. code-block:: pycon

    >>> import urllib3

You'll need a :class:`~poolmanager.PoolManager` instance to make requests.
This object handles all of the details of connection pooling and thread safety
so that you don't have to:

.. code-block:: pycon

    >>> http = urllib3.PoolManager()

To make a request use :meth:`~poolmanager.PoolManager.request`:

.. code-block:: pycon

    >>> r = http.request('GET', 'http://httpbin.org/robots.txt')
    >>> r.data
    b'User-agent: *\nDisallow: /deny\n'

``request()`` returns a :class:`~response.HTTPResponse` object, the
:ref:`response_content` section explains how to handle various responses.

You can use :meth:`~poolmanager.PoolManager.request` to make requests using any
HTTP verb:

.. code-block:: pycon

    >>> r = http.request(
    ...     'POST',
    ...     'http://httpbin.org/post',
    ...     fields={'hello': 'world'}
    ... )

The :ref:`request_data` section covers sending other kinds of requests data,
including JSON, files, and binary data.

.. _response_content:

Response Content
----------------

The :class:`~response.HTTPResponse` object provides
:attr:`~response.HTTPResponse.status`, :attr:`~response.HTTPResponse.data`, and
:attr:`~response.HTTPResponse.headers` attributes:

.. code-block:: pycon

    >>> r = http.request('GET', 'http://httpbin.org/ip')
    >>> r.status
    200
    >>> r.data
    b'{\n  "origin": "104.232.115.37"\n}\n'
    >>> r.headers
    HTTPHeaderDict({'Content-Length': '33', ...})

JSON Content
~~~~~~~~~~~~

JSON content can be loaded by decoding and deserializing the
:attr:`~response.HTTPResponse.data` attribute of the request:

.. code-block:: pycon

    >>> import json
    >>> r = http.request('GET', 'http://httpbin.org/ip')
    >>> json.loads(r.data.decode('utf-8'))
    {'origin': '127.0.0.1'}

Binary Content
~~~~~~~~~~~~~~

The :attr:`~response.HTTPResponse.data` attribute of the response is always set
to a byte string representing the response content:

.. code-block:: pycon

    >>> r = http.request('GET', 'http://httpbin.org/bytes/8')
    >>> r.data
    b'\xaa\xa5H?\x95\xe9\x9b\x11'

.. note:: For larger responses, it's sometimes better to :ref:`stream <stream>`
    the response.

Using io Wrappers with Response Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you want to use :class:`io.TextIOWrapper` or similar objects like a CSV reader
directly with :class:`~response.HTTPResponse` data. Making these two interfaces play nice
together requires using the :attr:`~response.HTTPResponse.auto_close` attribute by setting it
to ``False``. By default HTTP responses are closed after reading all bytes, this disables that behavior:

.. code-block:: pycon

    >>> import io
    >>> r = http.request('GET', 'https://example.com', preload_content=False)
    >>> r.auto_close = False
    >>> for line in io.TextIOWrapper(r):
    >>>     print(line)

.. _request_data:

Request Data
------------

Headers
~~~~~~~

You can specify headers as a dictionary in the ``headers`` argument in :meth:`~poolmanager.PoolManager.request`:

.. code-block:: pycon

    >>> r = http.request(
    ...     'GET',
    ...     'http://httpbin.org/headers',
    ...     headers={
    ...         'X-Something': 'value'
    ...     }
    ... )
    >>> json.loads(r.data.decode('utf-8'))['headers']
    {'X-Something': 'value', ...}

Query Parameters
~~~~~~~~~~~~~~~~

For ``GET``, ``HEAD``, and ``DELETE`` requests, you can simply pass the
arguments as a dictionary in the ``fields`` argument to
:meth:`~poolmanager.PoolManager.request`:

.. code-block:: pycon

    >>> r = http.request(
    ...     'GET',
    ...     'http://httpbin.org/get',
    ...     fields={'arg': 'value'}
    ... )
    >>> json.loads(r.data.decode('utf-8'))['args']
    {'arg': 'value'}

For ``POST`` and ``PUT`` requests, you need to manually encode query parameters
in the URL:

.. code-block:: pycon

    >>> from urllib.parse import urlencode
    >>> encoded_args = urlencode({'arg': 'value'})
    >>> url = 'http://httpbin.org/post?' + encoded_args
    >>> r = http.request('POST', url)
    >>> json.loads(r.data.decode('utf-8'))['args']
    {'arg': 'value'}


.. _form_data:

Form Data
~~~~~~~~~

For ``PUT`` and ``POST`` requests, urllib3 will automatically form-encode the
dictionary in the ``fields`` argument provided to
:meth:`~poolmanager.PoolManager.request`:

.. code-block:: pycon

    >>> r = http.request(
    ...     'POST',
    ...     'http://httpbin.org/post',
    ...     fields={'field': 'value'}
    ... )
    >>> json.loads(r.data.decode('utf-8'))['form']
    {'field': 'value'}

JSON
~~~~

You can send a JSON request by specifying the encoded data as the ``body``
argument and setting the ``Content-Type`` header when calling
:meth:`~poolmanager.PoolManager.request`:

.. code-block:: pycon

    >>> import json
    >>> data = {'attribute': 'value'}
    >>> encoded_data = json.dumps(data).encode('utf-8')
    >>> r = http.request(
    ...     'POST',
    ...     'http://httpbin.org/post',
    ...     body=encoded_data,
    ...     headers={'Content-Type': 'application/json'}
    ... )
    >>> json.loads(r.data.decode('utf-8'))['json']
    {'attribute': 'value'}

Files & Binary Data
~~~~~~~~~~~~~~~~~~~

For uploading files using ``multipart/form-data`` encoding you can use the same
approach as :ref:`form_data` and specify the file field as a tuple of
``(file_name, file_data)``:

.. code-block:: pycon

    >>> with open('example.txt') as fp:
    ...     file_data = fp.read()
    >>> r = http.request(
    ...     'POST',
    ...     'http://httpbin.org/post',
    ...     fields={
    ...         'filefield': ('example.txt', file_data),
    ...     }
    ... )
    >>> json.loads(r.data.decode('utf-8'))['files']
    {'filefield': '...'}

While specifying the filename is not strictly required, it's recommended in
order to match browser behavior. You can also pass a third item in the tuple
to specify the file's MIME type explicitly:

.. code-block:: pycon

    >>> r = http.request(
    ...     'POST',
    ...     'http://httpbin.org/post',
    ...     fields={
    ...         'filefield': ('example.txt', file_data, 'text/plain'),
    ...     }
    ... )

For sending raw binary data simply specify the ``body`` argument. It's also
recommended to set the ``Content-Type`` header:

.. code-block:: pycon

    >>> with open('example.jpg', 'rb') as fp:
    ...     binary_data = fp.read()
    >>> r = http.request(
    ...     'POST',
    ...     'http://httpbin.org/post',
    ...     body=binary_data,
    ...     headers={'Content-Type': 'image/jpeg'}
    ... )
    >>> json.loads(r.data.decode('utf-8'))['data']
    b'...'

.. _ssl:

Certificate Verification
------------------------

.. note:: *New in version 1.25:*

    HTTPS connections are now verified by default (``cert_reqs = 'CERT_REQUIRED'``).

While you can disable certification verification by setting ``cert_reqs = 'CERT_NONE'``, it is highly recommend to leave it on.

Unless otherwise specified urllib3 will try to load the default system certificate stores.
The most reliable cross-platform method is to use the `certifi <https://certifi.io/>`_
package which provides Mozilla's root certificate bundle:

.. code-block:: bash

    $ python -m pip install certifi

You can also install certifi along with urllib3 by using the ``secure``
extra:

.. code-block:: bash

    $ python -m pip install urllib3[secure]

.. warning:: If you're using Python 2 you may need additional packages. See the :ref:`section below <ssl_py2>` for more details.

Once you have certificates, you can create a :class:`~poolmanager.PoolManager`
that verifies certificates when making requests:

.. code-block:: pycon

    >>> import certifi
    >>> import urllib3
    >>> http = urllib3.PoolManager(
    ...     cert_reqs='CERT_REQUIRED',
    ...     ca_certs=certifi.where()
    ... )

The :class:`~poolmanager.PoolManager` will automatically handle certificate
verification and will raise :class:`~exceptions.SSLError` if verification fails:

.. code-block:: pycon

    >>> http.request('GET', 'https://google.com')
    (No exception)
    >>> http.request('GET', 'https://expired.badssl.com')
    urllib3.exceptions.SSLError ...

.. note:: You can use OS-provided certificates if desired. Just specify the full
    path to the certificate bundle as the ``ca_certs`` argument instead of
    ``certifi.where()``. For example, most Linux systems store the certificates
    at ``/etc/ssl/certs/ca-certificates.crt``. Other operating systems can
    be `difficult <https://stackoverflow.com/questions/10095676/openssl-reasonable-default-for-trusted-ca-certificates>`_.

.. _ssl_py2:

Certificate Verification in Python 2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Older versions of Python 2 are built with an :mod:`ssl` module that lacks
:ref:`SNI support <sni_warning>` and can lag behind security updates. For these reasons it's recommended to use
`pyOpenSSL <https://pyopenssl.readthedocs.io/en/latest/>`_.

If you install urllib3 with the ``secure`` extra, all required packages for
certificate verification on Python 2 will be installed:

.. code-block:: bash

    $ python -m pip install urllib3[secure]

If you want to install the packages manually, you will need ``pyOpenSSL``,
``cryptography``, ``idna``, and ``certifi``.

.. note:: If you are not using macOS or Windows, note that `cryptography
    <https://cryptography.io/en/latest/>`_ requires additional system packages
    to compile. See `building cryptography on Linux
    <https://cryptography.io/en/latest/installation/#building-cryptography-on-linux>`_
    for the list of packages required.

Once installed, you can tell urllib3 to use pyOpenSSL by using :mod:`urllib3.contrib.pyopenssl`:

.. code-block:: pycon

    >>> import urllib3.contrib.pyopenssl
    >>> urllib3.contrib.pyopenssl.inject_into_urllib3()

Finally, you can create a :class:`~poolmanager.PoolManager` that verifies
certificates when performing requests:

.. code-block:: pycon

    >>> import certifi
    >>> import urllib3
    >>> http = urllib3.PoolManager(
    ...     cert_reqs='CERT_REQUIRED',
    ...     ca_certs=certifi.where()
    ... )

If you do not wish to use pyOpenSSL, you can simply omit the call to
:func:`urllib3.contrib.pyopenssl.inject_into_urllib3`. urllib3 will fall back
to the standard-library :mod:`ssl` module. You may experience
:ref:`several warnings <ssl_warnings>` when doing this.

.. warning:: If you do not use pyOpenSSL, Python must be compiled with ssl
    support for certificate verification to work. It is uncommon, but it is
    possible to compile Python without SSL support. See this
    `StackOverflow thread <https://stackoverflow.com/questions/5128845/importerror-no-module-named-ssl>`_
    for more details.

    If you are on Google App Engine, you must explicitly enable SSL
    support in your ``app.yaml``:

    .. code-block:: yaml

        libraries:
        - name: ssl
          version: latest

Using Timeouts
--------------

Timeouts allow you to control how long (in seconds) requests are allowed to run
before being aborted. In simple cases, you can specify a timeout as a ``float``
to :meth:`~poolmanager.PoolManager.request`:

.. code-block:: pycon

    >>> http.request(
    ...     'GET', 'http://httpbin.org/delay/3', timeout=4.0
    ... )
    <urllib3.response.HTTPResponse>
    >>> http.request(
    ...     'GET', 'http://httpbin.org/delay/3', timeout=2.5
    ... )
    MaxRetryError caused by ReadTimeoutError

For more granular control you can use a :class:`~util.timeout.Timeout`
instance which lets you specify separate connect and read timeouts:

.. code-block:: pycon

    >>> http.request(
    ...     'GET',
    ...     'http://httpbin.org/delay/3',
    ...     timeout=urllib3.Timeout(connect=1.0)
    ... )
    <urllib3.response.HTTPResponse>
    >>> http.request(
    ...     'GET',
    ...     'http://httpbin.org/delay/3',
    ...     timeout=urllib3.Timeout(connect=1.0, read=2.0)
    ... )
    MaxRetryError caused by ReadTimeoutError


If you want all requests to be subject to the same timeout, you can specify
the timeout at the :class:`~urllib3.poolmanager.PoolManager` level:

.. code-block:: pycon

    >>> http = urllib3.PoolManager(timeout=3.0)
    >>> http = urllib3.PoolManager(
    ...     timeout=urllib3.Timeout(connect=1.0, read=2.0)
    ... )

You still override this pool-level timeout by specifying ``timeout`` to
:meth:`~poolmanager.PoolManager.request`.

Retrying Requests
-----------------

urllib3 can automatically retry idempotent requests. This same mechanism also
handles redirects. You can control the retries using the ``retries`` parameter
to :meth:`~poolmanager.PoolManager.request`. By default, urllib3 will retry
requests 3 times and follow up to 3 redirects.

To change the number of retries just specify an integer:

.. code-block:: pycon

    >>> http.requests('GET', 'http://httpbin.org/ip', retries=10)

To disable all retry and redirect logic specify ``retries=False``:

.. code-block:: pycon

    >>> http.request(
    ...     'GET', 'http://nxdomain.example.com', retries=False
    ... )
    NewConnectionError
    >>> r = http.request(
    ...     'GET', 'http://httpbin.org/redirect/1', retries=False
    ... )
    >>> r.status
    302

To disable redirects but keep the retrying logic, specify ``redirect=False``:

.. code-block:: pycon

    >>> r = http.request(
    ...     'GET', 'http://httpbin.org/redirect/1', redirect=False
    ... )
    >>> r.status
    302

For more granular control you can use a :class:`~util.retry.Retry` instance.
This class allows you far greater control of how requests are retried.

For example, to do a total of 3 retries, but limit to only 2 redirects:

.. code-block:: pycon

    >>> http.request(
    ...     'GET',
    ...     'http://httpbin.org/redirect/3',
    ...     retries=urllib3.Retry(3, redirect=2)
    ... )
    MaxRetryError

You can also disable exceptions for too many redirects and just return the
``302`` response:

.. code-block:: pycon

    >>> r = http.request(
    ...     'GET',
    ...     'http://httpbin.org/redirect/3',
    ...     retries=urllib3.Retry(
    ...         redirect=2, raise_on_redirect=False)
    ... )
    >>> r.status
    302

If you want all requests to be subject to the same retry policy, you can
specify the retry at the :class:`~urllib3.poolmanager.PoolManager` level:

.. code-block:: pycon

    >>> http = urllib3.PoolManager(retries=False)
    >>> http = urllib3.PoolManager(
    ...     retries=urllib3.Retry(5, redirect=2)
    ... )

You still override this pool-level retry policy by specifying ``retries`` to
:meth:`~poolmanager.PoolManager.request`.

Errors & Exceptions
-------------------

urllib3 wraps lower-level exceptions, for example:

.. code-block:: pycon

    >>> try:
    ...     http.request('GET', 'nx.example.com', retries=False)
    ... except urllib3.exceptions.NewConnectionError:
    ...     print('Connection failed.')

See :mod:`~urllib3.exceptions` for the full list of all exceptions.

Logging
-------

If you are using the standard library :mod:`logging` module urllib3 will
emit several logs. In some cases this can be undesirable. You can use the
standard logger interface to change the log level for urllib3's logger:

.. code-block:: pycon

    >>> logging.getLogger("urllib3").setLevel(logging.WARNING)
