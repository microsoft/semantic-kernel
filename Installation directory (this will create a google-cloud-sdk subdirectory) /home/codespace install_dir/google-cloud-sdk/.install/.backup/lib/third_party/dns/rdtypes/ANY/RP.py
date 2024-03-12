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

import dns.exception
import dns.rdata
import dns.name


class RP(dns.rdata.Rdata):

    """RP record

    @ivar mbox: The responsible person's mailbox
    @type mbox: dns.name.Name object
    @ivar txt: The owner name of a node with TXT records, or the root name
    if no TXT records are associated with this RP.
    @type txt: dns.name.Name object
    @see: RFC 1183"""

    __slots__ = ['mbox', 'txt']

    def __init__(self, rdclass, rdtype, mbox, txt):
        super(RP, self).__init__(rdclass, rdtype)
        self.mbox = mbox
        self.txt = txt

    def to_text(self, origin=None, relativize=True, **kw):
        mbox = self.mbox.choose_relativity(origin, relativize)
        txt = self.txt.choose_relativity(origin, relativize)
        return "{} {}".format(str(mbox), str(txt))

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        mbox = tok.get_name()
        txt = tok.get_name()
        mbox = mbox.choose_relativity(origin, relativize)
        txt = txt.choose_relativity(origin, relativize)
        tok.get_eol()
        return cls(rdclass, rdtype, mbox, txt)

    def to_wire(self, file, compress=None, origin=None):
        self.mbox.to_wire(file, None, origin)
        self.txt.to_wire(file, None, origin)

    def to_digestable(self, origin=None):
        return self.mbox.to_digestable(origin) + \
            self.txt.to_digestable(origin)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        (mbox, cused) = dns.name.from_wire(wire[: current + rdlen],
                                           current)
        current += cused
        rdlen -= cused
        if rdlen <= 0:
            raise dns.exception.FormError
        (txt, cused) = dns.name.from_wire(wire[: current + rdlen],
                                          current)
        if cused != rdlen:
            raise dns.exception.FormError
        if origin is not None:
            mbox = mbox.relativize(origin)
            txt = txt.relativize(origin)
        return cls(rdclass, rdtype, mbox, txt)

    def choose_relativity(self, origin=None, relativize=True):
        self.mbox = self.mbox.choose_relativity(origin, relativize)
        self.txt = self.txt.choose_relativity(origin, relativize)
