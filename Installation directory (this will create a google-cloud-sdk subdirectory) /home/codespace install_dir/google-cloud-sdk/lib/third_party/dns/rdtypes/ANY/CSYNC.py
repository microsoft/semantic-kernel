# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2004-2007, 2009-2011, 2016 Nominum, Inc.
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
import dns.rdatatype
import dns.name
from dns._compat import xrange

class CSYNC(dns.rdata.Rdata):

    """CSYNC record

    @ivar serial: the SOA serial number
    @type serial: int
    @ivar flags: the CSYNC flags
    @type flags: int
    @ivar windows: the windowed bitmap list
    @type windows: list of (window number, string) tuples"""

    __slots__ = ['serial', 'flags', 'windows']

    def __init__(self, rdclass, rdtype, serial, flags, windows):
        super(CSYNC, self).__init__(rdclass, rdtype)
        self.serial = serial
        self.flags = flags
        self.windows = windows

    def to_text(self, origin=None, relativize=True, **kw):
        text = ''
        for (window, bitmap) in self.windows:
            bits = []
            for i in xrange(0, len(bitmap)):
                byte = bitmap[i]
                for j in xrange(0, 8):
                    if byte & (0x80 >> j):
                        bits.append(dns.rdatatype.to_text(window * 256 +
                                                          i * 8 + j))
            text += (' ' + ' '.join(bits))
        return '%d %d%s' % (self.serial, self.flags, text)

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        serial = tok.get_uint32()
        flags = tok.get_uint16()
        rdtypes = []
        while 1:
            token = tok.get().unescape()
            if token.is_eol_or_eof():
                break
            nrdtype = dns.rdatatype.from_text(token.value)
            if nrdtype == 0:
                raise dns.exception.SyntaxError("CSYNC with bit 0")
            if nrdtype > 65535:
                raise dns.exception.SyntaxError("CSYNC with bit > 65535")
            rdtypes.append(nrdtype)
        rdtypes.sort()
        window = 0
        octets = 0
        prior_rdtype = 0
        bitmap = bytearray(b'\0' * 32)
        windows = []
        for nrdtype in rdtypes:
            if nrdtype == prior_rdtype:
                continue
            prior_rdtype = nrdtype
            new_window = nrdtype // 256
            if new_window != window:
                windows.append((window, bitmap[0:octets]))
                bitmap = bytearray(b'\0' * 32)
                window = new_window
            offset = nrdtype % 256
            byte = offset // 8
            bit = offset % 8
            octets = byte + 1
            bitmap[byte] = bitmap[byte] | (0x80 >> bit)

        windows.append((window, bitmap[0:octets]))
        return cls(rdclass, rdtype, serial, flags, windows)

    def to_wire(self, file, compress=None, origin=None):
        file.write(struct.pack('!IH', self.serial, self.flags))
        for (window, bitmap) in self.windows:
            file.write(struct.pack('!BB', window, len(bitmap)))
            file.write(bitmap)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        if rdlen < 6:
            raise dns.exception.FormError("CSYNC too short")
        (serial, flags) = struct.unpack("!IH", wire[current: current + 6])
        current += 6
        rdlen -= 6
        windows = []
        while rdlen > 0:
            if rdlen < 3:
                raise dns.exception.FormError("CSYNC too short")
            window = wire[current]
            octets = wire[current + 1]
            if octets == 0 or octets > 32:
                raise dns.exception.FormError("bad CSYNC octets")
            current += 2
            rdlen -= 2
            if rdlen < octets:
                raise dns.exception.FormError("bad CSYNC bitmap length")
            bitmap = bytearray(wire[current: current + octets].unwrap())
            current += octets
            rdlen -= octets
            windows.append((window, bitmap))
        return cls(rdclass, rdtype, serial, flags, windows)
