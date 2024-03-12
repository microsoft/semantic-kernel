
:mod:`crcmod` -- CRC calculation
================================

.. module:: crcmod
   :synopsis: CRC calculation
.. moduleauthor:: Raymond L Buvel
.. sectionauthor:: Craig McQueen

This module provides a function factory :func:`mkCrcFun` and a class :class:`Crc`
for calculating CRCs of byte strings using common CRC algorithms.

.. note:: This documentation normally shows Python 2.x usage. Python 3.x usage is very similar,
    with the main difference that input strings must be explicitly defined as
    :keyword:`bytes` type, or an object that supports the buffer protocol. E.g.::

       >>> crc_value = crc_function(b'123456789')
       
       >>> crc_value = crc_function(bytearray((49, 50, 51, 52, 53, 54, 55, 56, 57)))


:func:`mkCrcFun` -- CRC function factory
----------------------------------------

The function factory provides a simple interface for CRC calculation.

.. function:: mkCrcFun(poly[, initCrc, rev, xorOut])

   Function factory that returns a new function for calculating CRCs
   using a specified CRC algorithm.

   :param poly:     The generator polynomial to use in calculating the CRC.  The value
                    is specified as a Python integer or long integer.  The bits in this integer
                    are the coefficients of the polynomial.  The only polynomials allowed are
                    those that generate 8, 16, 24, 32, or 64 bit CRCs.

   :param initCrc:  Initial value used to start the CRC calculation.  This initial
                    value should be the initial shift register value, reversed if it uses a
                    reversed algorithm, and then XORed with the final XOR value.  That is
                    equivalent to the CRC result the algorithm should return for a
                    zero-length string.  Defaults to all bits set because that starting value
                    will take leading zero bytes into account.  Starting with zero will ignore
                    all leading zero bytes.

   :param rev:      A flag that selects a bit reversed algorithm when :keyword:`True`.  Defaults to
                    :keyword:`True` because the bit reversed algorithms are more efficient.

   :param xorOut:   Final value to XOR with the calculated CRC value.  Used by some
                    CRC algorithms.  Defaults to zero.

   :return:         CRC calculation function
   :rtype:          function

   The function that is returned is as follows:
   
   .. function:: .crc_function(data[, crc=initCrc])

   :param data:     Data for which to calculate the CRC.
   :type data:      byte string

   :param crc:      Initial CRC value.

   :return:         Calculated CRC value.
   :rtype:          integer

Examples
^^^^^^^^

**CRC-32** Example::

   >>> import crcmod
   
   >>> crc32_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
   >>> hex(crc32_func('123456789'))
   '0xcbf43926L'

The CRC-32 uses a "reversed" algorithm, used for many common CRC algorithms.
Less common is the non-reversed algorithm, as used by the 16-bit **XMODEM** CRC::

   >>> xmodem_crc_func = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
   >>> hex(xmodem_crc_func('123456789'))
   '0x31c3'

The CRC function can be called multiple times. On subsequent calls, pass the
CRC value previously calculated as a second parameter::

   >>> crc_value = crc32_func('1234')
   >>> crc_value = crc32_func('56789', crc_value)
   >>> hex(crc_value)
   '0xcbf43926L'

Python 3.x example: Unicode strings are not accepted as input. Byte strings are acceptable.
You may calculate a CRC for an object that implements the buffer protocol::

   >>> import crcmod
   >>> crc32_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
   >>> hex(crc32_func('123456789'))
   ...
   TypeError: Unicode-objects must be encoded before calculating a CRC
   >>> hex(crc32_func(b'123456789'))
   '0xcbf43926'
   >>> hex(crc32_func(bytearray((49, 50, 51, 52, 53, 54, 55, 56, 57))))
   '0xcbf43926'


Class :class:`Crc`
------------------

The class provides an interface similar to the Python :mod:`hashlib`, :mod:`md5` and :mod:`sha` modules.

.. class:: Crc(poly[, initCrc, rev, xorOut])

   Returns a new :class:`Crc` object for calculating CRCs using a specified CRC algorithm.
   
   The parameters are the same as those for the factory function :func:`mkCrcFun`.

   :param poly:     The generator polynomial to use in calculating the CRC.  The value
                    is specified as a Python integer or long integer.  The bits in this integer
                    are the coefficients of the polynomial.  The only polynomials allowed are
                    those that generate 8, 16, 24, 32, or 64 bit CRCs.

   :param initCrc:  Initial value used to start the CRC calculation.  This initial
                    value should be the initial shift register value, reversed if it uses a
                    reversed algorithm, and then XORed with the final XOR value.  That is
                    equivalent to the CRC result the algorithm should return for a
                    zero-length string.  Defaults to all bits set because that starting value
                    will take leading zero bytes into account.  Starting with zero will ignore
                    all leading zero bytes.

   :param rev:      A flag that selects a bit reversed algorithm when :keyword:`True`.  Defaults to
                    :keyword:`True` because the bit reversed algorithms are more efficient.

   :param xorOut:   Final value to XOR with the calculated CRC value.  Used by some
                    CRC algorithms.  Defaults to zero.

   :class:`Crc` objects contain the following constant values:

   .. attribute:: digest_size

      The size of the resulting digest in bytes. This depends on the width of the CRC polynomial.
      E.g. for a 32-bit CRC, :data:`digest_size` will be ``4``.

   .. attribute:: crcValue

      The calculated CRC value, as an integer, for the data that has been input
      using :meth:`update`. This value is updated after each call to :meth:`update`.

   :class:`Crc` objects support the following methods:

   .. method:: new([arg])

      Create a new instance of the :class:`Crc` class initialized to the same
      values as the original instance.  The CRC value is set to the initial
      value.  If a string is provided in the optional ``arg`` parameter, it is
      passed to the :meth:`update` method.

   .. method:: copy()

      Create a new instance of the :class:`Crc` class initialized to the same
      values as the original instance.  The CRC value is copied from the current
      value.  This allows multiple CRC calculations using a common initial
      string.

   .. method:: update(data)

      :param data:     Data for which to calculate the CRC
      :type data:      byte string

      Update the calculated CRC value for the specified input data.

   .. method:: digest()

      Return the current CRC value as a string of bytes.  The length of
      this string is specified in the :attr:`digest_size` attribute.

   .. method:: hexdigest()

      Return the current CRC value as a string of hex digits.  The length
      of this string is twice the :attr:`digest_size` attribute.

   .. method:: generateCode(functionName, out, [dataType, crcType])

      Generate a C/C++ function.

      :param functionName: String specifying the name of the function.

      :param out:       An open file-like object with a write method.
                        This specifies where the generated code is written.

      :param dataType:  An optional parameter specifying the data type of the input
                        data to the function.  Defaults to ``UINT8``.

      :param crcType:   An optional parameter specifying the data type of the CRC value.
                        Defaults to one of ``UINT8``, ``UINT16``, ``UINT32``, or ``UINT64`` depending
                        on the size of the CRC value.

Examples
^^^^^^^^

**CRC-32** Example::

   >>> import crcmod
   
   >>> crc32 = crcmod.Crc(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF)
   >>> crc32.update('123456789')
   >>> hex(crc32.crcValue)
   '0xcbf43926L'
   >>> crc32.hexdigest()
   'CBF43926'

The :meth:`Crc.update` method can be called multiple times, and the CRC value is updated with each call::

   >>> crc32new = crc32.new()
   >>> crc32new.update('1234')
   >>> crc32new.hexdigest()
   '9BE3E0A3'
   >>> crc32new.update('56789')
   >>> crc32new.hexdigest()
   'CBF43926'
