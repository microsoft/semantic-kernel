google-auth
===========

.. toctree::
   :hidden:
   :maxdepth: 2

   user-guide
   Reference <reference/modules>

google-auth is the Google authentication library for Python. This library
provides the ability to authenticate to Google APIs using various methods. It
also provides integration with several HTTP libraries.

- Support for Google :func:`Application Default Credentials <google.auth.default>`.
- Support for signing and verifying :mod:`JWTs <google.auth.jwt>`.
- Support for creating `Google ID Tokens <user-guide.html#identity-tokens>`__.
- Support for verifying and decoding :mod:`ID Tokens <google.oauth2.id_token>`.
- Support for Google :mod:`Service Account credentials <google.oauth2.service_account>`.
- Support for Google :mod:`Impersonated Credentials <google.auth.impersonated_credentials>`.
- Support for :mod:`Google Compute Engine credentials <google.auth.compute_engine>`.
- Support for :mod:`Google App Engine standard credentials <google.auth.app_engine>`.
- Support for :mod:`Identity Pool credentials <google.auth.identity_pool>`.
- Support for :mod:`AWS credentials <google.auth.aws>`.
- Support for :mod:`Downscoping with Credential Access Boundaries credentials <google.auth.downscoped>`.
- Support for various transports, including
  :mod:`Requests <google.auth.transport.requests>`,
  :mod:`urllib3 <google.auth.transport.urllib3>`, and
  :mod:`gRPC <google.auth.transport.grpc>`.

.. note:: ``oauth2client`` was recently deprecated in favor of this library. For more details on the deprecation, see :doc:`oauth2client-deprecation`.

Installing
----------

google-auth can be installed with `pip`_::

    $ pip install --upgrade google-auth

google-auth is open-source, so you can alternatively grab the source code from
`GitHub`_ and install from source.


For more information on setting up your Python development environment, please refer to `Python Development Environment Setup Guide`_ for Google Cloud Platform.

.. _`Python Development Environment Setup Guide`: https://cloud.google.com/python/setup
.. _pip: https://pip.pypa.io
.. _GitHub: https://github.com/GoogleCloudPlatform/google-auth-library-python

Usage
-----

The :doc:`user-guide` is the place to go to learn how to use the library and
accomplish common tasks.

The :doc:`Module Reference <reference/modules>` documentation provides API-level documentation.

License
-------

google-auth is made available under the Apache License, Version 2.0. For more
details, see `LICENSE`_

.. _LICENSE:
    https://github.com/GoogleCloudPlatform/google-auth-library-python/blob/main/LICENSE

Contributing
------------

We happily welcome contributions, please see our `contributing`_ documentation
for details.

.. _contributing:
    https://github.com/GoogleCloudPlatform/google-auth-library-python/blob/main/CONTRIBUTING.rst
