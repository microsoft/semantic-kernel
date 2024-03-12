# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2006-2017 Nominum, Inc.
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

"""TXT-like base class."""

import struct

import dns.exception
import dns.rdata
import dns.tokenizer
from dns._compat import binary_type, string_types


class TXTBase(dns.rdata.Rdata):

    """Base class for rdata that is like a TXT record

    @ivar strings: the strings
    @type strings: list of binary
    @see: RFC 1035"""

    __slots__ = ['strings']

    def __init__(self, rdclass, rdtype, strings):
        super(TXTBase, self).__init__(rdclass, rdtype)
        if isinstance(strings, binary_type) or \
           isinstance(strings, string_types):
            strings = [strings]
        self.strings = []
        for string in strings:
            if isinstance(string, string_types):
                string = string.encode()
            self.strings.append(string)

    def to_text(self, origin=None, relativize=True, **kw):
        txt = ''
        prefix = ''
        for s in self.strings:
            txt += '{}"{}"'.format(prefix, dns.rdata._escapify(s))
            prefix = ' '
        return txt

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        strings = []
        while 1:
            token = tok.get().unescape()
            if token.is_eol_or_eof():
                break
            if not (token.is_quoted_string() or token.is_identifier()):
                raise dns.exception.SyntaxError("expected a string")
            if len(token.value) > 255:
                raise dns.exception.SyntaxError("string too long")
            value = token.value
            if isinstance(value, binary_type):
                strings.append(value)
            else:
                strings.append(value.encode())
        if len(strings) == 0:
            raise dns.exception.UnexpectedEnd
        return cls(rdclass, rdtype, strings)

    def to_wire(self, file, compress=None, origin=None):
        for s in self.strings:
            l = len(s)
            assert l < 256
            file.write(struct.pack('!B', l))
            file.write(s)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        strings = []
        while rdlen > 0:
            l = wire[current]
            current += 1
            rdlen -= 1
            if l > rdlen:
                raise dns.exception.FormError
            s = wire[current: current + l].unwrap()
            current += l
            rdlen -= l
            strings.append(s)
        return cls(rdclass, rdtype, strings)
