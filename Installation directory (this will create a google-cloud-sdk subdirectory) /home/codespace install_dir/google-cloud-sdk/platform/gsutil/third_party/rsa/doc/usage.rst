.. _usage:

Usage
=====

This section describes the usage of the Python-RSA module.

Before you can use RSA you need keys. You will receive a private key
and a public key.

.. important::

    The private key is called *private* for a reason. Never share this
    key with anyone.

The public key is used for encrypting a message such that it can only
be read by the owner of the private key. As such it's also referred to
as the *encryption key*. Decrypting a message can only be done using
the private key, hence it's also called the *decryption key*.

The private key is used for signing a message. With this signature and
the public key, the receiver can verify that a message was signed
by the owner of the private key, and that the message was not modified
after signing.


Generating keys
---------------

You can use the :py:func:`rsa.newkeys` function to create a keypair:

    >>> import rsa
    >>> (pubkey, privkey) = rsa.newkeys(512)

Alternatively you can use :py:meth:`rsa.PrivateKey.load_pkcs1` and
:py:meth:`rsa.PublicKey.load_pkcs1` to load keys from a file:

    >>> import rsa
    >>> with open('private.pem', mode='rb') as privatefile:
    ...     keydata = privatefile.read()
    >>> privkey = rsa.PrivateKey.load_pkcs1(keydata)


Time to generate a key
++++++++++++++++++++++

Generating a keypair may take a long time, depending on the number of
bits required. The number of bits determines the cryptographic
strength of the key, as well as the size of the message you can
encrypt. If you don't mind having a slightly smaller key than you
requested, you can pass ``accurate=False`` to speed up the key
generation process.

Another way to speed up the key generation process is to use multiple
processes in parallel to speed up the key generation. Use no more than
the number of processes that your machine can run in parallel; a
dual-core machine should use ``poolsize=2``; a quad-core
hyperthreading machine can run two threads on each core, and thus can
use ``poolsize=8``.

    >>> (pubkey, privkey) = rsa.newkeys(512, poolsize=8)

These are some average timings from my desktop machine (Linux 2.6,
2.93 GHz quad-core Intel Core i7, 16 GB RAM) using 64-bit CPython 2.7.
Since key generation is a random process, times may differ even on
similar hardware. On all tests, we used the default ``accurate=True``.

+----------------+------------------+------------------+
| Keysize (bits) | single process   | eight processes  |
+================+==================+==================+
| 128            | 0.01 sec.        | 0.01 sec.        |
+----------------+------------------+------------------+
| 256            | 0.03 sec.        | 0.02 sec.        |
+----------------+------------------+------------------+
| 384            | 0.09 sec.        | 0.04 sec.        |
+----------------+------------------+------------------+
| 512            | 0.11 sec.        | 0.07 sec.        |
+----------------+------------------+------------------+
| 1024           | 0.79 sec.        | 0.30 sec.        |
+----------------+------------------+------------------+
| 2048           | 6.55 sec.        | 1.60 sec.        |
+----------------+------------------+------------------+
| 3072           | 23.4 sec.        | 7.14 sec.        |
+----------------+------------------+------------------+
| 4096           | 72.0 sec.        | 24.4 sec.        |
+----------------+------------------+------------------+

If key generation is too slow for you, you could use OpenSSL to
generate them for you, then load them in your Python code. OpenSSL
generates a 4096-bit key in 3.5 seconds on the same machine as used
above. See :ref:`openssl` for more information.


Encryption and decryption
-------------------------

To encrypt or decrypt a message, use :py:func:`rsa.encrypt` resp.
:py:func:`rsa.decrypt`. Let's say that Alice wants to send a message
that only Bob can read.

#. Bob generates a keypair, and gives the public key to Alice. This is
   done such that Alice knows for sure that the key is really Bob's
   (for example by handing over a USB stick that contains the key).

    >>> import rsa
    >>> (bob_pub, bob_priv) = rsa.newkeys(512)

#. Alice writes a message, and encodes it in UTF-8. The RSA module
   only operates on bytes, and not on strings, so this step is
   necessary.

    >>> message = 'hello Bob!'.encode('utf8')

#. Alice encrypts the message using Bob's public key, and sends the
   encrypted message.

    >>> import rsa
    >>> crypto = rsa.encrypt(message, bob_pub)

#. Bob receives the message, and decrypts it with his private key.

    >>> message = rsa.decrypt(crypto, bob_priv)
    >>> print(message.decode('utf8'))
    hello Bob!

Since Bob kept his private key *private*, Alice can be sure that he is
the only one who can read the message. Bob does *not* know for sure
that it was Alice that sent the message, since she didn't sign it.


RSA can only encrypt messages that are smaller than the key. A couple
of bytes are lost on random padding, and the rest is available for the
message itself. For example, a 512-bit key can encode a 53-byte
message (512 bit = 64 bytes, 11 bytes are used for random padding and
other stuff). See :ref:`bigfiles` for information on how to work with
larger files.

Altering the encrypted information will *likely* cause a
:py:class:`rsa.pkcs1.DecryptionError`. If you want to be *sure*, use
:py:func:`rsa.sign`.

    >>> crypto = rsa.encrypt(b'hello', bob_pub)
    >>> crypto = crypto[:-1] + b'X' # change the last byte
    >>> rsa.decrypt(crypto, bob_priv)
    Traceback (most recent call last):
    ...
    rsa.pkcs1.DecryptionError: Decryption failed


.. warning::

    Never display the stack trace of a
    :py:class:`rsa.pkcs1.DecryptionError` exception. It shows where
    in the code the exception occurred, and thus leaks information
    about the key. It’s only a tiny bit of information, but every bit
    makes cracking the keys easier.

Low-level operations
++++++++++++++++++++

The core RSA algorithm operates on large integers. These operations
are considered low-level and are supported by the
:py:func:`rsa.core.encrypt_int` and :py:func:`rsa.core.decrypt_int`
functions.

Signing and verification
------------------------

You can create a detached signature for a message using the
:py:func:`rsa.sign` function:

    >>> (pubkey, privkey) = rsa.newkeys(512)
    >>> message = 'Go left at the blue tree'
    >>> signature = rsa.sign(message, privkey, 'SHA-1')

This hashes the message using SHA-1. Other hash methods are also
possible, check the :py:func:`rsa.sign` function documentation for
details. The hash is then signed with the private key.

It is possible to calculate the hash and signature in separate operations
(i.e for generating the hash on a client machine and then sign with a
private key on remote server). To hash a message use the :py:func:`rsa.compute_hash`
function and then use the :py:func:`rsa.sign_hash` function to sign the hash:

    >>> message = 'Go left at the blue tree'
    >>> hash = rsa.compute_hash(message, 'SHA-1')
    >>> signature = rsa.sign_hash(hash, privkey, 'SHA-1')

In order to verify the signature, use the :py:func:`rsa.verify`
function. This function returns True if the verification is successful:

    >>> message = 'Go left at the blue tree'
    >>> rsa.verify(message, signature, pubkey)
    True

Modify the message, and the signature is no longer valid and a
:py:class:`rsa.pkcs1.VerificationError` is thrown:

    >>> message = 'Go right at the blue tree'
    >>> rsa.verify(message, signature, pubkey)
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/sybren/workspace/python-rsa/rsa/pkcs1.py", line 289, in verify
        raise VerificationError('Verification failed')
    rsa.pkcs1.VerificationError: Verification failed

.. warning::

    Never display the stack trace of a
    :py:class:`rsa.pkcs1.VerificationError` exception. It shows where
    in the code the exception occurred, and thus leaks information
    about the key. It's only a tiny bit of information, but every bit
    makes cracking the keys easier.

Instead of a message you can also call :py:func:`rsa.sign` and
:py:func:`rsa.verify` with a :py:class:`file`-like object. If the
message object has a ``read(int)`` method it is assumed to be a file.
In that case the file is hashed in 1024-byte blocks at the time.

    >>> with open('somefile', 'rb') as msgfile:
    ...     signature = rsa.sign(msgfile, privkey, 'SHA-1')

    >>> with open('somefile', 'rb') as msgfile:
    ...     rsa.verify(msgfile, signature, pubkey)


.. _bigfiles:

Working with big files
----------------------

RSA can only encrypt messages that are smaller than the key. A couple
of bytes are lost on random padding, and the rest is available for the
message itself. For example, a 512-bit key can encode a 53-byte
message (512 bit = 64 bytes, 11 bytes are used for random padding and
other stuff).

How it usually works
++++++++++++++++++++

The most common way to use RSA with larger files uses a block cypher
like AES or DES3 to encrypt the file with a random key, then encrypt
the random key with RSA. You would send the encrypted file along with
the encrypted key to the recipient. The complete flow is:

#. Generate a random key

    >>> import rsa.randnum
    >>> aes_key = rsa.randnum.read_random_bits(128)

#. Use that key to encrypt the file with AES.
#. :py:func:`Encrypt <rsa.encrypt>` the AES key with RSA

    >>> encrypted_aes_key = rsa.encrypt(aes_key, public_rsa_key)

#. Send the encrypted file together with ``encrypted_aes_key``
#. The recipient now reverses this process to obtain the encrypted
   file.

.. note::

    The Python-RSA module does not contain functionality to do the AES
    encryption for you.

Only using Python-RSA: the VARBLOCK format
++++++++++++++++++++++++++++++++++++++++++

.. warning::

    The VARBLOCK format is NOT recommended for general use, has been deprecated since
    Python-RSA 3.4, and has been removed in version 4.0. It's vulnerable to a
    number of attacks:

    1. decrypt/encrypt_bigfile() does not implement `Authenticated encryption`_ nor
       uses MACs to verify messages before decrypting public key encrypted messages.

    2. decrypt/encrypt_bigfile() does not use hybrid encryption (it uses plain RSA)
       and has no method for chaining, so block reordering is possible.

    See `issue #19 on GitHub`_ for more information.

.. _Authenticated encryption: https://en.wikipedia.org/wiki/Authenticated_encryption
.. _issue #19 on GitHub: https://github.com/sybrenstuvel/python-rsa/issues/13

As of Python-RSA version 4.0, the VARBLOCK format has been removed from the
library. For now, this section is kept here to document the issues with that
format, and ensure we don't do something like that again.
