Introduction & history
======================

Python-RSA's history starts in 2006. As a student assignment for the
University of Amsterdam we wrote a RSA implementation. We chose Python
for various reasons; one of the most important reasons was the
`unlimited precision integer`_ support.

.. _`unlimited precision integer`:
    https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex

It started out as just a module for calculating large primes, and RSA
encryption, decryption, signing and verification using those large
numbers. It also included generating public and private keys. There
was no functionality for working with byte sequences (such as files)
yet.

Version 1.0 did include support for byte sequences, but quite clunky,
mostly because it didn't support 0-bytes and thus was unsuitable for
binary messages.

Version 2.0 introduced a lot of improvements by Barry Mead, but still
wasn't compatible with other RSA implementations and used no random
padding.

Version 3.0 introduced PKCS#1 v1.5 functionality, which resulted in
compatibility with OpenSSL and many others implementing the same
standard. Random padding was introduced that considerably increased
security, which also resulted in the ability to encrypt and decrypt
binary messages.

Key generation was also improved in version 3.0, ensuring that you
really get the number of bits you asked for. At the same time key
generation speed was greatly improved. The ability to save and load
public and private keys in PEM and DER format as also added.



