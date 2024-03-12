Compatibility with standards
============================

.. index:: OpenSSL
.. index:: compatibility

Python-RSA implements encryption and signatures according to PKCS#1
version 1.5. This makes it compatible with the OpenSSL RSA module.

Keys are stored in PEM or DER format according to PKCS#1 v1.5. Private
keys are compatible with OpenSSL. However, OpenSSL uses X.509 for its
public keys, which are not supported.

Encryption:
    PKCS#1 v1.5 with at least 8 bytes of random padding

Signatures:
    PKCS#1 v1.5 using the following hash methods:
    MD5, SHA-1, SHA-224, SHA-256, SHA-384, SHA-512

Private keys:
    PKCS#1 v1.5 in PEM and DER format, ASN.1 type RSAPrivateKey

Public keys:
    PKCS#1 v1.5 in PEM and DER format, ASN.1 type RSAPublicKey

:ref:`VARBLOCK <bigfiles>` encryption:
    Deprecated in Python-RSA 3.4 and removed from Python-RSA 4.0.
    Was Python-RSA only, not compatible with any other known application.

.. _openssl:

Interoperability with OpenSSL
-----------------------------

You can create a 512-bit RSA key in OpenSSL as follows::

    openssl genrsa -out myprivatekey.pem 512

To get a Python-RSA-compatible public key from OpenSSL, you need the
private key first, then run it through the ``pyrsa-priv2pub``
command::

    pyrsa-priv2pub -i myprivatekey.pem -o mypublickey.pem

Encryption and decryption is also compatible::

    $ echo hello there > testfile.txt
    $ pyrsa-encrypt -i testfile.txt -o testfile.rsa publickey.pem
    $ openssl rsautl -in testfile.rsa -inkey privatekey.pem -decrypt
    hello there

Interoperability with PKCS#8
----------------------------

The standard PKCS#8 is widely used, and more complex than the PKCS#1
v1.5 supported by Python-RSA. In order to extract a key from the
PKCS#8 format you need an external tool such as OpenSSL::

    openssl rsa -in privatekey-pkcs8.pem -out privatekey.pem

You can then extract the corresponding public key as described above.
