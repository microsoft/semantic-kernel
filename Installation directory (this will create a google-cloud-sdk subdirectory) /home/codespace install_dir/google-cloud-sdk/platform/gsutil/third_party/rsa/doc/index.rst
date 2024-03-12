.. Python-RSA documentation master file, created by
   sphinx-quickstart on Sat Jul 30 23:11:07 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Python-RSA's documentation!
======================================

Python-RSA is a pure-Python RSA implementation. It supports
encryption and decryption, signing and verifying signatures, and key
generation according to PKCS#1 version 1.5.

If you have the time and skill to improve the implementation, by all
means be my guest. The best way is to clone the `Git
repository`_ and send me a merge request when you've got something
worth merging.

.. _`Git repository`: https://github.com/sybrenstuvel/python-rsa


Security notice
---------------

This RSA implementation has seen the eyes of a security expert, and it
uses an industry standard random padding method. However, there are
still possible vectors of attack. Just to name one example, it doesn't
compress the input stream to remove repetitions, and if you display
the stack trace of a :py:class:`rsa.pkcs1.CryptoError` exception
you'll leak information about the reason why decryption or
verification failed.

I'm sure that those aren't the only insecurities. Use your own
judgement to decide whether this module is secure enough for your
application.

Contents
--------

.. toctree::
    :maxdepth: 2
    :numbered:

    intro
    installation
    upgrading
    licence
    usage
    cli
    compatibility
    reference


* :ref:`genindex`
* :ref:`search`
