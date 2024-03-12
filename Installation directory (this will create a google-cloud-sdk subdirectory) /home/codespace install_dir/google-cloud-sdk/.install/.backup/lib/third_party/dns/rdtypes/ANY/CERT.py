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
import base64

import dns.exception
import dns.dnssec
import dns.rdata
import dns.tokenizer

_ctype_by_value = {
    1: 'PKIX',
    2: 'SPKI',
    3: 'PGP',
    253: 'URI',
    254: 'OID',
}

_ctype_by_name = {
    'PKIX': 1,
    'SPKI': 2,
    'PGP': 3,
    'URI': 253,
    'OID': 254,
}


def _ctype_from_text(what):
    v = _ctype_by_name.get(what)
    if v is not None:
        return v
    return int(what)


def _ctype_to_text(what):
    v = _ctype_by_value.get(what)
    if v is not None:
        return v
    return str(what)


class CERT(dns.rdata.Rdata):

    """CERT record

    @ivar certificate_type: certificate type
    @type certificate_type: int
    @ivar key_tag: key tag
    @type key_tag: int
    @ivar algorithm: algorithm
    @type algorithm: int
    @ivar certificate: the certificate or CRL
    @type certificate: string
    @see: RFC 2538"""

    __slots__ = ['certificate_type', 'key_tag', 'algorithm', 'certificate']

    def __init__(self, rdclass, rdtype, certificate_type, key_tag, algorithm,
                 certificate):
        super(CERT, self).__init__(rdclass, rdtype)
        self.certificate_type = certificate_type
        self.key_tag = key_tag
        self.algorithm = algorithm
        self.certificate = certificate

    def to_text(self, origin=None, relativize=True, **kw):
        certificate_type = _ctype_to_text(self.certificate_type)
        return "%s %d %s %s" % (certificate_type, self.key_tag,
                                dns.dnssec.algorithm_to_text(self.algorithm),
                                dns.rdata._base64ify(self.certificate))

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        certificate_type = _ctype_from_text(tok.get_string())
        key_tag = tok.get_uint16()
        algorithm = dns.dnssec.algorithm_from_text(tok.get_string())
        if algorithm < 0 or algorithm > 255:
            raise dns.exception.SyntaxError("bad algorithm type")
        chunks = []
        while 1:
            t = tok.get().unescape()
            if t.is_eol_or_eof():
                break
            if not t.is_identifier():
                raise dns.exception.SyntaxError
            chunks.append(t.value.encode())
        b64 = b''.join(chunks)
        certificate = base64.b64decode(b64)
        return cls(rdclass, rdtype, certificate_type, key_tag,
                   algorithm, certificate)

    def to_wire(self, file, compress=None, origin=None):
        prefix = struct.pack("!HHB", self.certificate_type, self.key_tag,
                             self.algorithm)
        file.write(prefix)
        file.write(self.certificate)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        prefix = wire[current: current + 5].unwrap()
        current += 5
        rdlen -= 5
        if rdlen < 0:
            raise dns.exception.FormError
        (certificate_type, key_tag, algorithm) = struct.unpack("!HHB", prefix)
        certificate = wire[current: current + rdlen].unwrap()
        return cls(rdclass, rdtype, certificate_type, key_tag, algorithm,
                   certificate)
