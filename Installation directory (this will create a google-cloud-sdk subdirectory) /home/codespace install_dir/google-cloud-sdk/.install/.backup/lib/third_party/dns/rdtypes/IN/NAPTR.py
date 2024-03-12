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
import dns.name
import dns.rdata
from dns._compat import xrange, text_type


def _write_string(file, s):
    l = len(s)
    assert l < 256
    file.write(struct.pack('!B', l))
    file.write(s)


def _sanitize(value):
    if isinstance(value, text_type):
        return value.encode()
    return value


class NAPTR(dns.rdata.Rdata):

    """NAPTR record

    @ivar order: order
    @type order: int
    @ivar preference: preference
    @type preference: int
    @ivar flags: flags
    @type flags: string
    @ivar service: service
    @type service: string
    @ivar regexp: regular expression
    @type regexp: string
    @ivar replacement: replacement name
    @type replacement: dns.name.Name object
    @see: RFC 3403"""

    __slots__ = ['order', 'preference', 'flags', 'service', 'regexp',
                 'replacement']

    def __init__(self, rdclass, rdtype, order, preference, flags, service,
                 regexp, replacement):
        super(NAPTR, self).__init__(rdclass, rdtype)
        self.flags = _sanitize(flags)
        self.service = _sanitize(service)
        self.regexp = _sanitize(regexp)
        self.order = order
        self.preference = preference
        self.replacement = replacement

    def to_text(self, origin=None, relativize=True, **kw):
        replacement = self.replacement.choose_relativity(origin, relativize)
        return '%d %d "%s" "%s" "%s" %s' % \
               (self.order, self.preference,
                dns.rdata._escapify(self.flags),
                dns.rdata._escapify(self.service),
                dns.rdata._escapify(self.regexp),
                replacement)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        order = tok.get_uint16()
        preference = tok.get_uint16()
        flags = tok.get_string()
        service = tok.get_string()
        regexp = tok.get_string()
        replacement = tok.get_name()
        replacement = replacement.choose_relativity(origin, relativize)
        tok.get_eol()
        return cls(rdclass, rdtype, order, preference, flags, service,
                   regexp, replacement)

    def to_wire(self, file, compress=None, origin=None):
        two_ints = struct.pack("!HH", self.order, self.preference)
        file.write(two_ints)
        _write_string(file, self.flags)
        _write_string(file, self.service)
        _write_string(file, self.regexp)
        self.replacement.to_wire(file, compress, origin)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        (order, preference) = struct.unpack('!HH', wire[current: current + 4])
        current += 4
        rdlen -= 4
        strings = []
        for i in xrange(3):
            l = wire[current]
            current += 1
            rdlen -= 1
            if l > rdlen or rdlen < 0:
                raise dns.exception.FormError
            s = wire[current: current + l].unwrap()
            current += l
            rdlen -= l
            strings.append(s)
        (replacement, cused) = dns.name.from_wire(wire[: current + rdlen],
                                                  current)
        if cused != rdlen:
            raise dns.exception.FormError
        if origin is not None:
            replacement = replacement.relativize(origin)
        return cls(rdclass, rdtype, order, preference, strings[0], strings[1],
                   strings[2], replacement)

    def choose_relativity(self, origin=None, relativize=True):
        self.replacement = self.replacement.choose_relativity(origin,
                                                              relativize)
