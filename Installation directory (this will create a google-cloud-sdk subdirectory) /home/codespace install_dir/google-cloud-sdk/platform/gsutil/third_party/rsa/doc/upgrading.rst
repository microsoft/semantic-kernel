Upgrading from older versions
=============================

From versions older than Python-RSA 4.0
---------------------------------------

Support for the VARBLOCK/bigfile format has been dropped in version 4.0, after
being deprecated for a year. There is no alternative implementation in
Python-RSA 4.0. If you need this, or have ideas on how to do handle encryption
of large files securely and in a compatible way with existing standards,
`open a ticket to discuss this`_.

.. _open a ticket to discuss this:
    https://github.com/sybrenstuvel/python-rsa/issues/new


From versions older than Python-RSA 3.4
---------------------------------------

Previous versions of Python-RSA were less secure than the current
version. In order to be able to gradually upgrade your software, those
old versions will be available until Python-RSA 4.0.

To use version 1.3.3, use this::

    import rsa._version133 as rsa

And to use version 2.0, use this::

    import rsa._version200 as rsa

You can import all three versions at the same time. This allows you to
use an old version to decrypt your messages, and a new version to
re-encrypt them::

    import rsa._version200 as rsa200
    import rsa                        # this imports version 3.0

    decrypted = rsa200.decrypt(old_crypto, version_200_private_key)
    new_crypto = rsa.encrypt(decrypted, version_3_public_key)

Those import statements *will create warnings* as they import much
less secure code into your project.

.. warning::

    These modules are included to allow upgrading to the latest version
    of Python-RSA, and not as a way to keep using those old versions.
    They will be removed in version 4.0.

The random padding introduced in version 3.0 made things much more
secure, but also requires a larger key to encrypt the same message.


Converting keys
---------------

Version 3.0 introduced industrial standard RSA keys according to
PKCS#1. The old keys were just dictionaries. To convert a key from an
older version of Python-RSA, use the following::

    import rsa

    # Load the old key somehow.
    old_pub_key = {
        'e': 65537,
        'n': 31698122414741849421263704398157795847591L
    }

    old_priv_key = {
        'd': 7506520894712811128876594754922157377793L,
        'p': 4169414332984308880603L,
        'q': 7602535963858869797L
    }

    # Create new key objects like this:
    pub_key = rsa.PublicKey(n=old_pub_key['n'], e=old_pub_key['e'])

    priv_key = rsa.PrivateKey(n=old_pub_key['n'], e=old_pub_key['e'],
        d=old_priv_key['d'], p=old_priv_key['p'], q=old_priv_key['q'])


    # Or use this shorter notation:
    pub_key = rsa.PublicKey(**old_pub_key)

    old_priv_key.update(old_pub_key)
    priv_key = rsa.PrivateKey(**old_priv_key)
