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

"""A place to store TSIG keys."""

from dns._compat import maybe_decode, maybe_encode

import base64

import dns.name


def from_text(textring):
    """Convert a dictionary containing (textual DNS name, base64 secret) pairs
    into a binary keyring which has (dns.name.Name, binary secret) pairs.
    @rtype: dict"""

    keyring = {}
    for keytext in textring:
        keyname = dns.name.from_text(keytext)
        secret = base64.decodestring(maybe_encode(textring[keytext]))
        keyring[keyname] = secret
    return keyring


def to_text(keyring):
    """Convert a dictionary containing (dns.name.Name, binary secret) pairs
    into a text keyring which has (textual DNS name, base64 secret) pairs.
    @rtype: dict"""

    textring = {}
    for keyname in keyring:
        keytext = maybe_decode(keyname.to_text())
        secret = maybe_decode(base64.encodestring(keyring[keyname]))
        textring[keytext] = secret
    return textring
