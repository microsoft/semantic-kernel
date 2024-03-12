# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2010, 2011 Nominum, Inc.
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
import binascii

import dns.exception
import dns.rdata
import dns.rdatatype


class HIP(dns.rdata.Rdata):

    """HIP record

    @ivar hit: the host identity tag
    @type hit: string
    @ivar algorithm: the public key cryptographic algorithm
    @type algorithm: int
    @ivar key: the public key
    @type key: string
    @ivar servers: the rendezvous servers
    @type servers: list of dns.name.Name objects
    @see: RFC 5205"""

    __slots__ = ['hit', 'algorithm', 'key', 'servers']

    def __init__(self, rdclass, rdtype, hit, algorithm, key, servers):
        super(HIP, self).__init__(rdclass, rdtype)
        self.hit = hit
        self.algorithm = algorithm
        self.key = key
        self.servers = servers

    def to_text(self, origin=None, relativize=True, **kw):
        hit = binascii.hexlify(self.hit).decode()
        key = base64.b64encode(self.key).replace(b'\n', b'').decode()
        text = u''
        servers = []
        for server in self.servers:
            servers.append(server.choose_relativity(origin, relativize))
        if len(servers) > 0:
            text += (u' ' + u' '.join((x.to_unicode() for x in servers)))
        return u'%u %s %s%s' % (self.algorithm, hit, key, text)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        algorithm = tok.get_uint8()
        hit = binascii.unhexlify(tok.get_string().encode())
        if len(hit) > 255:
            raise dns.exception.SyntaxError("HIT too long")
        key = base64.b64decode(tok.get_string().encode())
        servers = []
        while 1:
            token = tok.get()
            if token.is_eol_or_eof():
                break
            server = dns.name.from_text(token.value, origin)
            server.choose_relativity(origin, relativize)
            servers.append(server)
        return cls(rdclass, rdtype, hit, algorithm, key, servers)

    def to_wire(self, file, compress=None, origin=None):
        lh = len(self.hit)
        lk = len(self.key)
        file.write(struct.pack("!BBH", lh, self.algorithm, lk))
        file.write(self.hit)
        file.write(self.key)
        for server in self.servers:
            server.to_wire(file, None, origin)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        (lh, algorithm, lk) = struct.unpack('!BBH',
                                            wire[current: current + 4])
        current += 4
        rdlen -= 4
        hit = wire[current: current + lh].unwrap()
        current += lh
        rdlen -= lh
        key = wire[current: current + lk].unwrap()
        current += lk
        rdlen -= lk
        servers = []
        while rdlen > 0:
            (server, cused) = dns.name.from_wire(wire[: current + rdlen],
                                                 current)
            current += cused
            rdlen -= cused
            if origin is not None:
                server = server.relativize(origin)
            servers.append(server)
        return cls(rdclass, rdtype, hit, algorithm, key, servers)

    def choose_relativity(self, origin=None, relativize=True):
        servers = []
        for server in self.servers:
            server = server.choose_relativity(origin, relativize)
            servers.append(server)
        self.servers = servers
