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

"""Generic Internet address helper functions."""

import socket

import dns.ipv4
import dns.ipv6

from ._compat import maybe_ord

# We assume that AF_INET is always defined.

AF_INET = socket.AF_INET

# AF_INET6 might not be defined in the socket module, but we need it.
# We'll try to use the socket module's value, and if it doesn't work,
# we'll use our own value.

try:
    AF_INET6 = socket.AF_INET6
except AttributeError:
    AF_INET6 = 9999


def inet_pton(family, text):
    """Convert the textual form of a network address into its binary form.

    *family* is an ``int``, the address family.

    *text* is a ``text``, the textual address.

    Raises ``NotImplementedError`` if the address family specified is not
    implemented.

    Returns a ``binary``.
    """

    if family == AF_INET:
        return dns.ipv4.inet_aton(text)
    elif family == AF_INET6:
        return dns.ipv6.inet_aton(text)
    else:
        raise NotImplementedError


def inet_ntop(family, address):
    """Convert the binary form of a network address into its textual form.

    *family* is an ``int``, the address family.

    *address* is a ``binary``, the network address in binary form.

    Raises ``NotImplementedError`` if the address family specified is not
    implemented.

    Returns a ``text``.
    """

    if family == AF_INET:
        return dns.ipv4.inet_ntoa(address)
    elif family == AF_INET6:
        return dns.ipv6.inet_ntoa(address)
    else:
        raise NotImplementedError


def af_for_address(text):
    """Determine the address family of a textual-form network address.

    *text*, a ``text``, the textual address.

    Raises ``ValueError`` if the address family cannot be determined
    from the input.

    Returns an ``int``.
    """

    try:
        dns.ipv4.inet_aton(text)
        return AF_INET
    except Exception:
        try:
            dns.ipv6.inet_aton(text)
            return AF_INET6
        except:
            raise ValueError


def is_multicast(text):
    """Is the textual-form network address a multicast address?

    *text*, a ``text``, the textual address.

    Raises ``ValueError`` if the address family cannot be determined
    from the input.

    Returns a ``bool``.
    """

    try:
        first = maybe_ord(dns.ipv4.inet_aton(text)[0])
        return first >= 224 and first <= 239
    except Exception:
        try:
            first = maybe_ord(dns.ipv6.inet_aton(text)[0])
            return first == 255
        except Exception:
            raise ValueError
