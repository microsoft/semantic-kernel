# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2003-2007, 2009-2011 Nominum, Inc.
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

import socket
import struct

import dns.ipv4
import dns.rdata
from dns._compat import xrange

_proto_tcp = socket.getprotobyname('tcp')
_proto_udp = socket.getprotobyname('udp')


class WKS(dns.rdata.Rdata):

    """WKS record

    @ivar address: the address
    @type address: string
    @ivar protocol: the protocol
    @type protocol: int
    @ivar bitmap: the bitmap
    @type bitmap: string
    @see: RFC 1035"""

    __slots__ = ['address', 'protocol', 'bitmap']

    def __init__(self, rdclass, rdtype, address, protocol, bitmap):
        super(WKS, self).__init__(rdclass, rdtype)
        self.address = address
        self.protocol = protocol
        if not isinstance(bitmap, bytearray):
            self.bitmap = bytearray(bitmap)
        else:
            self.bitmap = bitmap

    def to_text(self, origin=None, relativize=True, **kw):
        bits = []
        for i in xrange(0, len(self.bitmap)):
            byte = self.bitmap[i]
            for j in xrange(0, 8):
                if byte & (0x80 >> j):
                    bits.append(str(i * 8 + j))
        text = ' '.join(bits)
        return '%s %d %s' % (self.address, self.protocol, text)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        address = tok.get_string()
        protocol = tok.get_string()
        if protocol.isdigit():
            protocol = int(protocol)
        else:
            protocol = socket.getprotobyname(protocol)
        bitmap = bytearray()
        while 1:
            token = tok.get().unescape()
            if token.is_eol_or_eof():
                break
            if token.value.isdigit():
                serv = int(token.value)
            else:
                if protocol != _proto_udp and protocol != _proto_tcp:
                    raise NotImplementedError("protocol must be TCP or UDP")
                if protocol == _proto_udp:
                    protocol_text = "udp"
                else:
                    protocol_text = "tcp"
                serv = socket.getservbyname(token.value, protocol_text)
            i = serv // 8
            l = len(bitmap)
            if l < i + 1:
                for j in xrange(l, i + 1):
                    bitmap.append(0)
            bitmap[i] = bitmap[i] | (0x80 >> (serv % 8))
        bitmap = dns.rdata._truncate_bitmap(bitmap)
        return cls(rdclass, rdtype, address, protocol, bitmap)

    def to_wire(self, file, compress=None, origin=None):
        file.write(dns.ipv4.inet_aton(self.address))
        protocol = struct.pack('!B', self.protocol)
        file.write(protocol)
        file.write(self.bitmap)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        address = dns.ipv4.inet_ntoa(wire[current: current + 4])
        protocol, = struct.unpack('!B', wire[current + 4: current + 5])
        current += 5
        rdlen -= 5
        bitmap = wire[current: current + rdlen].unwrap()
        return cls(rdclass, rdtype, address, protocol, bitmap)
