oauth2client
============

.. note:: oauth2client is now deprecated. No more features will be added to the
libraries and the core team is turning down support. We recommend you use
`google-auth`_ and `oauthlib`_. For more details on the deprecation, see `oauth2client deprecation`_.

.. _google-auth: https://google-auth.readthedocs.io
.. _oauthlib: http://oauthlib.readthedocs.io/
.. _oauth2client deprecation: https://google-auth.readthedocs.io/en/latest/oauth2client-deprecation.html

*making OAuth2 just a little less painful*

``oauth2client`` makes it easy to interact with OAuth2-protected resources,
especially those related to Google APIs. You can also start with `general
information about using OAuth2 with Google APIs
<https://developers.google.com/accounts/docs/OAuth2>`_.

Getting started
---------------

We recommend installing via ``pip``:

.. code-block:: bash

    $ pip install --upgrade oauth2client

You can also install from source:

.. code-block:: bash

    $ git clone https://github.com/google/oauth2client
    $ cd oauth2client
    $ python setup.py install

Using ``pypy``
--------------

-   In order to use crypto libraries (e.g. for service accounts) you will
    need to install one of ``pycrypto`` or ``pyOpenSSL``.
-   Using ``pycrypto`` with ``pypy`` will be in general problematic. If
    ``libgmp`` is installed on your machine, the ``pycrypto`` install will
    attempt to build ``_fastmath.c``. However, this file uses CPython
    implementation details and hence can't be built in ``pypy`` (as of
    ``pypy`` 2.6 and ``pycrypto`` 2.6.1). In order to install

    .. code-block:: bash

        with_gmp=no pip install --upgrade pycrypto

    See discussions on the `pypy issue tracker`_ and the
    `pycrypto issue tracker`_.

-   Using ``pyOpenSSL`` with versions of ``pypy`` before 2.6 may be in general
    problematic since ``pyOpenSSL`` depends on the ``cryptography`` library.
    For versions of ``cryptography`` before 1.0, importing ``pyOpenSSL``
    with it caused `massive startup costs`_. In order to address this
    slow startup, ``cryptography`` 1.0 made some `changes`_ in how it used
    ``cffi`` when means it can't be used on versions of ``pypy`` before 2.6.

    The default version of ``pypy`` you get when installed

    .. code-block:: bash

        apt-get install pypy pypy-dev

    on `Ubuntu 14.04`_ is 2.2.1. In order to upgrade, you'll need to use
    the `pypy/ppa PPA`_:

    .. code-block:: bash

        apt-get purge pypy pypy-dev
        add-apt-repository ppa:pypy/ppa
        apt-get update
        apt-get install pypy pypy-dev

.. _pypy issue tracker: https://bitbucket.org/pypy/pypy/issues/997
.. _pycrypto issue tracker: https://github.com/dlitz/pycrypto/pull/59
.. _massive startup costs: https://github.com/pyca/pyopenssl/issues/137
.. _changes: https://github.com/pyca/cryptography/issues/2275#issuecomment-130751514
.. _Ubuntu 14.04: http://packages.ubuntu.com/trusty/pypy
.. _pypy/ppa PPA: https://launchpad.net/~pypy/+archive/ubuntu/ppa

Downloads
^^^^^^^^^

* `Most recent release tarball
  <https://github.com/google/oauth2client/tarball/master>`_
* `Most recent release zipfile
  <https://github.com/google/oauth2client/zipball/master>`_
* `Complete release list <https://github.com/google/oauth2client/releases>`_

Library Documentation
---------------------

* Complete library index: :ref:`genindex`
* Index of all modules: :ref:`modindex`
* Search all documentation: :ref:`search`

Contributing
------------

Please see the `contributing page`_ for more information.
In particular, we love pull requests -- but please make sure to sign the
contributor license agreement.

.. _contributing page: https://github.com/google/oauth2client/blob/master/CONTRIBUTING.md

.. toctree::
   :maxdepth: 1
   :hidden:

   source/oauth2client

Supported Python Versions
-------------------------

We support Python 2.7 and 3.4+. (Whatever this file says, the truth is
always represented by our `tox.ini`_).

.. _tox.ini: https://github.com/google/oauth2client/blob/master/tox.ini

We explicitly decided to support Python 3 beginning with version
3.4. Reasons for this include:

* Encouraging use of newest versions of Python 3
* Following the lead of prominent `open-source projects`_
* Unicode literal support which
  allows for a cleaner codebase that works in both Python 2 and Python 3
* Prominent projects like `django`_ have `dropped support`_ for earlier
  versions (3.3 support dropped in December 2015, and 2.6 support
  `dropped`_ in September 2014)

.. _open-source projects: http://docs.python-requests.org/en/latest/
.. _Unicode literal support: https://www.python.org/dev/peps/pep-0414/
.. _django: https://docs.djangoproject.com/
.. _dropped support: https://docs.djangoproject.com/en/1.9/faq/install/#what-python-version-can-i-use-with-django
.. _dropped: https://docs.djangoproject.com/en/1.7/faq/install/#what-python-version-can-i-use-with-django
