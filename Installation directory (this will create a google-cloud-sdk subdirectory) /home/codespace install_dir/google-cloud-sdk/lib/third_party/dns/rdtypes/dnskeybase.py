# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2004-2007, 2009-2011 Nominum, Inc.
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
import struct

import dns.exception
import dns.dnssec
import dns.rdata

# wildcard import
__all__ = ["SEP", "REVOKE", "ZONE",
           "flags_to_text_set", "flags_from_text_set"]

# flag constants
SEP = 0x0001
REVOKE = 0x0080
ZONE = 0x0100

_flag_by_text = {
    'SEP': SEP,
    'REVOKE': REVOKE,
    'ZONE': ZONE
}

# We construct the inverse mapping programmatically to ensure that we
# cannot make any mistakes (e.g. omissions, cut-and-paste errors) that
# would cause the mapping not to be true inverse.
_flag_by_value = {y: x for x, y in _flag_by_text.items()}


def flags_to_text_set(flags):
    """Convert a DNSKEY flags value to set texts
    @rtype: set([string])"""

    flags_set = set()
    mask = 0x1
    while mask <= 0x8000:
        if flags & mask:
            text = _flag_by_value.get(mask)
            if not text:
                text = hex(mask)
            flags_set.add(text)
        mask <<= 1
    return flags_set


def flags_from_text_set(texts_set):
    """Convert set of DNSKEY flag mnemonic texts to DNSKEY flag value
    @rtype: int"""

    flags = 0
    for text in texts_set:
        try:
            flags += _flag_by_text[text]
        except KeyError:
            raise NotImplementedError(
                "DNSKEY flag '%s' is not supported" % text)
    return flags


class DNSKEYBase(dns.rdata.Rdata):

    """Base class for rdata that is like a DNSKEY record

    @ivar flags: the key flags
    @type flags: int
    @ivar protocol: the protocol for which this key may be used
    @type protocol: int
    @ivar algorithm: the algorithm used for the key
    @type algorithm: int
    @ivar key: the public key
    @type key: string"""

    __slots__ = ['flags', 'protocol', 'algorithm', 'key']

    def __init__(self, rdclass, rdtype, flags, protocol, algorithm, key):
        super(DNSKEYBase, self).__init__(rdclass, rdtype)
        self.flags = flags
        self.protocol = protocol
        self.algorithm = algorithm
        self.key = key

    def to_text(self, origin=None, relativize=True, **kw):
        return '%d %d %d %s' % (self.flags, self.protocol, self.algorithm,
                                dns.rdata._base64ify(self.key))

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        flags = tok.get_uint16()
        protocol = tok.get_uint8()
        algorithm = dns.dnssec.algorithm_from_text(tok.get_string())
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
        return cls(rdclass, rdtype, flags, protocol, algorithm, key)

    def to_wire(self, file, compress=None, origin=None):
        header = struct.pack("!HBB", self.flags, self.protocol, self.algorithm)
        file.write(header)
        file.write(self.key)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        if rdlen < 4:
            raise dns.exception.FormError
        header = struct.unpack('!HBB', wire[current: current + 4])
        current += 4
        rdlen -= 4
        key = wire[current: current + rdlen].unwrap()
        return cls(rdclass, rdtype, header[0], header[1], header[2],
                   key)

    def flags_to_text_set(self):
        """Convert a DNSKEY flags value to set texts
        @rtype: set([string])"""
        return flags_to_text_set(self.flags)
