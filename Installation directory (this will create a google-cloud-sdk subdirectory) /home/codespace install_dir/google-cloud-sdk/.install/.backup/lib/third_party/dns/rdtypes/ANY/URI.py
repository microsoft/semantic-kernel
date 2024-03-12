# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2003-2007, 2009-2011 Nominum, Inc.
# Copyright (C) 2015 Red Hat, Inc.
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
from dns._compat import text_type


class URI(dns.rdata.Rdata):

    """URI record

    @ivar priority: the priority
    @type priority: int
    @ivar weight: the weight
    @type weight: int
    @ivar target: the target host
    @type target: dns.name.Name object
    @see: draft-faltstrom-uri-13"""

    __slots__ = ['priority', 'weight', 'target']

    def __init__(self, rdclass, rdtype, priority, weight, target):
        super(URI, self).__init__(rdclass, rdtype)
        self.priority = priority
        self.weight = weight
        if len(target) < 1:
            raise dns.exception.SyntaxError("URI target cannot be empty")
        if isinstance(target, text_type):
            self.target = target.encode()
        else:
            self.target = target

    def to_text(self, origin=None, relativize=True, **kw):
        return '%d %d "%s"' % (self.priority, self.weight,
                               self.target.decode())

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        priority = tok.get_uint16()
        weight = tok.get_uint16()
        target = tok.get().unescape()
        if not (target.is_quoted_string() or target.is_identifier()):
            raise dns.exception.SyntaxError("URI target must be a string")
        tok.get_eol()
        return cls(rdclass, rdtype, priority, weight, target.value)

    def to_wire(self, file, compress=None, origin=None):
        two_ints = struct.pack("!HH", self.priority, self.weight)
        file.write(two_ints)
        file.write(self.target)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        if rdlen < 5:
            raise dns.exception.FormError('URI RR is shorter than 5 octets')

        (priority, weight) = struct.unpack('!HH', wire[current: current + 4])
        current += 4
        rdlen -= 4
        target = wire[current: current + rdlen]
        current += rdlen

        return cls(rdclass, rdtype, priority, weight, target)
