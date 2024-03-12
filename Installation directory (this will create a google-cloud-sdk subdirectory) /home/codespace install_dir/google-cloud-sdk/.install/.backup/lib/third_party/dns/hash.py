# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2011 Nominum, Inc.
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

"""Hashing backwards compatibility wrapper"""

import hashlib
import warnings

warnings.warn(
    "dns.hash module will be removed in future versions. Please use hashlib instead.",
    DeprecationWarning)

hashes = {}
hashes['MD5'] = hashlib.md5
hashes['SHA1'] = hashlib.sha1
hashes['SHA224'] = hashlib.sha224
hashes['SHA256'] = hashlib.sha256
hashes['SHA384'] = hashlib.sha384
hashes['SHA512'] = hashlib.sha512


def get(algorithm):
    return hashes[algorithm.upper()]
