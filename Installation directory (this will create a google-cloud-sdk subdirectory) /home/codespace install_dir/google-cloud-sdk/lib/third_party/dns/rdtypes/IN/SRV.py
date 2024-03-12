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

import struct

import dns.exception
import dns.rdata
import dns.name


class SRV(dns.rdata.Rdata):

    """SRV record

    @ivar priority: the priority
    @type priority: int
    @ivar weight: the weight
    @type weight: int
    @ivar port: the port of the service
    @type port: int
    @ivar target: the target host
    @type target: dns.name.Name object
    @see: RFC 2782"""

    __slots__ = ['priority', 'weight', 'port', 'target']

    def __init__(self, rdclass, rdtype, priority, weight, port, target):
        super(SRV, self).__init__(rdclass, rdtype)
        self.priority = priority
        self.weight = weight
        self.port = port
        self.target = target

    def to_text(self, origin=None, relativize=True, **kw):
        target = self.target.choose_relativity(origin, relativize)
        return '%d %d %d %s' % (self.priority, self.weight, self.port,
                                target)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        priority = tok.get_uint16()
        weight = tok.get_uint16()
        port = tok.get_uint16()
        target = tok.get_name(None)
        target = target.choose_relativity(origin, relativize)
        tok.get_eol()
        return cls(rdclass, rdtype, priority, weight, port, target)

    def to_wire(self, file, compress=None, origin=None):
        three_ints = struct.pack("!HHH", self.priority, self.weight, self.port)
        file.write(three_ints)
        self.target.to_wire(file, compress, origin)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        (priority, weight, port) = struct.unpack('!HHH',
                                                 wire[current: current + 6])
        current += 6
        rdlen -= 6
        (target, cused) = dns.name.from_wire(wire[: current + rdlen],
                                             current)
        if cused != rdlen:
            raise dns.exception.FormError
        if origin is not None:
            target = target.relativize(origin)
        return cls(rdclass, rdtype, priority, weight, port, target)

    def choose_relativity(self, origin=None, relativize=True):
        self.target = self.target.choose_relativity(origin, relativize)
