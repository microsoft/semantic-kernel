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

"""DNS nodes.  A node is a set of rdatasets."""

from io import StringIO

import dns.rdataset
import dns.rdatatype
import dns.renderer


class Node(object):

    """A Node is a set of rdatasets."""

    __slots__ = ['rdatasets']

    def __init__(self):
        #: the set of rdatsets, represented as a list.
        self.rdatasets = []

    def to_text(self, name, **kw):
        """Convert a node to text format.

        Each rdataset at the node is printed.  Any keyword arguments
        to this method are passed on to the rdataset's to_text() method.

        *name*, a ``dns.name.Name`` or ``text``, the owner name of the rdatasets.

        Returns a ``text``.
        """

        s = StringIO()
        for rds in self.rdatasets:
            if len(rds) > 0:
                s.write(rds.to_text(name, **kw))
                s.write(u'\n')
        return s.getvalue()[:-1]

    def __repr__(self):
        return '<DNS node ' + str(id(self)) + '>'

    def __eq__(self, other):
        #
        # This is inefficient.  Good thing we don't need to do it much.
        #
        for rd in self.rdatasets:
            if rd not in other.rdatasets:
                return False
        for rd in other.rdatasets:
            if rd not in self.rdatasets:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self.rdatasets)

    def __iter__(self):
        return iter(self.rdatasets)

    def find_rdataset(self, rdclass, rdtype, covers=dns.rdatatype.NONE,
                      create=False):
        """Find an rdataset matching the specified properties in the
        current node.

        *rdclass*, an ``int``, the class of the rdataset.

        *rdtype*, an ``int``, the type of the rdataset.

        *covers*, an ``int``, the covered type.  Usually this value is
        dns.rdatatype.NONE, but if the rdtype is dns.rdatatype.SIG or
        dns.rdatatype.RRSIG, then the covers value will be the rdata
        type the SIG/RRSIG covers.  The library treats the SIG and RRSIG
        types as if they were a family of
        types, e.g. RRSIG(A), RRSIG(NS), RRSIG(SOA).  This makes RRSIGs much
        easier to work with than if RRSIGs covering different rdata
        types were aggregated into a single RRSIG rdataset.

        *create*, a ``bool``.  If True, create the rdataset if it is not found.

        Raises ``KeyError`` if an rdataset of the desired type and class does
        not exist and *create* is not ``True``.

        Returns a ``dns.rdataset.Rdataset``.
        """

        for rds in self.rdatasets:
            if rds.match(rdclass, rdtype, covers):
                return rds
        if not create:
            raise KeyError
        rds = dns.rdataset.Rdataset(rdclass, rdtype)
        self.rdatasets.append(rds)
        return rds

    def get_rdataset(self, rdclass, rdtype, covers=dns.rdatatype.NONE,
                     create=False):
        """Get an rdataset matching the specified properties in the
        current node.

        None is returned if an rdataset of the specified type and
        class does not exist and *create* is not ``True``.

        *rdclass*, an ``int``, the class of the rdataset.

        *rdtype*, an ``int``, the type of the rdataset.

        *covers*, an ``int``, the covered type.  Usually this value is
        dns.rdatatype.NONE, but if the rdtype is dns.rdatatype.SIG or
        dns.rdatatype.RRSIG, then the covers value will be the rdata
        type the SIG/RRSIG covers.  The library treats the SIG and RRSIG
        types as if they were a family of
        types, e.g. RRSIG(A), RRSIG(NS), RRSIG(SOA).  This makes RRSIGs much
        easier to work with than if RRSIGs covering different rdata
        types were aggregated into a single RRSIG rdataset.

        *create*, a ``bool``.  If True, create the rdataset if it is not found.

        Returns a ``dns.rdataset.Rdataset`` or ``None``.
        """

        try:
            rds = self.find_rdataset(rdclass, rdtype, covers, create)
        except KeyError:
            rds = None
        return rds

    def delete_rdataset(self, rdclass, rdtype, covers=dns.rdatatype.NONE):
        """Delete the rdataset matching the specified properties in the
        current node.

        If a matching rdataset does not exist, it is not an error.

        *rdclass*, an ``int``, the class of the rdataset.

        *rdtype*, an ``int``, the type of the rdataset.

        *covers*, an ``int``, the covered type.
        """

        rds = self.get_rdataset(rdclass, rdtype, covers)
        if rds is not None:
            self.rdatasets.remove(rds)

    def replace_rdataset(self, replacement):
        """Replace an rdataset.

        It is not an error if there is no rdataset matching *replacement*.

        Ownership of the *replacement* object is transferred to the node;
        in other words, this method does not store a copy of *replacement*
        at the node, it stores *replacement* itself.

        *replacement*, a ``dns.rdataset.Rdataset``.

        Raises ``ValueError`` if *replacement* is not a
        ``dns.rdataset.Rdataset``.
        """

        if not isinstance(replacement, dns.rdataset.Rdataset):
            raise ValueError('replacement is not an rdataset')
        self.delete_rdataset(replacement.rdclass, replacement.rdtype,
                             replacement.covers)
        self.rdatasets.append(replacement)
