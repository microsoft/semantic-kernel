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

import dns.exception
import dns.rdata
import dns.tokenizer
from dns._compat import long, text_type


def _validate_float_string(what):
    if what[0] == b'-'[0] or what[0] == b'+'[0]:
        what = what[1:]
    if what.isdigit():
        return
    (left, right) = what.split(b'.')
    if left == b'' and right == b'':
        raise dns.exception.FormError
    if not left == b'' and not left.decode().isdigit():
        raise dns.exception.FormError
    if not right == b'' and not right.decode().isdigit():
        raise dns.exception.FormError


def _sanitize(value):
    if isinstance(value, text_type):
        return value.encode()
    return value


class GPOS(dns.rdata.Rdata):

    """GPOS record

    @ivar latitude: latitude
    @type latitude: string
    @ivar longitude: longitude
    @type longitude: string
    @ivar altitude: altitude
    @type altitude: string
    @see: RFC 1712"""

    __slots__ = ['latitude', 'longitude', 'altitude']

    def __init__(self, rdclass, rdtype, latitude, longitude, altitude):
        super(GPOS, self).__init__(rdclass, rdtype)
        if isinstance(latitude, float) or \
           isinstance(latitude, int) or \
           isinstance(latitude, long):
            latitude = str(latitude)
        if isinstance(longitude, float) or \
           isinstance(longitude, int) or \
           isinstance(longitude, long):
            longitude = str(longitude)
        if isinstance(altitude, float) or \
           isinstance(altitude, int) or \
           isinstance(altitude, long):
            altitude = str(altitude)
        latitude = _sanitize(latitude)
        longitude = _sanitize(longitude)
        altitude = _sanitize(altitude)
        _validate_float_string(latitude)
        _validate_float_string(longitude)
        _validate_float_string(altitude)
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

    def to_text(self, origin=None, relativize=True, **kw):
        return '{} {} {}'.format(self.latitude.decode(),
                             self.longitude.decode(),
                             self.altitude.decode())

    @classmethod
    def from_text(cls, rdclass, rdtype, tok, origin=None, relativize=True):
        latitude = tok.get_string()
        longitude = tok.get_string()
        altitude = tok.get_string()
        tok.get_eol()
        return cls(rdclass, rdtype, latitude, longitude, altitude)

    def to_wire(self, file, compress=None, origin=None):
        l = len(self.latitude)
        assert l < 256
        file.write(struct.pack('!B', l))
        file.write(self.latitude)
        l = len(self.longitude)
        assert l < 256
        file.write(struct.pack('!B', l))
        file.write(self.longitude)
        l = len(self.altitude)
        assert l < 256
        file.write(struct.pack('!B', l))
        file.write(self.altitude)

    @classmethod
    def from_wire(cls, rdclass, rdtype, wire, current, rdlen, origin=None):
        l = wire[current]
        current += 1
        rdlen -= 1
        if l > rdlen:
            raise dns.exception.FormError
        latitude = wire[current: current + l].unwrap()
        current += l
        rdlen -= l
        l = wire[current]
        current += 1
        rdlen -= 1
        if l > rdlen:
            raise dns.exception.FormError
        longitude = wire[current: current + l].unwrap()
        current += l
        rdlen -= l
        l = wire[current]
        current += 1
        rdlen -= 1
        if l != rdlen:
            raise dns.exception.FormError
        altitude = wire[current: current + l].unwrap()
        return cls(rdclass, rdtype, latitude, longitude, altitude)

    def _get_float_latitude(self):
        return float(self.latitude)

    def _set_float_latitude(self, value):
        self.latitude = str(value)

    float_latitude = property(_get_float_latitude, _set_float_latitude,
                              doc="latitude as a floating point value")

    def _get_float_longitude(self):
        return float(self.longitude)

    def _set_float_longitude(self, value):
        self.longitude = str(value)

    float_longitude = property(_get_float_longitude, _set_float_longitude,
                               doc="longitude as a floating point value")

    def _get_float_altitude(self):
        return float(self.altitude)

    def _set_float_altitude(self, value):
        self.altitude = str(value)

    float_altitude = property(_get_float_altitude, _set_float_altitude,
                              doc="altitude as a floating point value")
