# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2011,2017 Nominum, Inc.
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

"""DNS Wire Data Helper"""

import dns.exception
from ._compat import binary_type, string_types, PY2

# Figure out what constant python passes for an unspecified slice bound.
# It's supposed to be sys.maxint, yet on 64-bit windows sys.maxint is 2^31 - 1
# but Python uses 2^63 - 1 as the constant.  Rather than making pointless
# extra comparisons, duplicating code, or weakening WireData, we just figure
# out what constant Python will use.


class _SliceUnspecifiedBound(binary_type):

    def __getitem__(self, key):
        return key.stop

    if PY2:
        def __getslice__(self, i, j):  # pylint: disable=getslice-method
            return self.__getitem__(slice(i, j))

_unspecified_bound = _SliceUnspecifiedBound()[1:]


class WireData(binary_type):
    # WireData is a binary type with stricter slicing

    def __getitem__(self, key):
        try:
            if isinstance(key, slice):
                # make sure we are not going outside of valid ranges,
                # do stricter control of boundaries than python does
                # by default
                start = key.start
                stop = key.stop

                if PY2:
                    if stop == _unspecified_bound:
                        # handle the case where the right bound is unspecified
                        stop = len(self)

                    if start < 0 or stop < 0:
                        raise dns.exception.FormError
                    # If it's not an empty slice, access left and right bounds
                    # to make sure they're valid
                    if start != stop:
                        super(WireData, self).__getitem__(start)
                        super(WireData, self).__getitem__(stop - 1)
                else:
                    for index in (start, stop):
                        if index is None:
                            continue
                        elif abs(index) > len(self):
                            raise dns.exception.FormError

                return WireData(super(WireData, self).__getitem__(
                    slice(start, stop)))
            return bytearray(self.unwrap())[key]
        except IndexError:
            raise dns.exception.FormError

    if PY2:
        def __getslice__(self, i, j):  # pylint: disable=getslice-method
            return self.__getitem__(slice(i, j))

    def __iter__(self):
        i = 0
        while 1:
            try:
                yield self[i]
                i += 1
            except dns.exception.FormError:
                raise StopIteration

    def unwrap(self):
        return binary_type(self)


def maybe_wrap(wire):
    if isinstance(wire, WireData):
        return wire
    elif isinstance(wire, binary_type):
        return WireData(wire)
    elif isinstance(wire, string_types):
        return WireData(wire.encode())
    raise ValueError("unhandled type %s" % type(wire))
