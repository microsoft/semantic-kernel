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

"""dnspython release version information."""

#: MAJOR
MAJOR = 1
#: MINOR
MINOR = 16
#: MICRO
MICRO = 0
#: RELEASELEVEL
RELEASELEVEL = 0x0f
#: SERIAL
SERIAL = 0

if RELEASELEVEL == 0x0f:
    #: version
    version = '%d.%d.%d' % (MAJOR, MINOR, MICRO)
elif RELEASELEVEL == 0x00:
    version = '%d.%d.%dx%d' % \
              (MAJOR, MINOR, MICRO, SERIAL)
else:
    version = '%d.%d.%d%x%d' % \
              (MAJOR, MINOR, MICRO, RELEASELEVEL, SERIAL)

#: hexversion
hexversion = MAJOR << 24 | MINOR << 16 | MICRO << 8 | RELEASELEVEL << 4 | \
    SERIAL
