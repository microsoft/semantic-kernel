# Copyright (C) Dnspython Contributors, see LICENSE for text of ISC license

# Copyright (C) 2012-2017 Nominum, Inc.
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

"""DNS GENERATE range conversion."""

import dns

def from_text(text):
    """Convert the text form of a range in a ``$GENERATE`` statement to an
    integer.

    *text*, a ``str``, the textual range in ``$GENERATE`` form.

    Returns a tuple of three ``int`` values ``(start, stop, step)``.
    """

    # TODO, figure out the bounds on start, stop and step.
    step = 1
    cur = ''
    state = 0
    # state   0 1 2 3 4
    #         x - y / z

    if text and text[0] == '-':
        raise dns.exception.SyntaxError("Start cannot be a negative number")

    for c in text:
        if c == '-' and state == 0:
            start = int(cur)
            cur = ''
            state = 2
        elif c == '/':
            stop = int(cur)
            cur = ''
            state = 4
        elif c.isdigit():
            cur += c
        else:
            raise dns.exception.SyntaxError("Could not parse %s" % (c))

    if state in (1, 3):
        raise dns.exception.SyntaxError()

    if state == 2:
        stop = int(cur)

    if state == 4:
        step = int(cur)

    assert step >= 1
    assert start >= 0
    assert start <= stop
    # TODO, can start == stop?

    return (start, stop, step)
