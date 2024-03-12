macOS SecureTransport
=====================

`SecureTranport <https://developer.apple.com/documentation/security/secure_transport>`_
support for urllib3 via ctypes.

This makes platform-native TLS available to urllib3 users on macOS without the
use of a compiler. This is an important feature because the Python Package
Index is moving to become a TLSv1.2-or-higher server, and the default OpenSSL
that ships with macOS is not capable of doing TLSv1.2. The only way to resolve
this is to give macOS users an alternative solution to the problem, and that
solution is to use SecureTransport.

We use ctypes here because this solution must not require a compiler. That's
because Pip is not allowed to require a compiler either.

This code is a bastardised version of the code found in Will Bond's
`oscrypto <https://github.com/wbond/oscrypto>`_ library. An enormous debt
is owed to him for blazing this trail for us. For that reason, this code
should be considered to be covered both by urllib3's license and by
`oscrypto's <https://github.com/wbond/oscrypto/blob/master/LICENSE>`_.

To use this module, simply import and inject it:

.. code-block:: python

    import urllib3.contrib.securetransport
    urllib3.contrib.securetransport.inject_into_urllib3()
