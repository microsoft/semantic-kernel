# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2003-2017 Nominum, Inc.
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

import binascii
import codecs
import struct

import dns.exception
import dns.inet
import dns.rdata
import dns.tokenizer
from dns._compat import xrange, maybe_chr


class APLItem(object):

    """An APL list item.

    @ivar family: the address family (IANA address family registry)
    @type family: int
    @ivar negation: is this item negated?
    @type negation: bool
    @ivar address: the address
    @type address: string
    @ivar prefix: the prefix length
    @type prefix: int
    """

    __slots__ = ['family', 'negation', 'address', 'prefix']

    def __init__(self, family, negation, address, prefix):
        self.family = family
        self.negation = negation
        self.address = address
        self.prefix = prefix

    def __str__(self):
        if self.negation:
            return "!%d:%s/%s" % (self.family, self.address, self.prefix)
        else:
            return "%d:%s/%s" % (self.family, self.address, self.prefix)

    def to_wire(self, file):
        if self.family == 1:
            address = dns.inet.inet_pton(dns.inet.AF_INET, self.address)
        elif self.family == 2:
            address = dns.inet.inet_pton(dns.inet.AF_INET6, self.address)
        else:
            address = binascii.unhexlify(self.address)
        #
        # Truncate least significant zero bytes.
        #
        last = 0
        for i in xrange(len(address) - 1, -1, -1):
            if address[i] != maybe_chr(0):
                last = i + 1
                break
        address = address[0: last]
        l = len(address)
        assert l < 128
        if self.negation:
            l |= 0x80
        header = struct.pack('!HBB', self.family, self.prefix, l)
        file.write(header)
        file.write(address)


class APL(dns.rdata.Rdata):

    """APL record.

    @ivar items: a list of APL items
    @type items: list of APL_Item
    @see: RFC 3123"""

    __slots__ = ['items']

    def __init__(self, rdclass, rdtype, items):
        super(APL, self).__init__(rdclass, rdtype)
        self.items = items

    def to_text(self, origin=None, relativize=True, **kw):
        return ' '.join(map(str, self.items))

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        items = []
        while 1:
            token = tok.get().unescape()
            if token.is_eol_or_eof():
                break
            item = token.value
            if item[0] == '!':
                negation = True
                item = item[1:]
            else:
                negation = False
            (family, rest) = item.split(':', 1)
            family = int(family)
            (address, prefix) = rest.split('/', 1)
            prefix = int(prefix)
            item = APLItem(family, negation, address, prefix)
            items.append(item)

        return cls(rdclass, rdtype, items)

    def to_wire(self, file, compress=None, origin=None):
        for item in self.items:
            item.to_wire(file)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):

        items = []
        while 1:
            if rdlen == 0:
                break
            if rdlen < 4:
                raise dns.exception.FormError
            header = struct.unpack('!HBB', wire[current: current + 4])
            afdlen = header[2]
            if afdlen > 127:
                negation = True
                afdlen -= 128
            else:
                negation = False
            current += 4
            rdlen -= 4
            if rdlen < afdlen:
                raise dns.exception.FormError
            address = wire[current: current + afdlen].unwrap()
            l = len(address)
            if header[0] == 1:
                if l < 4:
                    address += b'\x00' * (4 - l)
                address = dns.inet.inet_ntop(dns.inet.AF_INET, address)
            elif header[0] == 2:
                if l < 16:
                    address += b'\x00' * (16 - l)
                address = dns.inet.inet_ntop(dns.inet.AF_INET6, address)
            else:
                #
                # This isn't really right according to the RFC, but it
                # seems better than throwing an exception
                #
                address = codecs.encode(address, 'hex_codec')
            current += afdlen
            rdlen -= afdlen
            item = APLItem(header[0], negation, address, header[1])
            items.append(item)
        return cls(rdclass, rdtype, items)
