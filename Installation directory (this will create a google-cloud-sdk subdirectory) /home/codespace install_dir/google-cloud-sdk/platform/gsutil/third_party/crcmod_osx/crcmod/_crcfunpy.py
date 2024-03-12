#-----------------------------------------------------------------------------
# Low level CRC functions for use by crcmod.  This version is implemented in
# Python for a couple of reasons.  1) Provide a reference implememtation.
# 2) Provide a version that can be used on systems where a C compiler is not
# available for building extension modules.
#
# Copyright (c) 2004  Raymond L. Buvel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#-----------------------------------------------------------------------------

import sys
if sys.version_info.major > 2:
  long = int

def _crc8(data, crc, table):
    crc = crc & 0xFF
    for x in data:
        crc = table[ord(x) ^ crc]
    return crc

def _crc8r(data, crc, table):
    crc = crc & 0xFF
    for x in data:
        crc = table[ord(x) ^ crc]
    return crc

def _crc16(data, crc, table):
    crc = crc & 0xFFFF
    for x in data:
        crc = table[ord(x) ^ ((crc>>8) & 0xFF)] ^ ((crc << 8) & 0xFF00)
    return crc

def _crc16r(data, crc, table):
    crc = crc & 0xFFFF
    for x in data:
        crc = table[ord(x) ^ (crc & 0xFF)] ^ (crc >> 8)
    return crc

def _crc24(data, crc, table):
    crc = crc & 0xFFFFFF
    for x in data:
        crc = table[ord(x) ^ (int(crc>>16) & 0xFF)] ^ ((crc << 8) & 0xFFFF00)
    return crc

def _crc24r(data, crc, table):
    crc = crc & 0xFFFFFF
    for x in data:
        crc = table[ord(x) ^ int(crc & 0xFF)] ^ (crc >> 8)
    return crc

def _crc32(data, crc, table):
    crc = crc & long(0xFFFFFFFF)
    for x in data:
        crc = table[ord(x) ^ (int(crc>>24) & 0xFF)] ^ ((crc << 8) & long(0xFFFFFF00))
    return crc

def _crc32r(data, crc, table):
    crc = crc & long(0xFFFFFFFF)
    for x in data:
        crc = table[ord(x) ^ int(crc & long(0xFF))] ^ (crc >> 8)
    return crc

def _crc64(data, crc, table):
    crc = crc & long(0xFFFFFFFFFFFFFFFF)
    for x in data:
        crc = table[ord(x) ^ (int(crc>>56) & 0xFF)] ^ ((crc << 8) & long(0xFFFFFFFFFFFFFF00))
    return crc

def _crc64r(data, crc, table):
    crc = crc & long(0xFFFFFFFFFFFFFFFF)
    for x in data:
        crc = table[ord(x) ^ int(crc & long(0xFF))] ^ (crc >> 8)
    return crc

