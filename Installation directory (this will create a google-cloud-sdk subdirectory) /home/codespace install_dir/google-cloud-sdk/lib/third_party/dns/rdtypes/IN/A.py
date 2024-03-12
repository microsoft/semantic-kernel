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
import dns.ipv4
import dns.rdata
import dns.tokenizer


class A(dns.rdata.Rdata):

    """A record.

    @ivar address: an IPv4 address
    @type address: string (in the standard "dotted quad" format)"""

    __slots__ = ['address']

    def __init__(self, rdclass, rdtype, address):
        super(A, self).__init__(rdclass, rdtype)
        # check that it's OK
        dns.ipv4.inet_aton(address)
        self.address = address

    def to_text(self, origin=None, relativize=True, **kw):
        return self.address

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        address = tok.get_identifier()
        tok.get_eol()
        return cls(rdclass, rdtype, address)

    def to_wire(self, file, compress=None, origin=None):
        file.write(dns.ipv4.inet_aton(self.address))

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        address = dns.ipv4.inet_ntoa(wire[current: current + rdlen])
        return cls(rdclass, rdtype, address)
