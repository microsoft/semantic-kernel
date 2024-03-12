# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2005-2007, 2009-2011 Nominum, Inc.
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
import binascii

import dns.rdata
import dns.rdatatype


class SSHFP(dns.rdata.Rdata):

    """SSHFP record

    @ivar algorithm: the algorithm
    @type algorithm: int
    @ivar fp_type: the digest type
    @type fp_type: int
    @ivar fingerprint: the fingerprint
    @type fingerprint: string
    @see: draft-ietf-secsh-dns-05.txt"""

    __slots__ = ['algorithm', 'fp_type', 'fingerprint']

    def __init__(self, rdclass, rdtype, algorithm, fp_type,
                 fingerprint):
        super(SSHFP, self).__init__(rdclass, rdtype)
        self.algorithm = algorithm
        self.fp_type = fp_type
        self.fingerprint = fingerprint

    def to_text(self, origin=None, relativize=True, **kw):
        return '%d %d %s' % (self.algorithm,
                             self.fp_type,
                             dns.rdata._hexify(self.fingerprint,
                                               chunksize=128))

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        algorithm = tok.get_uint8()
        fp_type = tok.get_uint8()
        chunks = []
        while 1:
            t = tok.get().unescape()
            if t.is_eol_or_eof():
                break
            if not t.is_identifier():
                raise dns.exception.SyntaxError
            chunks.append(t.value.encode())
        fingerprint = b''.join(chunks)
        fingerprint = binascii.unhexlify(fingerprint)
        return cls(rdclass, rdtype, algorithm, fp_type, fingerprint)

    def to_wire(self, file, compress=None, origin=None):
        header = struct.pack("!BB", self.algorithm, self.fp_type)
        file.write(header)
        file.write(self.fingerprint)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        header = struct.unpack("!BB", wire[current: current + 2])
        current += 2
        rdlen -= 2
        fingerprint = wire[current: current + rdlen].unwrap()
        return cls(rdclass, rdtype, header[0], header[1], fingerprint)
