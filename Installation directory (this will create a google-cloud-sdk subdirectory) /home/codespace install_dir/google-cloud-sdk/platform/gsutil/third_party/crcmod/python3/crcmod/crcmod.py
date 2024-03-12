#-----------------------------------------------------------------------------
# Copyright (c) 2010  Raymond L. Buvel
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
'''crcmod is a Python module for gererating objects that compute the Cyclic
Redundancy Check.  Any 8, 16, 24, 32, or 64 bit polynomial can be used.  

The following are the public components of this module.

Crc -- a class that creates instances providing the same interface as the
algorithms in the hashlib module in the Python standard library.  These
instances also provide a method for generating a C/C++ function to compute
the CRC.

mkCrcFun -- create a Python function to compute the CRC using the specified
polynomial and initial value.  This provides a much simpler interface if
all you need is a function for CRC calculation.
'''

__all__ = '''mkCrcFun Crc
'''.split()

# Select the appropriate set of low-level CRC functions for this installation.
# If the extension module was not built, drop back to the Python implementation
# even though it is significantly slower.
try:
    import crcmod._crcfunext as _crcfun
    _usingExtension = True
except ImportError:
    import crcmod._crcfunpy as _crcfun
    _usingExtension = False

import sys, struct

#-----------------------------------------------------------------------------
class Crc:
    '''Compute a Cyclic Redundancy Check (CRC) using the specified polynomial.

    Instances of this class have the same interface as the algorithms in the
    hashlib module in the Python standard library.  See the documentation of
    this module for examples of how to use a Crc instance.

    The string representation of a Crc instance identifies the polynomial,
    initial value, XOR out value, and the current CRC value.  The print
    statement can be used to output this information.

    If you need to generate a C/C++ function for use in another application,
    use the generateCode method.  If you need to generate code for another
    language, subclass Crc and override the generateCode method.

    The following are the parameters supplied to the constructor.

    poly -- The generator polynomial to use in calculating the CRC.  The value
    is specified as a Python integer.  The bits in this integer are the
    coefficients of the polynomial.  The only polynomials allowed are those
    that generate 8, 16, 24, 32, or 64 bit CRCs.

    initCrc -- Initial value used to start the CRC calculation.  This initial
    value should be the initial shift register value XORed with the final XOR
    value.  That is equivalent to the CRC result the algorithm should return for
    a zero-length string.  Defaults to all bits set because that starting value
    will take leading zero bytes into account.  Starting with zero will ignore
    all leading zero bytes.

    rev -- A flag that selects a bit reversed algorithm when True.  Defaults to
    True because the bit reversed algorithms are more efficient.

    xorOut -- Final value to XOR with the calculated CRC value.  Used by some
    CRC algorithms.  Defaults to zero.
    '''
    def __init__(self, poly, initCrc=~0, rev=True, xorOut=0, initialize=True):
        if not initialize:
            # Don't want to perform the initialization when using new or copy
            # to create a new instance.
            return

        (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)
        self.digest_size = sizeBits//8
        self.initCrc = initCrc
        self.xorOut = xorOut

        self.poly = poly
        self.reverse = rev

        (crcfun, table) = _mkCrcFun(poly, sizeBits, initCrc, rev, xorOut)
        self._crc = crcfun
        self.table = table

        self.crcValue = self.initCrc

    def __str__(self):
        lst = []
        lst.append('poly = 0x%X' % self.poly)
        lst.append('reverse = %s' % self.reverse)
        fmt = '0x%%0%dX' % (self.digest_size*2)
        lst.append('initCrc  = %s' % (fmt % self.initCrc))
        lst.append('xorOut   = %s' % (fmt % self.xorOut))
        lst.append('crcValue = %s' % (fmt % self.crcValue))
        return '\n'.join(lst)

    def new(self, arg=None):
        '''Create a new instance of the Crc class initialized to the same
        values as the original instance.  The current CRC is set to the initial
        value.  If a string is provided in the optional arg parameter, it is
        passed to the update method.
        '''
        n = Crc(poly=None, initialize=False)
        n._crc = self._crc
        n.digest_size = self.digest_size
        n.initCrc = self.initCrc
        n.xorOut = self.xorOut
        n.table = self.table
        n.crcValue = self.initCrc
        n.reverse = self.reverse
        n.poly = self.poly
        if arg is not None:
            n.update(arg)
        return n

    def copy(self):
        '''Create a new instance of the Crc class initialized to the same
        values as the original instance.  The current CRC is set to the current
        value.  This allows multiple CRC calculations using a common initial
        string.
        '''
        c = self.new()
        c.crcValue = self.crcValue
        return c

    def update(self, data):
        '''Update the current CRC value using the string specified as the data
        parameter.
        '''
        self.crcValue = self._crc(data, self.crcValue)

    def digest(self):
        '''Return the current CRC value as a string of bytes.  The length of
        this string is specified in the digest_size attribute.
        '''
        n = self.digest_size
        crc = self.crcValue
        lst = []
        while n > 0:
            lst.append(crc & 0xFF)
            crc = crc >> 8
            n -= 1
        lst.reverse()
        return bytes(lst)

    def hexdigest(self):
        '''Return the current CRC value as a string of hex digits.  The length
        of this string is twice the digest_size attribute.
        '''
        n = self.digest_size
        crc = self.crcValue
        lst = []
        while n > 0:
            lst.append('%02X' % (crc & 0xFF))
            crc = crc >> 8
            n -= 1
        lst.reverse()
        return ''.join(lst)

    def generateCode(self, functionName, out, dataType=None, crcType=None):
        '''Generate a C/C++ function.

        functionName -- String specifying the name of the function.

        out -- An open file-like object with a write method.  This specifies
        where the generated code is written.

        dataType -- An optional parameter specifying the data type of the input
        data to the function.  Defaults to UINT8.

        crcType -- An optional parameter specifying the data type of the CRC
        value.  Defaults to one of UINT8, UINT16, UINT32, or UINT64 depending
        on the size of the CRC value.
        '''
        if dataType is None:
            dataType = 'UINT8'

        if crcType is None:
            size = 8*self.digest_size
            if size == 24:
                size = 32
            crcType = 'UINT%d' % size

        if self.digest_size == 1:
            # Both 8-bit CRC algorithms are the same
            crcAlgor = 'table[*data ^ (%s)crc]'
        elif self.reverse:
            # The bit reverse algorithms are all the same except for the data
            # type of the crc variable which is specified elsewhere.
            crcAlgor = 'table[*data ^ (%s)crc] ^ (crc >> 8)'
        else:
            # The forward CRC algorithms larger than 8 bits have an extra shift
            # operation to get the high byte.
            shift = 8*(self.digest_size - 1)
            crcAlgor = 'table[*data ^ (%%s)(crc >> %d)] ^ (crc << 8)' % shift

        fmt = '0x%%0%dX' % (2*self.digest_size)
        if self.digest_size <= 4:
            fmt = fmt + 'U,'
        else:
            # Need the long long type identifier to keep gcc from complaining.
            fmt = fmt + 'ULL,'

        # Select the number of entries per row in the output code.
        n = {1:8, 2:8, 3:4, 4:4, 8:2}[self.digest_size]

        lst = []
        for i, val in enumerate(self.table):
            if (i % n) == 0:
                lst.append('\n    ')
            lst.append(fmt % val)

        poly = 'polynomial: 0x%X' % self.poly
        if self.reverse:
            poly = poly + ', bit reverse algorithm'

        if self.xorOut:
            # Need to remove the comma from the format.
            preCondition = '\n    crc = crc ^ %s;' % (fmt[:-1] % self.xorOut)
            postCondition = preCondition
        else:
            preCondition = ''
            postCondition = ''

        if self.digest_size == 3:
            # The 24-bit CRC needs to be conditioned so that only 24-bits are
            # used from the 32-bit variable.
            if self.reverse:
                preCondition += '\n    crc = crc & 0xFFFFFFU;'
            else:
                postCondition += '\n    crc = crc & 0xFFFFFFU;'
                

        parms = {
            'dataType' : dataType,
            'crcType' : crcType,
            'name' : functionName,
            'crcAlgor' : crcAlgor % dataType,
            'crcTable' : ''.join(lst),
            'poly' : poly,
            'preCondition' : preCondition,
            'postCondition' : postCondition,
        }
        out.write(_codeTemplate % parms) 

#-----------------------------------------------------------------------------
def mkCrcFun(poly, initCrc=~0, rev=True, xorOut=0):
    '''Return a function that computes the CRC using the specified polynomial.

    poly -- integer representation of the generator polynomial
    initCrc -- default initial CRC value
    rev -- when true, indicates that the data is processed bit reversed.
    xorOut -- the final XOR value

    The returned function has the following user interface
    def crcfun(data, crc=initCrc):
    '''

    # First we must verify the params
    (sizeBits, initCrc, xorOut) = _verifyParams(poly, initCrc, xorOut)
    # Make the function (and table), return the function
    return _mkCrcFun(poly, sizeBits, initCrc, rev, xorOut)[0]

#-----------------------------------------------------------------------------
# Naming convention:
# All function names ending with r are bit reverse variants of the ones
# without the r.

#-----------------------------------------------------------------------------
# Check the polynomial to make sure that it is acceptable and return the number
# of bits in the CRC.

def _verifyPoly(poly):
    msg = 'The degree of the polynomial must be 8, 16, 24, 32 or 64'
    for n in (8,16,24,32,64):
        low = 1<<n
        high = low*2
        if low <= poly < high:
            return n
    raise ValueError(msg)

#-----------------------------------------------------------------------------
# Bit reverse the input value.

def _bitrev(x, n):
    y = 0
    for i in range(n):
        y = (y << 1) | (x & 1)
        x = x >> 1
    return y

#-----------------------------------------------------------------------------
# The following functions compute the CRC for a single byte.  These are used
# to build up the tables needed in the CRC algorithm.  Assumes the high order
# bit of the polynomial has been stripped off.

def _bytecrc(crc, poly, n):
    mask = 1<<(n-1)
    for i in range(8):
        if crc & mask:
            crc = (crc << 1) ^ poly
        else:
            crc = crc << 1
    mask = (1<<n) - 1
    crc = crc & mask
    return crc

def _bytecrc_r(crc, poly, n):
    for i in range(8):
        if crc & 1:
            crc = (crc >> 1) ^ poly
        else:
            crc = crc >> 1
    mask = (1<<n) - 1
    crc = crc & mask
    return crc

#-----------------------------------------------------------------------------
# The following functions compute the table needed to compute the CRC.  The
# table is returned as a list.  Note that the array module does not support
# 64-bit integers on a 32-bit architecture as of Python 2.3.
#
# These routines assume that the polynomial and the number of bits in the CRC
# have been checked for validity by the caller.

def _mkTable(poly, n):
    mask = (1<<n) - 1
    poly = poly & mask
    table = [_bytecrc(i<<(n-8),poly,n) for i in range(256)]
    return table

def _mkTable_r(poly, n):
    mask = (1<<n) - 1
    poly = _bitrev(poly & mask, n)
    table = [_bytecrc_r(i,poly,n) for i in range(256)]
    return table

#-----------------------------------------------------------------------------
# Map the CRC size onto the functions that handle these sizes.

_sizeMap = {
     8 : [_crcfun._crc8, _crcfun._crc8r],
    16 : [_crcfun._crc16, _crcfun._crc16r],
    24 : [_crcfun._crc24, _crcfun._crc24r],
    32 : [_crcfun._crc32, _crcfun._crc32r],
    64 : [_crcfun._crc64, _crcfun._crc64r],
}

#-----------------------------------------------------------------------------
# Build a mapping of size to struct module type code.  This table is
# constructed dynamically so that it has the best chance of picking the best
# code to use for the platform we are running on.  This should properly adapt
# to 32 and 64 bit machines.

_sizeToTypeCode = {}

for typeCode in 'B H I L Q'.split():
    size = {1:8, 2:16, 4:32, 8:64}.get(struct.calcsize(typeCode),None)
    if size is not None and size not in _sizeToTypeCode:
        _sizeToTypeCode[size] = '256%s' % typeCode

_sizeToTypeCode[24] = _sizeToTypeCode[32]

del typeCode, size

#-----------------------------------------------------------------------------
# The following function validates the parameters of the CRC, namely,
# poly, and initial/final XOR values.
# It returns the size of the CRC (in bits), and "sanitized" initial/final XOR values.

def _verifyParams(poly, initCrc, xorOut):
    sizeBits = _verifyPoly(poly)

    mask = (1<<sizeBits) - 1

    # Adjust the initial CRC to the correct data type (unsigned value).
    initCrc = initCrc & mask

    # Similar for XOR-out value.
    xorOut = xorOut & mask

    return (sizeBits, initCrc, xorOut)

#-----------------------------------------------------------------------------
# The following function returns a Python function to compute the CRC.
#
# It must be passed parameters that are already verified & sanitized by
# _verifyParams().
#
# The returned function calls a low level function that is written in C if the
# extension module could be loaded.  Otherwise, a Python implementation is
# used.
#
# In addition to this function, a list containing the CRC table is returned.

def _mkCrcFun(poly, sizeBits, initCrc, rev, xorOut):
    if rev:
        tableList = _mkTable_r(poly, sizeBits)
        _fun = _sizeMap[sizeBits][1]
    else:
        tableList = _mkTable(poly, sizeBits)
        _fun = _sizeMap[sizeBits][0]

    _table = tableList
    if _usingExtension:
        _table = struct.pack(_sizeToTypeCode[sizeBits], *tableList)

    if xorOut == 0:
        def crcfun(data, crc=initCrc, table=_table, fun=_fun):
            return fun(data, crc, table)
    else:
        def crcfun(data, crc=initCrc, table=_table, fun=_fun):
            return xorOut ^ fun(data, xorOut ^ crc, table)

    return crcfun, tableList

#-----------------------------------------------------------------------------
_codeTemplate = '''// Automatically generated CRC function
// %(poly)s
%(crcType)s
%(name)s(%(dataType)s *data, int len, %(crcType)s crc)
{
    static const %(crcType)s table[256] = {%(crcTable)s
    };
    %(preCondition)s
    while (len > 0)
    {
        crc = %(crcAlgor)s;
        data++;
        len--;
    }%(postCondition)s
    return crc;
}
'''

