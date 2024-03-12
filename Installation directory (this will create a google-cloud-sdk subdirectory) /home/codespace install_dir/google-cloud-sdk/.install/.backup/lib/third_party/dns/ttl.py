# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2003-2017 Nominum, Inc.
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

"""DNS TTL conversion."""

import dns.exception
from ._compat import long


class BadTTL(dns.exception.SyntaxError):
    """DNS TTL value is not well-formed."""


def from_text(text):
    """Convert the text form of a TTL to an integer.

    The BIND 8 units syntax for TTLs (e.g. '1w6d4h3m10s') is supported.

    *text*, a ``text``, the textual TTL.

    Raises ``dns.ttl.BadTTL`` if the TTL is not well-formed.

    Returns an ``int``.
    """

    if text.isdigit():
        total = long(text)
    else:
        if not text[0].isdigit():
            raise BadTTL
        total = long(0)
        current = long(0)
        for c in text:
            if c.isdigit():
                current *= 10
                current += long(c)
            else:
                c = c.lower()
                if c == 'w':
                    total += current * long(604800)
                elif c == 'd':
                    total += current * long(86400)
                elif c == 'h':
                    total += current * long(3600)
                elif c == 'm':
                    total += current * long(60)
                elif c == 's':
                    total += current
                else:
                    raise BadTTL("unknown unit '%s'" % c)
                current = 0
        if not current == 0:
            raise BadTTL("trailing integer")
    if total < long(0) or total > long(2147483647):
        raise BadTTL("TTL should be between 0 and 2^31 - 1 (inclusive)")
    return total
