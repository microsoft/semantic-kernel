
:mod:`crcmod.predefined` -- CRC calculation using predefined algorithms
=======================================================================

.. module:: crcmod.predefined
   :synopsis: CRC calculation using predefined algorithms
.. moduleauthor:: Craig McQueen
.. sectionauthor:: Craig McQueen

This module provides a function factory :func:`mkPredefinedCrcFun` and a class :class:`PredefinedCrc`
for calculating CRCs of byte strings using common predefined CRC algorithms.

The function factory and the class are very similar to those defined in :mod:`crcmod`,
except that the CRC algorithm is specified by a predefined name, rather than the
individual polynomial, reflection, and initial and final-XOR parameters.

Predefined CRC algorithms
-------------------------

The :mod:`crcmod.predefined` module offers the following predefined algorithms:

================================  ======================  ==========  ====================  ====================  ====================
Name                              Polynomial              Reversed?   Init-value            XOR-out               Check
================================  ======================  ==========  ====================  ====================  ====================
``crc-8``                         0x107                   False       0x00                  0x00                  0xF4
``crc-8-darc``                    0x139                   True        0x00                  0x00                  0x15
``crc-8-i-code``                  0x11D                   False       0xFD                  0x00                  0x7E
``crc-8-itu``                     0x107                   False       0x55                  0x55                  0xA1
``crc-8-maxim``                   0x131                   True        0x00                  0x00                  0xA1
``crc-8-rohc``                    0x107                   True        0xFF                  0x00                  0xD0
``crc-8-wcdma``                   0x19B                   True        0x00                  0x00                  0x25
``crc-16``                        0x18005                 True        0x0000                0x0000                0xBB3D
``crc-16-buypass``                0x18005                 False       0x0000                0x0000                0xFEE8
``crc-16-dds-110``                0x18005                 False       0x800D                0x0000                0x9ECF
``crc-16-dect``                   0x10589                 False       0x0001                0x0001                0x007E
``crc-16-dnp``                    0x13D65                 True        0xFFFF                0xFFFF                0xEA82
``crc-16-en-13757``               0x13D65                 False       0xFFFF                0xFFFF                0xC2B7
``crc-16-genibus``                0x11021                 False       0x0000                0xFFFF                0xD64E
``crc-16-maxim``                  0x18005                 True        0xFFFF                0xFFFF                0x44C2
``crc-16-mcrf4xx``                0x11021                 True        0xFFFF                0x0000                0x6F91
``crc-16-riello``                 0x11021                 True        0x554D                0x0000                0x63D0
``crc-16-t10-dif``                0x18BB7                 False       0x0000                0x0000                0xD0DB
``crc-16-teledisk``               0x1A097                 False       0x0000                0x0000                0x0FB3
``crc-16-usb``                    0x18005                 True        0x0000                0xFFFF                0xB4C8
``x-25``                          0x11021                 True        0x0000                0xFFFF                0x906E
``xmodem``                        0x11021                 False       0x0000                0x0000                0x31C3
``modbus``                        0x18005                 True        0xFFFF                0x0000                0x4B37
``kermit`` [#ccitt]_              0x11021                 True        0x0000                0x0000                0x2189
``crc-ccitt-false`` [#ccitt]_     0x11021                 False       0xFFFF                0x0000                0x29B1
``crc-aug-ccitt`` [#ccitt]_       0x11021                 False       0x1D0F                0x0000                0xE5CC
``crc-24``                        0x1864CFB               False       0xB704CE              0x000000              0x21CF02
``crc-24-flexray-a``              0x15D6DCB               False       0xFEDCBA              0x000000              0x7979BD
``crc-24-flexray-b``              0x15D6DCB               False       0xABCDEF              0x000000              0x1F23B8
``crc-32``                        0x104C11DB7             True        0x00000000            0xFFFFFFFF            0xCBF43926
``crc-32-bzip2``                  0x104C11DB7             False       0x00000000            0xFFFFFFFF            0xFC891918
``crc-32c``                       0x11EDC6F41             True        0x00000000            0xFFFFFFFF            0xE3069283
``crc-32d``                       0x1A833982B             True        0x00000000            0xFFFFFFFF            0x87315576
``crc-32-mpeg``                   0x104C11DB7             False       0xFFFFFFFF            0x00000000            0x0376E6E7
``posix``                         0x104C11DB7             False       0xFFFFFFFF            0xFFFFFFFF            0x765E7680
``crc-32q``                       0x1814141AB             False       0x00000000            0x00000000            0x3010BF7F
``jamcrc``                        0x104C11DB7             True        0xFFFFFFFF            0x00000000            0x340BC6D9
``xfer``                          0x1000000AF             False       0x00000000            0x00000000            0xBD0BE338
``crc-64``                        0x1000000000000001B     True        0x0000000000000000    0x0000000000000000    0x46A5A9388A5BEFFE
``crc-64-we``                     0x142F0E1EBA9EA3693     False       0x0000000000000000    0xFFFFFFFFFFFFFFFF    0x62EC59E3F1A4F00A
``crc-64-jones``                  0x1AD93D23594C935A9     True        0xFFFFFFFFFFFFFFFF    0x0000000000000000    0xCAA717168609F281
================================  ======================  ==========  ====================  ====================  ====================

.. rubric:: Notes

.. [#ccitt] Definitions of CCITT are disputable. See:

    * http://homepages.tesco.net/~rainstorm/crc-catalogue.htm
    * http://web.archive.org/web/20071229021252/http://www.joegeluso.com/software/articles/ccitt.htm

:func:`mkPredefinedCrcFun` -- CRC function factory
--------------------------------------------------

The function factory provides a simple interface for CRC calculation. It is similar
to :func:`crcmod.mkCrcFun`, except that it specifies a CRC algorithm by name rather
than its parameters.

.. function:: mkPredefinedCrcFun(crc_name)

   Function factory that returns a new function for calculating CRCs
   using a specified CRC algorithm.

   :param crc_name: The name of the predefined CRC algorithm to use.
   :type crc_name:  string

   :return:         CRC calculation function
   :rtype:          function

   The function that is returned is the same as that returned by :func:`crcmod.mkCrcFun`:
   
   .. function:: .crc_function(data[, crc=initCrc])

   :param data:     Data for which to calculate the CRC.
   :type data:      byte string

   :param crc:      Initial CRC value.

   :return:         Calculated CRC value.
   :rtype:          integer

.. function:: mkCrcFun(crc_name)

   This is an alias for :func:`crcmod.predefined.mkPredefinedCrcFun`. However, it is not defined when
   :mod:`crcmod.predefined` is imported using the form::
   
       >>> from crcmod.predefined import *

Examples
^^^^^^^^

**CRC-32** example::

   >>> import crcmod.predefined
   
   >>> crc32_func = crcmod.predefined.mkCrcFun('crc-32')
   >>> hex(crc32_func('123456789'))
   '0xcbf43926L'

**XMODEM** example::

   >>> xmodem_crc_func = crcmod.predefined.mkCrcFun('xmodem')
   >>> hex(xmodem_crc_func('123456789'))
   '0x31c3'


Class :class:`PredefinedCrc`
----------------------------

This class is inherited from the :class:`crcmod.Crc` class, and is the same except for the
initialization.  It specifies a CRC algorithm by name rather than its parameters.

.. class:: PredefinedCrc(crc_name)

   Returns a new :class:`Crc` object for calculating CRCs using a specified CRC algorithm.
   
   The parameter is the same as that for the factory function :func:`crcmod.predefined.mkPredefinedCrcFun`.

   :param crc_name: The name of the predefined CRC algorithm to use.
   :type crc_name:  string

.. class:: Crc(poly[, initCrc, rev, xorOut])

   This is an alias for :class:`crcmod.predefined.PredefinedCrc`. However, it is not defined when
   :mod:`crcmod.predefined` is imported using the form::
   
       >>> from crcmod.predefined import *

Examples
^^^^^^^^

**CRC-32** Example::

   >>> import crcmod.predefined
   
   >>> crc32 = crcmod.predefined.Crc('crc-32')
   >>> crc32.update('123456789')
   >>> hex(crc32.crcValue)
   '0xcbf43926L'
   >>> crc32.hexdigest()
   'CBF43926'
