# -*- coding: utf-8 -*-
#
#  Copyright 2011 Sybren A. Stüvel <sybren@stuvel.eu>
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Functions that load and write PEM-encoded files."""

import base64

from rsa._compat import is_bytes, range


def _markers(pem_marker):
    """
    Returns the start and end PEM markers, as bytes.
    """

    if not is_bytes(pem_marker):
        pem_marker = pem_marker.encode('ascii')

    return (b'-----BEGIN ' + pem_marker + b'-----',
            b'-----END ' + pem_marker + b'-----')


def load_pem(contents, pem_marker):
    """Loads a PEM file.

    :param contents: the contents of the file to interpret
    :param pem_marker: the marker of the PEM content, such as 'RSA PRIVATE KEY'
        when your file has '-----BEGIN RSA PRIVATE KEY-----' and
        '-----END RSA PRIVATE KEY-----' markers.

    :return: the base64-decoded content between the start and end markers.

    @raise ValueError: when the content is invalid, for example when the start
        marker cannot be found.

    """

    # We want bytes, not text. If it's text, it can be converted to ASCII bytes.
    if not is_bytes(contents):
        contents = contents.encode('ascii')

    (pem_start, pem_end) = _markers(pem_marker)

    pem_lines = []
    in_pem_part = False

    for line in contents.splitlines():
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Handle start marker
        if line == pem_start:
            if in_pem_part:
                raise ValueError('Seen start marker "%s" twice' % pem_start)

            in_pem_part = True
            continue

        # Skip stuff before first marker
        if not in_pem_part:
            continue

        # Handle end marker
        if in_pem_part and line == pem_end:
            in_pem_part = False
            break

        # Load fields
        if b':' in line:
            continue

        pem_lines.append(line)

    # Do some sanity checks
    if not pem_lines:
        raise ValueError('No PEM start marker "%s" found' % pem_start)

    if in_pem_part:
        raise ValueError('No PEM end marker "%s" found' % pem_end)

    # Base64-decode the contents
    pem = b''.join(pem_lines)
    return base64.standard_b64decode(pem)


def save_pem(contents, pem_marker):
    """Saves a PEM file.

    :param contents: the contents to encode in PEM format
    :param pem_marker: the marker of the PEM content, such as 'RSA PRIVATE KEY'
        when your file has '-----BEGIN RSA PRIVATE KEY-----' and
        '-----END RSA PRIVATE KEY-----' markers.

    :return: the base64-encoded content between the start and end markers, as bytes.

    """

    (pem_start, pem_end) = _markers(pem_marker)

    b64 = base64.standard_b64encode(contents).replace(b'\n', b'')
    pem_lines = [pem_start]

    for block_start in range(0, len(b64), 64):
        block = b64[block_start:block_start + 64]
        pem_lines.append(block)

    pem_lines.append(pem_end)
    pem_lines.append(b'')

    return b'\n'.join(pem_lines)
