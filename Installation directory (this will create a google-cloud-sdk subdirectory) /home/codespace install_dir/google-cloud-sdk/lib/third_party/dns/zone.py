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

"""DNS Zones."""

from __future__ import generators

import sys
import re
import os
from io import BytesIO

import dns.exception
import dns.name
import dns.node
import dns.rdataclass
import dns.rdatatype
import dns.rdata
import dns.rdtypes.ANY.SOA
import dns.rrset
import dns.tokenizer
import dns.ttl
import dns.grange
from ._compat import string_types, text_type, PY3


class BadZone(dns.exception.DNSException):

    """The DNS zone is malformed."""


class NoSOA(BadZone):

    """The DNS zone has no SOA RR at its origin."""


class NoNS(BadZone):

    """The DNS zone has no NS RRset at its origin."""


class UnknownOrigin(BadZone):

    """The DNS zone's origin is unknown."""


class Zone(object):

    """A DNS zone.

    A Zone is a mapping from names to nodes.  The zone object may be
    treated like a Python dictionary, e.g. zone[name] will retrieve
    the node associated with that name.  The I{name} may be a
    dns.name.Name object, or it may be a string.  In the either case,
    if the name is relative it is treated as relative to the origin of
    the zone.

    @ivar rdclass: The zone's rdata class; the default is class IN.
    @type rdclass: int
    @ivar origin: The origin of the zone.
    @type origin: dns.name.Name object
    @ivar nodes: A dictionary mapping the names of nodes in the zone to the
    nodes themselves.
    @type nodes: dict
    @ivar relativize: should names in the zone be relativized?
    @type relativize: bool
    @cvar node_factory: the factory used to create a new node
    @type node_factory: class or callable
    """

    node_factory = dns.node.Node

    __slots__ = ['rdclass', 'origin', 'nodes', 'relativize']

    def __init__(self, origin, rdclass=dns.rdataclass.IN, relativize=True):
        """Initialize a zone object.

        @param origin: The origin of the zone.
        @type origin: dns.name.Name object
        @param rdclass: The zone's rdata class; the default is class IN.
        @type rdclass: int"""

        if origin is not None:
            if isinstance(origin, string_types):
                origin = dns.name.from_text(origin)
            elif not isinstance(origin, dns.name.Name):
                raise ValueError("origin parameter must be convertible to a "
                                 "DNS name")
            if not origin.is_absolute():
                raise ValueError("origin parameter must be an absolute name")
        self.origin = origin
        self.rdclass = rdclass
        self.nodes = {}
        self.relativize = relativize

    def __eq__(self, other):
        """Two zones are equal if they have the same origin, class, and
        nodes.
        @rtype: bool
        """

        if not isinstance(other, Zone):
            return False
        if self.rdclass != other.rdclass or \
           self.origin != other.origin or \
           self.nodes != other.nodes:
            return False
        return True

    def __ne__(self, other):
        """Are two zones not equal?
        @rtype: bool
        """

        return not self.__eq__(other)

    def _validate_name(self, name):
        if isinstance(name, string_types):
            name = dns.name.from_text(name, None)
        elif not isinstance(name, dns.name.Name):
            raise KeyError("name parameter must be convertible to a DNS name")
        if name.is_absolute():
            if not name.is_subdomain(self.origin):
                raise KeyError(
                    "name parameter must be a subdomain of the zone origin")
            if self.relativize:
                name = name.relativize(self.origin)
        return name

    def __getitem__(self, key):
        key = self._validate_name(key)
        return self.nodes[key]

    def __setitem__(self, key, value):
        key = self._validate_name(key)
        self.nodes[key] = value

    def __delitem__(self, key):
        key = self._validate_name(key)
        del self.nodes[key]

    def __iter__(self):
        return self.nodes.__iter__()

    def iterkeys(self):
        if PY3:
            return self.nodes.keys() # pylint: disable=dict-keys-not-iterating
        else:
            return self.nodes.iterkeys()  # pylint: disable=dict-iter-method

    def keys(self):
        return self.nodes.keys() # pylint: disable=dict-keys-not-iterating

    def itervalues(self):
        if PY3:
            return self.nodes.values() # pylint: disable=dict-values-not-iterating
        else:
            return self.nodes.itervalues()  # pylint: disable=dict-iter-method

    def values(self):
        return self.nodes.values() # pylint: disable=dict-values-not-iterating

    def items(self):
        return self.nodes.items() # pylint: disable=dict-items-not-iterating

    iteritems = items

    def get(self, key):
        key = self._validate_name(key)
        return self.nodes.get(key)

    def __contains__(self, other):
        return other in self.nodes

    def find_node(self, name, create=False):
        """Find a node in the zone, possibly creating it.

        @param name: the name of the node to find
        @type name: dns.name.Name object or string
        @param create: should the node be created if it doesn't exist?
        @type create: bool
        @raises KeyError: the name is not known and create was not specified.
        @rtype: dns.node.Node object
        """

        name = self._validate_name(name)
        node = self.nodes.get(name)
        if node is None:
            if not create:
                raise KeyError
            node = self.node_factory()
            self.nodes[name] = node
        return node

    def get_node(self, name, create=False):
        """Get a node in the zone, possibly creating it.

        This method is like L{find_node}, except it returns None instead
        of raising an exception if the node does not exist and creation
        has not been requested.

        @param name: the name of the node to find
        @type name: dns.name.Name object or string
        @param create: should the node be created if it doesn't exist?
        @type create: bool
        @rtype: dns.node.Node object or None
        """

        try:
            node = self.find_node(name, create)
        except KeyError:
            node = None
        return node

    def delete_node(self, name):
        """Delete the specified node if it exists.

        It is not an error if the node does not exist.
        """

        name = self._validate_name(name)
        if name in self.nodes:
            del self.nodes[name]

    def find_rdataset(self, name, rdtype, covers=dns.rdatatype.NONE,
                      create=False):
        """Look for rdata with the specified name and type in the zone,
        and return an rdataset encapsulating it.

        The I{name}, I{rdtype}, and I{covers} parameters may be
        strings, in which case they will be converted to their proper
        type.

        The rdataset returned is not a copy; changes to it will change
        the zone.

        KeyError is raised if the name or type are not found.
        Use L{get_rdataset} if you want to have None returned instead.

        @param name: the owner name to look for
        @type name: DNS.name.Name object or string
        @param rdtype: the rdata type desired
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        @param create: should the node and rdataset be created if they do not
        exist?
        @type create: bool
        @raises KeyError: the node or rdata could not be found
        @rtype: dns.rdataset.Rdataset object
        """

        name = self._validate_name(name)
        if isinstance(rdtype, string_types):
            rdtype = dns.rdatatype.from_text(rdtype)
        if isinstance(covers, string_types):
            covers = dns.rdatatype.from_text(covers)
        node = self.find_node(name, create)
        return node.find_rdataset(self.rdclass, rdtype, covers, create)

    def get_rdataset(self, name, rdtype, covers=dns.rdatatype.NONE,
                     create=False):
        """Look for rdata with the specified name and type in the zone,
        and return an rdataset encapsulating it.

        The I{name}, I{rdtype}, and I{covers} parameters may be
        strings, in which case they will be converted to their proper
        type.

        The rdataset returned is not a copy; changes to it will change
        the zone.

        None is returned if the name or type are not found.
        Use L{find_rdataset} if you want to have KeyError raised instead.

        @param name: the owner name to look for
        @type name: DNS.name.Name object or string
        @param rdtype: the rdata type desired
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        @param create: should the node and rdataset be created if they do not
        exist?
        @type create: bool
        @rtype: dns.rdataset.Rdataset object or None
        """

        try:
            rdataset = self.find_rdataset(name, rdtype, covers, create)
        except KeyError:
            rdataset = None
        return rdataset

    def delete_rdataset(self, name, rdtype, covers=dns.rdatatype.NONE):
        """Delete the rdataset matching I{rdtype} and I{covers}, if it
        exists at the node specified by I{name}.

        The I{name}, I{rdtype}, and I{covers} parameters may be
        strings, in which case they will be converted to their proper
        type.

        It is not an error if the node does not exist, or if there is no
        matching rdataset at the node.

        If the node has no rdatasets after the deletion, it will itself
        be deleted.

        @param name: the owner name to look for
        @type name: DNS.name.Name object or string
        @param rdtype: the rdata type desired
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        """

        name = self._validate_name(name)
        if isinstance(rdtype, string_types):
            rdtype = dns.rdatatype.from_text(rdtype)
        if isinstance(covers, string_types):
            covers = dns.rdatatype.from_text(covers)
        node = self.get_node(name)
        if node is not None:
            node.delete_rdataset(self.rdclass, rdtype, covers)
            if len(node) == 0:
                self.delete_node(name)

    def replace_rdataset(self, name, replacement):
        """Replace an rdataset at name.

        It is not an error if there is no rdataset matching I{replacement}.

        Ownership of the I{replacement} object is transferred to the zone;
        in other words, this method does not store a copy of I{replacement}
        at the node, it stores I{replacement} itself.

        If the I{name} node does not exist, it is created.

        @param name: the owner name
        @type name: DNS.name.Name object or string
        @param replacement: the replacement rdataset
        @type replacement: dns.rdataset.Rdataset
        """

        if replacement.rdclass != self.rdclass:
            raise ValueError('replacement.rdclass != zone.rdclass')
        node = self.find_node(name, True)
        node.replace_rdataset(replacement)

    def find_rrset(self, name, rdtype, covers=dns.rdatatype.NONE):
        """Look for rdata with the specified name and type in the zone,
        and return an RRset encapsulating it.

        The I{name}, I{rdtype}, and I{covers} parameters may be
        strings, in which case they will be converted to their proper
        type.

        This method is less efficient than the similar
        L{find_rdataset} because it creates an RRset instead of
        returning the matching rdataset.  It may be more convenient
        for some uses since it returns an object which binds the owner
        name to the rdata.

        This method may not be used to create new nodes or rdatasets;
        use L{find_rdataset} instead.

        KeyError is raised if the name or type are not found.
        Use L{get_rrset} if you want to have None returned instead.

        @param name: the owner name to look for
        @type name: DNS.name.Name object or string
        @param rdtype: the rdata type desired
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        @raises KeyError: the node or rdata could not be found
        @rtype: dns.rrset.RRset object
        """

        name = self._validate_name(name)
        if isinstance(rdtype, string_types):
            rdtype = dns.rdatatype.from_text(rdtype)
        if isinstance(covers, string_types):
            covers = dns.rdatatype.from_text(covers)
        rdataset = self.nodes[name].find_rdataset(self.rdclass, rdtype, covers)
        rrset = dns.rrset.RRset(name, self.rdclass, rdtype, covers)
        rrset.update(rdataset)
        return rrset

    def get_rrset(self, name, rdtype, covers=dns.rdatatype.NONE):
        """Look for rdata with the specified name and type in the zone,
        and return an RRset encapsulating it.

        The I{name}, I{rdtype}, and I{covers} parameters may be
        strings, in which case they will be converted to their proper
        type.

        This method is less efficient than the similar L{get_rdataset}
        because it creates an RRset instead of returning the matching
        rdataset.  It may be more convenient for some uses since it
        returns an object which binds the owner name to the rdata.

        This method may not be used to create new nodes or rdatasets;
        use L{find_rdataset} instead.

        None is returned if the name or type are not found.
        Use L{find_rrset} if you want to have KeyError raised instead.

        @param name: the owner name to look for
        @type name: DNS.name.Name object or string
        @param rdtype: the rdata type desired
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        @rtype: dns.rrset.RRset object
        """

        try:
            rrset = self.find_rrset(name, rdtype, covers)
        except KeyError:
            rrset = None
        return rrset

    def iterate_rdatasets(self, rdtype=dns.rdatatype.ANY,
                          covers=dns.rdatatype.NONE):
        """Return a generator which yields (name, rdataset) tuples for
        all rdatasets in the zone which have the specified I{rdtype}
        and I{covers}.  If I{rdtype} is dns.rdatatype.ANY, the default,
        then all rdatasets will be matched.

        @param rdtype: int or string
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        """

        if isinstance(rdtype, string_types):
            rdtype = dns.rdatatype.from_text(rdtype)
        if isinstance(covers, string_types):
            covers = dns.rdatatype.from_text(covers)
        for (name, node) in self.iteritems(): # pylint: disable=dict-iter-method
            for rds in node:
                if rdtype == dns.rdatatype.ANY or \
                   (rds.rdtype == rdtype and rds.covers == covers):
                    yield (name, rds)

    def iterate_rdatas(self, rdtype=dns.rdatatype.ANY,
                       covers=dns.rdatatype.NONE):
        """Return a generator which yields (name, ttl, rdata) tuples for
        all rdatas in the zone which have the specified I{rdtype}
        and I{covers}.  If I{rdtype} is dns.rdatatype.ANY, the default,
        then all rdatas will be matched.

        @param rdtype: int or string
        @type rdtype: int or string
        @param covers: the covered type (defaults to None)
        @type covers: int or string
        """

        if isinstance(rdtype, string_types):
            rdtype = dns.rdatatype.from_text(rdtype)
        if isinstance(covers, string_types):
            covers = dns.rdatatype.from_text(covers)
        for (name, node) in self.iteritems(): # pylint: disable=dict-iter-method
            for rds in node:
                if rdtype == dns.rdatatype.ANY or \
                   (rds.rdtype == rdtype and rds.covers == covers):
                    for rdata in rds:
                        yield (name, rds.ttl, rdata)

    def to_file(self, f, sorted=True, relativize=True, nl=None):
        """Write a zone to a file.

        @param f: file or string.  If I{f} is a string, it is treated
        as the name of a file to open.
        @param sorted: if True, the file will be written with the
        names sorted in DNSSEC order from least to greatest.  Otherwise
        the names will be written in whatever order they happen to have
        in the zone's dictionary.
        @param relativize: if True, domain names in the output will be
        relativized to the zone's origin (if possible).
        @type relativize: bool
        @param nl: The end of line string.  If not specified, the
        output will use the platform's native end-of-line marker (i.e.
        LF on POSIX, CRLF on Windows, CR on Macintosh).
        @type nl: string or None
        """

        if isinstance(f, string_types):
            f = open(f, 'wb')
            want_close = True
        else:
            want_close = False

        # must be in this way, f.encoding may contain None, or even attribute
        # may not be there
        file_enc = getattr(f, 'encoding', None)
        if file_enc is None:
            file_enc = 'utf-8'

        if nl is None:
            nl_b = os.linesep.encode(file_enc)  # binary mode, '\n' is not enough
            nl = u'\n'
        elif isinstance(nl, string_types):
            nl_b = nl.encode(file_enc)
        else:
            nl_b = nl
            nl = nl.decode()

        try:
            if sorted:
                names = list(self.keys())
                names.sort()
            else:
                names = self.iterkeys() # pylint: disable=dict-iter-method
            for n in names:
                l = self[n].to_text(n, origin=self.origin,
                                    relativize=relativize)
                if isinstance(l, text_type):
                    l_b = l.encode(file_enc)
                else:
                    l_b = l
                    l = l.decode()

                try:
                    f.write(l_b)
                    f.write(nl_b)
                except TypeError:  # textual mode
                    f.write(l)
                    f.write(nl)
        finally:
            if want_close:
                f.close()

    def to_text(self, sorted=True, relativize=True, nl=None):
        """Return a zone's text as though it were written to a file.

        @param sorted: if True, the file will be written with the
        names sorted in DNSSEC order from least to greatest.  Otherwise
        the names will be written in whatever order they happen to have
        in the zone's dictionary.
        @param relativize: if True, domain names in the output will be
        relativized to the zone's origin (if possible).
        @type relativize: bool
        @param nl: The end of line string.  If not specified, the
        output will use the platform's native end-of-line marker (i.e.
        LF on POSIX, CRLF on Windows, CR on Macintosh).
        @type nl: string or None
        """
        temp_buffer = BytesIO()
        self.to_file(temp_buffer, sorted, relativize, nl)
        return_value = temp_buffer.getvalue()
        temp_buffer.close()
        return return_value

    def check_origin(self):
        """Do some simple checking of the zone's origin.

        @raises dns.zone.NoSOA: there is no SOA RR
        @raises dns.zone.NoNS: there is no NS RRset
        @raises KeyError: there is no origin node
        """
        if self.relativize:
            name = dns.name.empty
        else:
            name = self.origin
        if self.get_rdataset(name, dns.rdatatype.SOA) is None:
            raise NoSOA
        if self.get_rdataset(name, dns.rdatatype.NS) is None:
            raise NoNS


class _MasterReader(object):

    """Read a DNS master file

    @ivar tok: The tokenizer
    @type tok: dns.tokenizer.Tokenizer object
    @ivar last_ttl: The last seen explicit TTL for an RR
    @type last_ttl: int
    @ivar last_ttl_known: Has last TTL been detected
    @type last_ttl_known: bool
    @ivar default_ttl: The default TTL from a $TTL directive or SOA RR
    @type default_ttl: int
    @ivar default_ttl_known: Has default TTL been detected
    @type default_ttl_known: bool
    @ivar last_name: The last name read
    @type last_name: dns.name.Name object
    @ivar current_origin: The current origin
    @type current_origin: dns.name.Name object
    @ivar relativize: should names in the zone be relativized?
    @type relativize: bool
    @ivar zone: the zone
    @type zone: dns.zone.Zone object
    @ivar saved_state: saved reader state (used when processing $INCLUDE)
    @type saved_state: list of (tokenizer, current_origin, last_name, file,
    last_ttl, last_ttl_known, default_ttl, default_ttl_known) tuples.
    @ivar current_file: the file object of the $INCLUDed file being parsed
    (None if no $INCLUDE is active).
    @ivar allow_include: is $INCLUDE allowed?
    @type allow_include: bool
    @ivar check_origin: should sanity checks of the origin node be done?
    The default is True.
    @type check_origin: bool
    """

    def __init__(self, tok, origin, rdclass, relativize, zone_factory=Zone,
                 allow_include=False, check_origin=True):
        if isinstance(origin, string_types):
            origin = dns.name.from_text(origin)
        self.tok = tok
        self.current_origin = origin
        self.relativize = relativize
        self.last_ttl = 0
        self.last_ttl_known = False
        self.default_ttl = 0
        self.default_ttl_known = False
        self.last_name = self.current_origin
        self.zone = zone_factory(origin, rdclass, relativize=relativize)
        self.saved_state = []
        self.current_file = None
        self.allow_include = allow_include
        self.check_origin = check_origin

    def _eat_line(self):
        while 1:
            token = self.tok.get()
            if token.is_eol_or_eof():
                break

    def _rr_line(self):
        """Process one line from a DNS master file."""
        # Name
        if self.current_origin is None:
            raise UnknownOrigin
        token = self.tok.get(want_leading=True)
        if not token.is_whitespace():
            self.last_name = dns.name.from_text(
                token.value, self.current_origin)
        else:
            token = self.tok.get()
            if token.is_eol_or_eof():
                # treat leading WS followed by EOL/EOF as if they were EOL/EOF.
                return
            self.tok.unget(token)
        name = self.last_name
        if not name.is_subdomain(self.zone.origin):
            self._eat_line()
            return
        if self.relativize:
            name = name.relativize(self.zone.origin)
        token = self.tok.get()
        if not token.is_identifier():
            raise dns.exception.SyntaxError
        # TTL
        try:
            ttl = dns.ttl.from_text(token.value)
            self.last_ttl = ttl
            self.last_ttl_known = True
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except dns.ttl.BadTTL:
            if not (self.last_ttl_known or self.default_ttl_known):
                raise dns.exception.SyntaxError("Missing default TTL value")
            if self.default_ttl_known:
                ttl = self.default_ttl
            else:
                ttl = self.last_ttl
        # Class
        try:
            rdclass = dns.rdataclass.from_text(token.value)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except dns.exception.SyntaxError:
            raise dns.exception.SyntaxError
        except Exception:
            rdclass = self.zone.rdclass
        if rdclass != self.zone.rdclass:
            raise dns.exception.SyntaxError("RR class is not zone's class")
        # Type
        try:
            rdtype = dns.rdatatype.from_text(token.value)
        except:
            raise dns.exception.SyntaxError(
                "unknown rdatatype '%s'" % token.value)
        n = self.zone.nodes.get(name)
        if n is None:
            n = self.zone.node_factory()
            self.zone.nodes[name] = n
        try:
            rd = dns.rdata.from_text(rdclass, rdtype, self.tok,
                                     self.current_origin, False)
        except dns.exception.SyntaxError:
            # Catch and reraise.
            (ty, va) = sys.exc_info()[:2]
            raise va
        except:
            # All exceptions that occur in the processing of rdata
            # are treated as syntax errors.  This is not strictly
            # correct, but it is correct almost all of the time.
            # We convert them to syntax errors so that we can emit
            # helpful filename:line info.
            (ty, va) = sys.exc_info()[:2]
            raise dns.exception.SyntaxError(
                "caught exception {}: {}".format(str(ty), str(va)))

        if not self.default_ttl_known and isinstance(rd, dns.rdtypes.ANY.SOA.SOA):
            # The pre-RFC2308 and pre-BIND9 behavior inherits the zone default
            # TTL from the SOA minttl if no $TTL statement is present before the
            # SOA is parsed.
            self.default_ttl = rd.minimum
            self.default_ttl_known = True

        rd.choose_relativity(self.zone.origin, self.relativize)
        covers = rd.covers()
        rds = n.find_rdataset(rdclass, rdtype, covers, True)
        rds.add(rd, ttl)

    def _parse_modify(self, side):
        # Here we catch everything in '{' '}' in a group so we can replace it
        # with ''.
        is_generate1 = re.compile(r"^.*\$({(\+|-?)(\d+),(\d+),(.)}).*$")
        is_generate2 = re.compile(r"^.*\$({(\+|-?)(\d+)}).*$")
        is_generate3 = re.compile(r"^.*\$({(\+|-?)(\d+),(\d+)}).*$")
        # Sometimes there are modifiers in the hostname. These come after
        # the dollar sign. They are in the form: ${offset[,width[,base]]}.
        # Make names
        g1 = is_generate1.match(side)
        if g1:
            mod, sign, offset, width, base = g1.groups()
            if sign == '':
                sign = '+'
        g2 = is_generate2.match(side)
        if g2:
            mod, sign, offset = g2.groups()
            if sign == '':
                sign = '+'
            width = 0
            base = 'd'
        g3 = is_generate3.match(side)
        if g3:
            mod, sign, offset, width = g1.groups()
            if sign == '':
                sign = '+'
            width = g1.groups()[2]
            base = 'd'

        if not (g1 or g2 or g3):
            mod = ''
            sign = '+'
            offset = 0
            width = 0
            base = 'd'

        if base != 'd':
            raise NotImplementedError()

        return mod, sign, offset, width, base

    def _generate_line(self):
        # range lhs [ttl] [class] type rhs [ comment ]
        """Process one line containing the GENERATE statement from a DNS
        master file."""
        if self.current_origin is None:
            raise UnknownOrigin

        token = self.tok.get()
        # Range (required)
        try:
            start, stop, step = dns.grange.from_text(token.value)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except:
            raise dns.exception.SyntaxError

        # lhs (required)
        try:
            lhs = token.value
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except:
            raise dns.exception.SyntaxError

        # TTL
        try:
            ttl = dns.ttl.from_text(token.value)
            self.last_ttl = ttl
            self.last_ttl_known = True
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except dns.ttl.BadTTL:
            if not (self.last_ttl_known or self.default_ttl_known):
                raise dns.exception.SyntaxError("Missing default TTL value")
            if self.default_ttl_known:
                ttl = self.default_ttl
            else:
                ttl = self.last_ttl
        # Class
        try:
            rdclass = dns.rdataclass.from_text(token.value)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except dns.exception.SyntaxError:
            raise dns.exception.SyntaxError
        except Exception:
            rdclass = self.zone.rdclass
        if rdclass != self.zone.rdclass:
            raise dns.exception.SyntaxError("RR class is not zone's class")
        # Type
        try:
            rdtype = dns.rdatatype.from_text(token.value)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except Exception:
            raise dns.exception.SyntaxError("unknown rdatatype '%s'" %
                                            token.value)

        # lhs (required)
        try:
            rhs = token.value
        except:
            raise dns.exception.SyntaxError

        lmod, lsign, loffset, lwidth, lbase = self._parse_modify(lhs)
        rmod, rsign, roffset, rwidth, rbase = self._parse_modify(rhs)
        for i in range(start, stop + 1, step):
            # +1 because bind is inclusive and python is exclusive

            if lsign == u'+':
                lindex = i + int(loffset)
            elif lsign == u'-':
                lindex = i - int(loffset)

            if rsign == u'-':
                rindex = i - int(roffset)
            elif rsign == u'+':
                rindex = i + int(roffset)

            lzfindex = str(lindex).zfill(int(lwidth))
            rzfindex = str(rindex).zfill(int(rwidth))

            name = lhs.replace(u'$%s' % (lmod), lzfindex)
            rdata = rhs.replace(u'$%s' % (rmod), rzfindex)

            self.last_name = dns.name.from_text(name, self.current_origin)
            name = self.last_name
            if not name.is_subdomain(self.zone.origin):
                self._eat_line()
                return
            if self.relativize:
                name = name.relativize(self.zone.origin)

            n = self.zone.nodes.get(name)
            if n is None:
                n = self.zone.node_factory()
                self.zone.nodes[name] = n
            try:
                rd = dns.rdata.from_text(rdclass, rdtype, rdata,
                                         self.current_origin, False)
            except dns.exception.SyntaxError:
                # Catch and reraise.
                (ty, va) = sys.exc_info()[:2]
                raise va
            except:
                # All exceptions that occur in the processing of rdata
                # are treated as syntax errors.  This is not strictly
                # correct, but it is correct almost all of the time.
                # We convert them to syntax errors so that we can emit
                # helpful filename:line info.
                (ty, va) = sys.exc_info()[:2]
                raise dns.exception.SyntaxError("caught exception %s: %s" %
                                                (str(ty), str(va)))

            rd.choose_relativity(self.zone.origin, self.relativize)
            covers = rd.covers()
            rds = n.find_rdataset(rdclass, rdtype, covers, True)
            rds.add(rd, ttl)

    def read(self):
        """Read a DNS master file and build a zone object.

        @raises dns.zone.NoSOA: No SOA RR was found at the zone origin
        @raises dns.zone.NoNS: No NS RRset was found at the zone origin
        """

        try:
            while 1:
                token = self.tok.get(True, True)
                if token.is_eof():
                    if self.current_file is not None:
                        self.current_file.close()
                    if len(self.saved_state) > 0:
                        (self.tok,
                         self.current_origin,
                         self.last_name,
                         self.current_file,
                         self.last_ttl,
                         self.last_ttl_known,
                         self.default_ttl,
                         self.default_ttl_known) = self.saved_state.pop(-1)
                        continue
                    break
                elif token.is_eol():
                    continue
                elif token.is_comment():
                    self.tok.get_eol()
                    continue
                elif token.value[0] == u'$':
                    c = token.value.upper()
                    if c == u'$TTL':
                        token = self.tok.get()
                        if not token.is_identifier():
                            raise dns.exception.SyntaxError("bad $TTL")
                        self.default_ttl = dns.ttl.from_text(token.value)
                        self.default_ttl_known = True
                        self.tok.get_eol()
                    elif c == u'$ORIGIN':
                        self.current_origin = self.tok.get_name()
                        self.tok.get_eol()
                        if self.zone.origin is None:
                            self.zone.origin = self.current_origin
                    elif c == u'$INCLUDE' and self.allow_include:
                        token = self.tok.get()
                        filename = token.value
                        token = self.tok.get()
                        if token.is_identifier():
                            new_origin =\
                                dns.name.from_text(token.value,
                                                   self.current_origin)
                            self.tok.get_eol()
                        elif not token.is_eol_or_eof():
                            raise dns.exception.SyntaxError(
                                "bad origin in $INCLUDE")
                        else:
                            new_origin = self.current_origin
                        self.saved_state.append((self.tok,
                                                 self.current_origin,
                                                 self.last_name,
                                                 self.current_file,
                                                 self.last_ttl,
                                                 self.last_ttl_known,
                                                 self.default_ttl,
                                                 self.default_ttl_known))
                        self.current_file = open(filename, 'r')
                        self.tok = dns.tokenizer.Tokenizer(self.current_file,
                                                           filename)
                        self.current_origin = new_origin
                    elif c == u'$GENERATE':
                        self._generate_line()
                    else:
                        raise dns.exception.SyntaxError(
                            "Unknown master file directive '" + c + "'")
                    continue
                self.tok.unget(token)
                self._rr_line()
        except dns.exception.SyntaxError as detail:
            (filename, line_number) = self.tok.where()
            if detail is None:
                detail = "syntax error"
            raise dns.exception.SyntaxError(
                "%s:%d: %s" % (filename, line_number, detail))

        # Now that we're done reading, do some basic checking of the zone.
        if self.check_origin:
            self.zone.check_origin()


def from_text(text, origin=None, rdclass=dns.rdataclass.IN,
              relativize=True, zone_factory=Zone, filename=None,
              allow_include=False, check_origin=True):
    """Build a zone object from a master file format string.

    @param text: the master file format input
    @type text: string.
    @param origin: The origin of the zone; if not specified, the first
    $ORIGIN statement in the master file will determine the origin of the
    zone.
    @type origin: dns.name.Name object or string
    @param rdclass: The zone's rdata class; the default is class IN.
    @type rdclass: int
    @param relativize: should names be relativized?  The default is True
    @type relativize: bool
    @param zone_factory: The zone factory to use
    @type zone_factory: function returning a Zone
    @param filename: The filename to emit when describing where an error
    occurred; the default is '<string>'.
    @type filename: string
    @param allow_include: is $INCLUDE allowed?
    @type allow_include: bool
    @param check_origin: should sanity checks of the origin node be done?
    The default is True.
    @type check_origin: bool
    @raises dns.zone.NoSOA: No SOA RR was found at the zone origin
    @raises dns.zone.NoNS: No NS RRset was found at the zone origin
    @rtype: dns.zone.Zone object
    """

    # 'text' can also be a file, but we don't publish that fact
    # since it's an implementation detail.  The official file
    # interface is from_file().

    if filename is None:
        filename = '<string>'
    tok = dns.tokenizer.Tokenizer(text, filename)
    reader = _MasterReader(tok, origin, rdclass, relativize, zone_factory,
                           allow_include=allow_include,
                           check_origin=check_origin)
    reader.read()
    return reader.zone


def from_file(f, origin=None, rdclass=dns.rdataclass.IN,
              relativize=True, zone_factory=Zone, filename=None,
              allow_include=True, check_origin=True):
    """Read a master file and build a zone object.

    @param f: file or string.  If I{f} is a string, it is treated
    as the name of a file to open.
    @param origin: The origin of the zone; if not specified, the first
    $ORIGIN statement in the master file will determine the origin of the
    zone.
    @type origin: dns.name.Name object or string
    @param rdclass: The zone's rdata class; the default is class IN.
    @type rdclass: int
    @param relativize: should names be relativized?  The default is True
    @type relativize: bool
    @param zone_factory: The zone factory to use
    @type zone_factory: function returning a Zone
    @param filename: The filename to emit when describing where an error
    occurred; the default is '<file>', or the value of I{f} if I{f} is a
    string.
    @type filename: string
    @param allow_include: is $INCLUDE allowed?
    @type allow_include: bool
    @param check_origin: should sanity checks of the origin node be done?
    The default is True.
    @type check_origin: bool
    @raises dns.zone.NoSOA: No SOA RR was found at the zone origin
    @raises dns.zone.NoNS: No NS RRset was found at the zone origin
    @rtype: dns.zone.Zone object
    """

    str_type = string_types
    if PY3:
        opts = 'r'
    else:
        opts = 'rU'

    if isinstance(f, str_type):
        if filename is None:
            filename = f
        f = open(f, opts)
        want_close = True
    else:
        if filename is None:
            filename = '<file>'
        want_close = False

    try:
        z = from_text(f, origin, rdclass, relativize, zone_factory,
                      filename, allow_include, check_origin)
    finally:
        if want_close:
            f.close()
    return z


def from_xfr(xfr, zone_factory=Zone, relativize=True, check_origin=True):
    """Convert the output of a zone transfer generator into a zone object.

    @param xfr: The xfr generator
    @type xfr: generator of dns.message.Message objects
    @param relativize: should names be relativized?  The default is True.
    It is essential that the relativize setting matches the one specified
    to dns.query.xfr().
    @type relativize: bool
    @param check_origin: should sanity checks of the origin node be done?
    The default is True.
    @type check_origin: bool
    @raises dns.zone.NoSOA: No SOA RR was found at the zone origin
    @raises dns.zone.NoNS: No NS RRset was found at the zone origin
    @rtype: dns.zone.Zone object
    """

    z = None
    for r in xfr:
        if z is None:
            if relativize:
                origin = r.origin
            else:
                origin = r.answer[0].name
            rdclass = r.answer[0].rdclass
            z = zone_factory(origin, rdclass, relativize=relativize)
        for rrset in r.answer:
            znode = z.nodes.get(rrset.name)
            if not znode:
                znode = z.node_factory()
                z.nodes[rrset.name] = znode
            zrds = znode.find_rdataset(rrset.rdclass, rrset.rdtype,
                                       rrset.covers, True)
            zrds.update_ttl(rrset.ttl)
            for rd in rrset:
                rd.choose_relativity(z.origin, relativize)
                zrds.add(rd)
    if check_origin:
        z.check_origin()
    return z
