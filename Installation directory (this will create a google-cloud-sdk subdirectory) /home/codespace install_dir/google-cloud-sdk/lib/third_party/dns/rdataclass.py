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

"""DNS Rdata Classes."""

import re

import dns.exception

RESERVED0 = 0
IN = 1
CH = 3
HS = 4
NONE = 254
ANY = 255

_by_text = {
    'RESERVED0': RESERVED0,
    'IN': IN,
    'CH': CH,
    'HS': HS,
    'NONE': NONE,
    'ANY': ANY
}

# We construct the inverse mapping programmatically to ensure that we
# cannot make any mistakes (e.g. omissions, cut-and-paste errors) that
# would cause the mapping not to be true inverse.

_by_value = {y: x for x, y in _by_text.items()}

# Now that we've built the inverse map, we can add class aliases to
# the _by_text mapping.

_by_text.update({
    'INTERNET': IN,
    'CHAOS': CH,
    'HESIOD': HS
})

_metaclasses = {
    NONE: True,
    ANY: True
}

_unknown_class_pattern = re.compile('CLASS([0-9]+)$', re.I)


class UnknownRdataclass(dns.exception.DNSException):
    """A DNS class is unknown."""


def from_text(text):
    """Convert text into a DNS rdata class value.

    The input text can be a defined DNS RR class mnemonic or
    instance of the DNS generic class syntax.

    For example, "IN" and "CLASS1" will both result in a value of 1.

    Raises ``dns.rdatatype.UnknownRdataclass`` if the class is unknown.

    Raises ``ValueError`` if the rdata class value is not >= 0 and <= 65535.

    Returns an ``int``.
    """

    value = _by_text.get(text.upper())
    if value is None:
        match = _unknown_class_pattern.match(text)
        if match is None:
            raise UnknownRdataclass
        value = int(match.group(1))
        if value < 0 or value > 65535:
            raise ValueError("class must be between >= 0 and <= 65535")
    return value


def to_text(value):
    """Convert a DNS rdata type value to text.

    If the value has a known mnemonic, it will be used, otherwise the
    DNS generic class syntax will be used.

    Raises ``ValueError`` if the rdata class value is not >= 0 and <= 65535.

    Returns a ``str``.
    """

    if value < 0 or value > 65535:
        raise ValueError("class must be between >= 0 and <= 65535")
    text = _by_value.get(value)
    if text is None:
        text = 'CLASS' + repr(value)
    return text


def is_metaclass(rdclass):
    """True if the specified class is a metaclass.

    The currently defined metaclasses are ANY and NONE.

    *rdclass* is an ``int``.
    """

    if rdclass in _metaclasses:
        return True
    return False
