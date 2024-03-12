# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2009-2017 Nominum, Inc.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose with or without fee is hereby granted,
# provided that the above copyright notice and this permission notice
# appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND NOMINUM DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL NOMINUM BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""EDNS Options"""

from __future__ import absolute_import

import math
import struct

import dns.inet

#: NSID
NSID = 3
#: DAU
DAU = 5
#: DHU
DHU = 6
#: N3U
N3U = 7
#: ECS (client-subnet)
ECS = 8
#: EXPIRE
EXPIRE = 9
#: COOKIE
COOKIE = 10
#: KEEPALIVE
KEEPALIVE = 11
#: PADDING
PADDING = 12
#: CHAIN
CHAIN = 13

class Option(object):

    """Base class for all EDNS option types."""

    def __init__(self, otype):
        """Initialize an option.

        *otype*, an ``int``, is the option type.
        """
        self.otype = otype

    def to_wire(self, file):
        """Convert an option to wire format.
        """
        raise NotImplementedError

    @classmethod
    def from_wire(cls, otype, wire, current, olen):
        """Build an EDNS option object from wire format.

        *otype*, an ``int``, is the option type.

        *wire*, a ``binary``, is the wire-format message.

        *current*, an ``int``, is the offset in *wire* of the beginning
        of the rdata.

        *olen*, an ``int``, is the length of the wire-format option data

        Returns a ``dns.edns.Option``.
        """

        raise NotImplementedError

    def _cmp(self, other):
        """Compare an EDNS option with another option of the same type.

        Returns < 0 if < *other*, 0 if == *other*, and > 0 if > *other*.
        """
        raise NotImplementedError

    def __eq__(self, other):
        if not isinstance(other, Option):
            return False
        if self.otype != other.otype:
            return False
        return self._cmp(other) == 0

    def __ne__(self, other):
        if not isinstance(other, Option):
            return False
        if self.otype != other.otype:
            return False
        return self._cmp(other) != 0

    def __lt__(self, other):
        if not isinstance(other, Option) or \
                self.otype != other.otype:
            return NotImplemented
        return self._cmp(other) < 0

    def __le__(self, other):
        if not isinstance(other, Option) or \
                self.otype != other.otype:
            return NotImplemented
        return self._cmp(other) <= 0

    def __ge__(self, other):
        if not isinstance(other, Option) or \
                self.otype != other.otype:
            return NotImplemented
        return self._cmp(other) >= 0

    def __gt__(self, other):
        if not isinstance(other, Option) or \
                self.otype != other.otype:
            return NotImplemented
        return self._cmp(other) > 0


class GenericOption(Option):

    """Generic Option Class

    This class is used for EDNS option types for which we have no better
    implementation.
    """

    def __init__(self, otype, data):
        super(GenericOption, self).__init__(otype)
        self.data = data

    def to_wire(self, file):
        file.write(self.data)

    def to_text(self):
        return "Generic %d" % self.otype

    @classmethod
    def from_wire(cls, otype, wire, current, olen):
        return cls(otype, wire[current: current + olen])

    def _cmp(self, other):
        if self.data == other.data:
            return 0
        if self.data > other.data:
            return 1
        return -1


class ECSOption(Option):
    """EDNS Client Subnet (ECS, RFC7871)"""

    def __init__(self, address, srclen=None, scopelen=0):
        """*address*, a ``text``, is the client address information.

        *srclen*, an ``int``, the source prefix length, which is the
        leftmost number of bits of the address to be used for the
        lookup.  The default is 24 for IPv4 and 56 for IPv6.

        *scopelen*, an ``int``, the scope prefix length.  This value
        must be 0 in queries, and should be set in responses.
        """

        super(ECSOption, self).__init__(ECS)
        af = dns.inet.af_for_address(address)

        if af == dns.inet.AF_INET6:
            self.family = 2
            if srclen is None:
                srclen = 56
        elif af == dns.inet.AF_INET:
            self.family = 1
            if srclen is None:
                srclen = 24
        else:
            raise ValueError('Bad ip family')

        self.address = address
        self.srclen = srclen
        self.scopelen = scopelen

        addrdata = dns.inet.inet_pton(af, address)
        nbytes = int(math.ceil(srclen/8.0))

        # Truncate to srclen and pad to the end of the last octet needed
        # See RFC section 6
        self.addrdata = addrdata[:nbytes]
        nbits = srclen % 8
        if nbits != 0:
            last = struct.pack('B', ord(self.addrdata[-1:]) & (0xff << nbits))
            self.addrdata = self.addrdata[:-1] + last

    def to_text(self):
        return "ECS {}/{} scope/{}".format(self.address, self.srclen,
                                           self.scopelen)

    def to_wire(self, file):
        file.write(struct.pack('!H', self.family))
        file.write(struct.pack('!BB', self.srclen, self.scopelen))
        file.write(self.addrdata)

    @classmethod
    def from_wire(cls, otype, wire, cur, olen):
        family, src, scope = struct.unpack('!HBB', wire[cur:cur+4])
        cur += 4

        addrlen = int(math.ceil(src/8.0))

        if family == 1:
            af = dns.inet.AF_INET
            pad = 4 - addrlen
        elif family == 2:
            af = dns.inet.AF_INET6
            pad = 16 - addrlen
        else:
            raise ValueError('unsupported family')

        addr = dns.inet.inet_ntop(af, wire[cur:cur+addrlen] + b'\x00' * pad)
        return cls(addr, src, scope)

    def _cmp(self, other):
        if self.addrdata == other.addrdata:
            return 0
        if self.addrdata > other.addrdata:
            return 1
        return -1

_type_to_class = {
        ECS: ECSOption
}

def get_option_class(otype):
    """Return the class for the specified option type.

    The GenericOption class is used if a more specific class is not
    known.
    """

    cls = _type_to_class.get(otype)
    if cls is None:
        cls = GenericOption
    return cls


def option_from_wire(otype, wire, current, olen):
    """Build an EDNS option object from wire format.

    *otype*, an ``int``, is the option type.

    *wire*, a ``binary``, is the wire-format message.

    *current*, an ``int``, is the offset in *wire* of the beginning
    of the rdata.

    *olen*, an ``int``, is the length of the wire-format option data

    Returns an instance of a subclass of ``dns.edns.Option``.
    """

    cls = get_option_class(otype)
    return cls.from_wire(otype, wire, current, olen)
