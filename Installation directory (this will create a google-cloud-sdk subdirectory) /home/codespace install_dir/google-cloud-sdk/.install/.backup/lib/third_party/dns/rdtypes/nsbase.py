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

"""NS-like base classes."""

from io import BytesIO

import dns.exception
import dns.rdata
import dns.name


class NSBase(dns.rdata.Rdata):

    """Base class for rdata that is like an NS record.

    @ivar target: the target name of the rdata
    @type target: dns.name.Name object"""

    __slots__ = ['target']

    def __init__(self, rdclass, rdtype, target):
        super(NSBase, self).__init__(rdclass, rdtype)
        self.target = target

    def to_text(self, origin=None, relativize=True, **kw):
        target = self.target.choose_relativity(origin, relativize)
        return str(target)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        target = tok.get_name()
        target = target.choose_relativity(origin, relativize)
        tok.get_eol()
        return cls(rdclass, rdtype, target)

    def to_wire(self, file, compress=None, origin=None):
        self.target.to_wire(file, compress, origin)

    def to_digestable(self, origin=None):
        return self.target.to_digestable(origin)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        (target, cused) = dns.name.from_wire(wire[: current + rdlen],
                                             current)
        if cused != rdlen:
            raise dns.exception.FormError
        if origin is not None:
            target = target.relativize(origin)
        return cls(rdclass, rdtype, target)

    def choose_relativity(self, origin=None, relativize=True):
        self.target = self.target.choose_relativity(origin, relativize)


class UncompressedNS(NSBase):

    """Base class for rdata that is like an NS record, but whose name
    is not compressed when convert to DNS wire format, and whose
    digestable form is not downcased."""

    def to_wire(self, file, compress=None, origin=None):
        super(UncompressedNS, self).to_wire(file, None, origin)

    def to_digestable(self, origin=None):
        f = BytesIO()
        self.to_wire(f, None, origin)
        return f.getvalue()
