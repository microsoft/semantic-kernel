# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2016 Nominum, Inc.
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

import base64

import dns.exception
import dns.rdata
import dns.tokenizer

class OPENPGPKEY(dns.rdata.Rdata):

    """OPENPGPKEY record

    @ivar key: the key
    @type key: bytes
    @see: RFC 7929
    """

    def __init__(self, rdclass, rdtype, key):
        super(OPENPGPKEY, self).__init__(rdclass, rdtype)
        self.key = key

    def to_text(self, origin=None, relativize=True, **kw):
        return dns.rdata._base64ify(self.key)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        chunks = []
        while 1:
            t = tok.get().unescape()
            if t.is_eol_or_eof():
                break
            if not t.is_identifier():
                raise dns.exception.SyntaxError
            chunks.append(t.value.encode())
        b64 = b''.join(chunks)
        key = base64.b64decode(b64)
        return cls(rdclass, rdtype, key)

    def to_wire(self, file, compress=None, origin=None):
        file.write(self.key)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        key = wire[current: current + rdlen].unwrap()
        return cls(rdclass, rdtype, key)
