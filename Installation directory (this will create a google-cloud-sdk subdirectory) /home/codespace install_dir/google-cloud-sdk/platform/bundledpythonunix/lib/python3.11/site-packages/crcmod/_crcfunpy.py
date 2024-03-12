#-----------------------------------------------------------------------------
# Low level CRC functions for use by crcmod.  This version is implemented in
# Python for a couple of reasons.  1) Provide a reference implememtation.
# 2) Provide a version that can be used on systems where a C compiler is not
# available for building extension modules.
#
# Copyright (c) 2009  Raymond L. Buvel
# Copyright (c) 2010  Craig McQueen
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

def _get_buffer_view(in_obj):
    if isinstance(in_obj, str):
        raise TypeError('Unicode-objects must be encoded before calculating a CRC')
    mv = memoryview(in_obj)
    if mv.ndim > 1:
        raise BufferError('Buffer must be single dimension')
    return mv


def _crc8(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFF
    for x in mv.tobytes():
        crc = table[x ^ crc]
    return crc

def _crc8r(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFF
    for x in mv.tobytes():
        crc = table[x ^ crc]
    return crc

def _crc16(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFF
    for x in mv.tobytes():
        crc = table[x ^ ((crc>>8) & 0xFF)] ^ ((crc << 8) & 0xFF00)
    return crc

def _crc16r(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFF
    for x in mv.tobytes():
        crc = table[x ^ (crc & 0xFF)] ^ (crc >> 8)
    return crc

def _crc24(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFFFF
    for x in mv.tobytes():
        crc = table[x ^ (crc>>16 & 0xFF)] ^ ((crc << 8) & 0xFFFF00)
    return crc

def _crc24r(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFFFF
    for x in mv.tobytes():
        crc = table[x ^ (crc & 0xFF)] ^ (crc >> 8)
    return crc

def _crc32(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFFFFFF
    for x in mv.tobytes():
        crc = table[x ^ ((crc>>24) & 0xFF)] ^ ((crc << 8) & 0xFFFFFF00)
    return crc

def _crc32r(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFFFFFF
    for x in mv.tobytes():
        crc = table[x ^ (crc & 0xFF)] ^ (crc >> 8)
    return crc

def _crc64(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFFFFFFFFFFFFFF
    for x in mv.tobytes():
        crc = table[x ^ ((crc>>56) & 0xFF)] ^ ((crc << 8) & 0xFFFFFFFFFFFFFF00)
    return crc

def _crc64r(data, crc, table):
    mv = _get_buffer_view(data)
    crc = crc & 0xFFFFFFFFFFFFFFFF
    for x in mv.tobytes():
        crc = table[x ^ (crc & 0xFF)] ^ (crc >> 8)
    return crc

