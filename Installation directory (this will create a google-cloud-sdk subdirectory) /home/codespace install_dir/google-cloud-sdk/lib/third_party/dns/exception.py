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

"""Common DNS Exceptions.

Dnspython modules may also define their own exceptions, which will
always be subclasses of ``DNSException``.
"""

class DNSException(Exception):
    """Abstract base class shared by all dnspython exceptions.

    It supports two basic modes of operation:

    a) Old/compatible mode is used if ``__init__`` was called with
    empty *kwargs*.  In compatible mode all *args* are passed
    to the standard Python Exception class as before and all *args* are
    printed by the standard ``__str__`` implementation.  Class variable
    ``msg`` (or doc string if ``msg`` is ``None``) is returned from ``str()``
    if *args* is empty.

    b) New/parametrized mode is used if ``__init__`` was called with
    non-empty *kwargs*.
    In the new mode *args* must be empty and all kwargs must match
    those set in class variable ``supp_kwargs``. All kwargs are stored inside
    ``self.kwargs`` and used in a new ``__str__`` implementation to construct
    a formatted message based on the ``fmt`` class variable, a ``string``.

    In the simplest case it is enough to override the ``supp_kwargs``
    and ``fmt`` class variables to get nice parametrized messages.
    """

    msg = None  # non-parametrized message
    supp_kwargs = set()  # accepted parameters for _fmt_kwargs (sanity check)
    fmt = None  # message parametrized with results from _fmt_kwargs

    def __init__(self, *args, **kwargs):
        self._check_params(*args, **kwargs)
        if kwargs:
            self.kwargs = self._check_kwargs(**kwargs)
            self.msg = str(self)
        else:
            self.kwargs = dict()  # defined but empty for old mode exceptions
        if self.msg is None:
            # doc string is better implicit message than empty string
            self.msg = self.__doc__
        if args:
            super(DNSException, self).__init__(*args)
        else:
            super(DNSException, self).__init__(self.msg)

    def _check_params(self, *args, **kwargs):
        """Old exceptions supported only args and not kwargs.

        For sanity we do not allow to mix old and new behavior."""
        if args or kwargs:
            assert bool(args) != bool(kwargs), \
                'keyword arguments are mutually exclusive with positional args'

    def _check_kwargs(self, **kwargs):
        if kwargs:
            assert set(kwargs.keys()) == self.supp_kwargs, \
                'following set of keyword args is required: %s' % (
                    self.supp_kwargs)
        return kwargs

    def _fmt_kwargs(self, **kwargs):
        """Format kwargs before printing them.

        Resulting dictionary has to have keys necessary for str.format call
        on fmt class variable.
        """
        fmtargs = {}
        for kw, data in kwargs.items():
            if isinstance(data, (list, set)):
                # convert list of <someobj> to list of str(<someobj>)
                fmtargs[kw] = list(map(str, data))
                if len(fmtargs[kw]) == 1:
                    # remove list brackets [] from single-item lists
                    fmtargs[kw] = fmtargs[kw].pop()
            else:
                fmtargs[kw] = data
        return fmtargs

    def __str__(self):
        if self.kwargs and self.fmt:
            # provide custom message constructed from keyword arguments
            fmtargs = self._fmt_kwargs(**self.kwargs)
            return self.fmt.format(**fmtargs)
        else:
            # print *args directly in the same way as old DNSException
            return super(DNSException, self).__str__()


class FormError(DNSException):
    """DNS message is malformed."""


class SyntaxError(DNSException):
    """Text input is malformed."""


class UnexpectedEnd(SyntaxError):
    """Text input ended unexpectedly."""


class TooBig(DNSException):
    """The DNS message is too big."""


class Timeout(DNSException):
    """The DNS operation timed out."""
    supp_kwargs = {'timeout'}
    fmt = "The DNS operation timed out after {timeout} seconds"
