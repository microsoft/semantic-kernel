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

"""DNS Opcodes."""

import dns.exception

#: Query
QUERY = 0
#: Inverse Query (historical)
IQUERY = 1
#: Server Status (unspecified and unimplemented anywhere)
STATUS = 2
#: Notify
NOTIFY = 4
#: Dynamic Update
UPDATE = 5

_by_text = {
    'QUERY': QUERY,
    'IQUERY': IQUERY,
    'STATUS': STATUS,
    'NOTIFY': NOTIFY,
    'UPDATE': UPDATE
}

# We construct the inverse mapping programmatically to ensure that we
# cannot make any mistakes (e.g. omissions, cut-and-paste errors) that
# would cause the mapping not to be true inverse.

_by_value = {y: x for x, y in _by_text.items()}


class UnknownOpcode(dns.exception.DNSException):
    """An DNS opcode is unknown."""


def from_text(text):
    """Convert text into an opcode.

    *text*, a ``text``, the textual opcode

    Raises ``dns.opcode.UnknownOpcode`` if the opcode is unknown.

    Returns an ``int``.
    """

    if text.isdigit():
        value = int(text)
        if value >= 0 and value <= 15:
            return value
    value = _by_text.get(text.upper())
    if value is None:
        raise UnknownOpcode
    return value


def from_flags(flags):
    """Extract an opcode from DNS message flags.

    *flags*, an ``int``, the DNS flags.

    Returns an ``int``.
    """

    return (flags & 0x7800) >> 11


def to_flags(value):
    """Convert an opcode to a value suitable for ORing into DNS message
    flags.

    *value*, an ``int``, the DNS opcode value.

    Returns an ``int``.
    """

    return (value << 11) & 0x7800


def to_text(value):
    """Convert an opcode to text.

    *value*, an ``int`` the opcode value,

    Raises ``dns.opcode.UnknownOpcode`` if the opcode is unknown.

    Returns a ``text``.
    """

    text = _by_value.get(value)
    if text is None:
        text = str(value)
    return text


def is_update(flags):
    """Is the opcode in flags UPDATE?

    *flags*, an ``int``, the DNS message flags.

    Returns a ``bool``.
    """

    return from_flags(flags) == UPDATE
