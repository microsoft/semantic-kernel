# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2001-2017 Nominum, Inc.
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

"""DNS Rdata Types."""

import re

import dns.exception

NONE = 0
A = 1
NS = 2
MD = 3
MF = 4
CNAME = 5
SOA = 6
MB = 7
MG = 8
MR = 9
NULL = 10
WKS = 11
PTR = 12
HINFO = 13
MINFO = 14
MX = 15
TXT = 16
RP = 17
AFSDB = 18
X25 = 19
ISDN = 20
RT = 21
NSAP = 22
NSAP_PTR = 23
SIG = 24
KEY = 25
PX = 26
GPOS = 27
AAAA = 28
LOC = 29
NXT = 30
SRV = 33
NAPTR = 35
KX = 36
CERT = 37
A6 = 38
DNAME = 39
OPT = 41
APL = 42
DS = 43
SSHFP = 44
IPSECKEY = 45
RRSIG = 46
NSEC = 47
DNSKEY = 48
DHCID = 49
NSEC3 = 50
NSEC3PARAM = 51
TLSA = 52
HIP = 55
CDS = 59
CDNSKEY = 60
OPENPGPKEY = 61
CSYNC = 62
SPF = 99
UNSPEC = 103
EUI48 = 108
EUI64 = 109
TKEY = 249
TSIG = 250
IXFR = 251
AXFR = 252
MAILB = 253
MAILA = 254
ANY = 255
URI = 256
CAA = 257
AVC = 258
TA = 32768
DLV = 32769

_by_text = {
    'NONE': NONE,
    'A': A,
    'NS': NS,
    'MD': MD,
    'MF': MF,
    'CNAME': CNAME,
    'SOA': SOA,
    'MB': MB,
    'MG': MG,
    'MR': MR,
    'NULL': NULL,
    'WKS': WKS,
    'PTR': PTR,
    'HINFO': HINFO,
    'MINFO': MINFO,
    'MX': MX,
    'TXT': TXT,
    'RP': RP,
    'AFSDB': AFSDB,
    'X25': X25,
    'ISDN': ISDN,
    'RT': RT,
    'NSAP': NSAP,
    'NSAP-PTR': NSAP_PTR,
    'SIG': SIG,
    'KEY': KEY,
    'PX': PX,
    'GPOS': GPOS,
    'AAAA': AAAA,
    'LOC': LOC,
    'NXT': NXT,
    'SRV': SRV,
    'NAPTR': NAPTR,
    'KX': KX,
    'CERT': CERT,
    'A6': A6,
    'DNAME': DNAME,
    'OPT': OPT,
    'APL': APL,
    'DS': DS,
    'SSHFP': SSHFP,
    'IPSECKEY': IPSECKEY,
    'RRSIG': RRSIG,
    'NSEC': NSEC,
    'DNSKEY': DNSKEY,
    'DHCID': DHCID,
    'NSEC3': NSEC3,
    'NSEC3PARAM': NSEC3PARAM,
    'TLSA': TLSA,
    'HIP': HIP,
    'CDS': CDS,
    'CDNSKEY': CDNSKEY,
    'OPENPGPKEY': OPENPGPKEY,
    'CSYNC': CSYNC,
    'SPF': SPF,
    'UNSPEC': UNSPEC,
    'EUI48': EUI48,
    'EUI64': EUI64,
    'TKEY': TKEY,
    'TSIG': TSIG,
    'IXFR': IXFR,
    'AXFR': AXFR,
    'MAILB': MAILB,
    'MAILA': MAILA,
    'ANY': ANY,
    'URI': URI,
    'CAA': CAA,
    'AVC': AVC,
    'TA': TA,
    'DLV': DLV,
}

# We construct the inverse mapping programmatically to ensure that we
# cannot make any mistakes (e.g. omissions, cut-and-paste errors) that
# would cause the mapping not to be true inverse.

_by_value = {y: x for x, y in _by_text.items()}

_metatypes = {
    OPT: True
}

_singletons = {
    SOA: True,
    NXT: True,
    DNAME: True,
    NSEC: True,
    CNAME: True,
}

_unknown_type_pattern = re.compile('TYPE([0-9]+)$', re.I)


class UnknownRdatatype(dns.exception.DNSException):
    """DNS resource record type is unknown."""


def from_text(text):
    """Convert text into a DNS rdata type value.

    The input text can be a defined DNS RR type mnemonic or
    instance of the DNS generic type syntax.

    For example, "NS" and "TYPE2" will both result in a value of 2.

    Raises ``dns.rdatatype.UnknownRdatatype`` if the type is unknown.

    Raises ``ValueError`` if the rdata type value is not >= 0 and <= 65535.

    Returns an ``int``.
    """

    value = _by_text.get(text.upper())
    if value is None:
        match = _unknown_type_pattern.match(text)
        if match is None:
            raise UnknownRdatatype
        value = int(match.group(1))
        if value < 0 or value > 65535:
            raise ValueError("type must be between >= 0 and <= 65535")
    return value


def to_text(value):
    """Convert a DNS rdata type value to text.

    If the value has a known mnemonic, it will be used, otherwise the
    DNS generic type syntax will be used.

    Raises ``ValueError`` if the rdata type value is not >= 0 and <= 65535.

    Returns a ``str``.
    """

    if value < 0 or value > 65535:
        raise ValueError("type must be between >= 0 and <= 65535")
    text = _by_value.get(value)
    if text is None:
        text = 'TYPE' + repr(value)
    return text


def is_metatype(rdtype):
    """True if the specified type is a metatype.

    *rdtype* is an ``int``.

    The currently defined metatypes are TKEY, TSIG, IXFR, AXFR, MAILA,
    MAILB, ANY, and OPT.

    Returns a ``bool``.
    """

    if rdtype >= TKEY and rdtype <= ANY or rdtype in _metatypes:
        return True
    return False


def is_singleton(rdtype):
    """Is the specified type a singleton type?

    Singleton types can only have a single rdata in an rdataset, or a single
    RR in an RRset.

    The currently defined singleton types are CNAME, DNAME, NSEC, NXT, and
    SOA.

    *rdtype* is an ``int``.

    Returns a ``bool``.
    """

    if rdtype in _singletons:
        return True
    return False


def register_type(rdtype, rdtype_text, is_singleton=False):  # pylint: disable=redefined-outer-name
    """Dynamically register an rdatatype.

    *rdtype*, an ``int``, the rdatatype to register.

    *rdtype_text*, a ``text``, the textual form of the rdatatype.

    *is_singleton*, a ``bool``, indicating if the type is a singleton (i.e.
    RRsets of the type can have only one member.)
    """

    _by_text[rdtype_text] = rdtype
    _by_value[rdtype] = rdtype_text
    if is_singleton:
        _singletons[rdtype] = True
