Commandline interface
==================================================

A lot of the Python-RSA functionality is also available as commandline
scripts. On Linux and other unix-like systems they are executable
Python scripts, on Windows they are .exe files.

All scripts accept a ``--help`` parameter that give you instructions
on how to use them. Here is a short overview:

.. index:: CLI interface
.. index:: pyrsa-keygen, pyrsa-encrypt, pyrsa-decrypt, pyrsa-sign
.. index:: pyrsa-verify, pyrsa-priv2pub, pyrsa-encrypt-bigfile
.. index:: pyrsa-decrypt-bigfile, pyrsa-decrypt-bigfile

+-------------------------+--------------------------------------------------+-----------------------------------------+
| Command                 | Usage                                            | Core function                           |
+=========================+==================================================+=========================================+
| pyrsa-keygen            | Generates a new RSA keypair in PEM or DER format | :py:func:`rsa.newkeys`                  |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| pyrsa-encrypt           | Encrypts a file. The file must be shorter than   | :py:func:`rsa.encrypt`                  |
|                         | the key length in order to be encrypted.         |                                         |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| pyrsa-decrypt           | Decrypts a file.                                 | :py:func:`rsa.decrypt`                  |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| pyrsa-sign              | Signs a file, outputs the signature.             | :py:func:`rsa.sign`                     |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| pyrsa-verify            | Verifies a signature. The result is written to   | :py:func:`rsa.verify`                   |
|                         | the console as well as returned in the exit      |                                         |
|                         | status code.                                     |                                         |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| pyrsa-priv2pub          | Reads a private key and outputs the              | \-                                      |
|                         | corresponding public key.                        |                                         |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| *pyrsa-encrypt-bigfile* | *Encrypts a file to an encrypted VARBLOCK file.  | *Deprecated in Python-RSA 3.4 and       |
|                         | The file can be larger than the key length, but  | removed from version 4.0.*              |
|                         | the output file is only compatible with          |                                         |
|                         | Python-RSA.*                                     |                                         |
+-------------------------+--------------------------------------------------+-----------------------------------------+
| *pyrsa-decrypt-bigfile* | *Decrypts an encrypted VARBLOCK file.*           | *Deprecated in Python-RSA 3.4 and       |
|                         |                                                  | removed from version 4.0.*              |
+-------------------------+--------------------------------------------------+-----------------------------------------+
