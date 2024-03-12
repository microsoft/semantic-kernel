
============
Introduction
============

The software in this package is a Python module for generating objects that
compute the Cyclic Redundancy Check (CRC).  It includes a (optional) C
extension for fast calculation, as well as a pure Python implementation.

There is no attempt in this package to explain how the CRC works.  There are a
number of resources on the web that give a good explanation of the algorithms.
Just do a Google search for "crc calculation" and browse till you find what you
need.  Another resource can be found in chapter 20 of the book "Numerical
Recipes in C" by Press et. al.

This package allows the use of any 8, 16, 24, 32, or 64 bit CRC.  You can
generate a Python function for the selected polynomial or an instance of the
:class:`crcmod.Crc` class which provides the same interface as the
:mod:`hashlib`, :mod:`md5` and :mod:`sha` modules from the Python standard
library.  A :class:`crcmod.Crc` class instance can also generate C/C++ source
code that can be used in another application.

----------
Guidelines
----------

Documentation is available here as well as from the doc strings.

It is up to you to decide what polynomials to use in your application.  Some
common CRC algorithms are predefined in :mod:`crcmod.predefined`.  If someone
has not specified the polynomials to use, you will need to do some research to
find one suitable for your application.  Examples are available in the unit
test script :file:`test.py`.

If you need to generate code for another language, I suggest you subclass the
:class:`crcmod.Crc` class and replace the method
:meth:`crcmod.Crc.generateCode`.  Use :meth:`crcmod.Crc.generateCode` as a
model for the new version.

------------
Dependencies
------------

Python Version
^^^^^^^^^^^^^^

The package has separate code to support the 2.x and 3.x Python series.

For the 2.x versions of Python, these versions have been tested:

* 2.4
* 2.5
* 2.6
* 2.7

It may still work on earlier versions of Python 2.x, but these have not been
recently tested.

For the 3.x versions of Python, these versions have been tested:

* 3.1

Building C extension
^^^^^^^^^^^^^^^^^^^^

To build the C extension, the appropriate compiler tools for your platform must
be installed. Refer to the Python documentation for building C extensions for
details.

------------
Installation
------------

The :mod:`crcmod` package is installed using :mod:`distutils`.
Run the following command::

   python setup.py install

If the extension module builds, it will be installed.  Otherwise, the
installation will include the pure Python version.  This will run significantly
slower than the extension module but will allow the package to be used.

For Windows users who want to use the mingw32 compiler, run this command::

    python setup.py build --compiler=mingw32 install

For Python 3.x, the install process is the same but you need to use the 3.x
interpreter.

------------
Unit Testing
------------

The :mod:`crcmod` package has a module :mod:`crcmod.test`, which contains
unit tests for both :mod:`crcmod` and :mod:`crcmod.predefined`.

When you first install :mod:`crcmod`, you should run the unit tests to make
sure everything is installed properly.  The test script performs a number of
tests including a comparison to the direct method which uses a class
implementing polynomials over the integers mod 2.

To run the unit tests on Python >=2.5::

    python -m crcmod.test

Alternatively, in the :file:`test` directory run::

    python test_crcmod.py

---------------
Code Generation
---------------

The :mod:`crcmod` package is capable of generating C functions that can be
compiled with a C or C++ compiler.  In the :file:`test` directory, there is an
:file:`examples.py` script that demonstrates how to use the code generator.
The result of this is written out to the file :file:`examples.c`.  The
generated code was checked to make sure it compiles with the GCC compiler.

-------
License
-------

The :mod:`crcmod` package is released under the MIT license.  See the
:file:`LICENSE` file for details.

----------
References
----------

.. seealso::

   :func:`binascii.crc32` function from the :mod:`binascii` module
      CRC-32 implementation
   
   :func:`zlib.crc32` function from the :mod:`zlib` module
      CRC-32 implementation

   Module :mod:`hashlib`
      Secure hash and message digest algorithms.

   Module :mod:`md5`
      RSA's MD5 message digest algorithm.

   Module :mod:`sha`
      NIST's secure hash algorithm, SHA.

   Module :mod:`hmac`
      Keyed-hashing for message authentication.
