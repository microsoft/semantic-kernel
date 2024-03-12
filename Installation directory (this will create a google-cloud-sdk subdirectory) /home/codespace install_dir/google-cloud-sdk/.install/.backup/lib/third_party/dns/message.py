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

"""DNS Messages"""

from __future__ import absolute_import

from io import StringIO
import struct
import time

import dns.edns
import dns.exception
import dns.flags
import dns.name
import dns.opcode
import dns.entropy
import dns.rcode
import dns.rdata
import dns.rdataclass
import dns.rdatatype
import dns.rrset
import dns.renderer
import dns.tsig
import dns.wiredata

from ._compat import long, xrange, string_types


class ShortHeader(dns.exception.FormError):
    """The DNS packet passed to from_wire() is too short."""


class TrailingJunk(dns.exception.FormError):
    """The DNS packet passed to from_wire() has extra junk at the end of it."""


class UnknownHeaderField(dns.exception.DNSException):
    """The header field name was not recognized when converting from text
    into a message."""


class BadEDNS(dns.exception.FormError):
    """An OPT record occurred somewhere other than the start of
    the additional data section."""


class BadTSIG(dns.exception.FormError):
    """A TSIG record occurred somewhere other than the end of
    the additional data section."""


class UnknownTSIGKey(dns.exception.DNSException):
    """A TSIG with an unknown key was received."""


#: The question section number
QUESTION = 0

#: The answer section number
ANSWER = 1

#: The authority section number
AUTHORITY = 2

#: The additional section number
ADDITIONAL = 3

class Message(object):
    """A DNS message."""

    def __init__(self, id=None):
        if id is None:
            self.id = dns.entropy.random_16()
        else:
            self.id = id
        self.flags = 0
        self.question = []
        self.answer = []
        self.authority = []
        self.additional = []
        self.edns = -1
        self.ednsflags = 0
        self.payload = 0
        self.options = []
        self.request_payload = 0
        self.keyring = None
        self.keyname = None
        self.keyalgorithm = dns.tsig.default_algorithm
        self.request_mac = b''
        self.other_data = b''
        self.tsig_error = 0
        self.fudge = 300
        self.original_id = self.id
        self.mac = b''
        self.xfr = False
        self.origin = None
        self.tsig_ctx = None
        self.had_tsig = False
        self.multi = False
        self.first = True
        self.index = {}

    def __repr__(self):
        return '<DNS message, ID ' + repr(self.id) + '>'

    def __str__(self):
        return self.to_text()

    def to_text(self, origin=None, relativize=True, **kw):
        """Convert the message to text.

        The *origin*, *relativize*, and any other keyword
        arguments are passed to the RRset ``to_wire()`` method.

        Returns a ``text``.
        """

        s = StringIO()
        s.write(u'id %d\n' % self.id)
        s.write(u'opcode %s\n' %
                dns.opcode.to_text(dns.opcode.from_flags(self.flags)))
        rc = dns.rcode.from_flags(self.flags, self.ednsflags)
        s.write(u'rcode %s\n' % dns.rcode.to_text(rc))
        s.write(u'flags %s\n' % dns.flags.to_text(self.flags))
        if self.edns >= 0:
            s.write(u'edns %s\n' % self.edns)
            if self.ednsflags != 0:
                s.write(u'eflags %s\n' %
                        dns.flags.edns_to_text(self.ednsflags))
            s.write(u'payload %d\n' % self.payload)
        for opt in self.options:
            s.write(u'option %s\n' % opt.to_text())
        is_update = dns.opcode.is_update(self.flags)
        if is_update:
            s.write(u';ZONE\n')
        else:
            s.write(u';QUESTION\n')
        for rrset in self.question:
            s.write(rrset.to_text(origin, relativize, **kw))
            s.write(u'\n')
        if is_update:
            s.write(u';PREREQ\n')
        else:
            s.write(u';ANSWER\n')
        for rrset in self.answer:
            s.write(rrset.to_text(origin, relativize, **kw))
            s.write(u'\n')
        if is_update:
            s.write(u';UPDATE\n')
        else:
            s.write(u';AUTHORITY\n')
        for rrset in self.authority:
            s.write(rrset.to_text(origin, relativize, **kw))
            s.write(u'\n')
        s.write(u';ADDITIONAL\n')
        for rrset in self.additional:
            s.write(rrset.to_text(origin, relativize, **kw))
            s.write(u'\n')
        #
        # We strip off the final \n so the caller can print the result without
        # doing weird things to get around eccentricities in Python print
        # formatting
        #
        return s.getvalue()[:-1]

    def __eq__(self, other):
        """Two messages are equal if they have the same content in the
        header, question, answer, and authority sections.

        Returns a ``bool``.
        """

        if not isinstance(other, Message):
            return False
        if self.id != other.id:
            return False
        if self.flags != other.flags:
            return False
        for n in self.question:
            if n not in other.question:
                return False
        for n in other.question:
            if n not in self.question:
                return False
        for n in self.answer:
            if n not in other.answer:
                return False
        for n in other.answer:
            if n not in self.answer:
                return False
        for n in self.authority:
            if n not in other.authority:
                return False
        for n in other.authority:
            if n not in self.authority:
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_response(self, other):
        """Is this message a response to *other*?

        Returns a ``bool``.
        """

        if other.flags & dns.flags.QR == 0 or \
           self.id != other.id or \
           dns.opcode.from_flags(self.flags) != \
           dns.opcode.from_flags(other.flags):
            return False
        if dns.rcode.from_flags(other.flags, other.ednsflags) != \
                dns.rcode.NOERROR:
            return True
        if dns.opcode.is_update(self.flags):
            return True
        for n in self.question:
            if n not in other.question:
                return False
        for n in other.question:
            if n not in self.question:
                return False
        return True

    def section_number(self, section):
        """Return the "section number" of the specified section for use
        in indexing.  The question section is 0, the answer section is 1,
        the authority section is 2, and the additional section is 3.

        *section* is one of the section attributes of this message.

        Raises ``ValueError`` if the section isn't known.

        Returns an ``int``.
        """

        if section is self.question:
            return QUESTION
        elif section is self.answer:
            return ANSWER
        elif section is self.authority:
            return AUTHORITY
        elif section is self.additional:
            return ADDITIONAL
        else:
            raise ValueError('unknown section')

    def section_from_number(self, number):
        """Return the "section number" of the specified section for use
        in indexing.  The question section is 0, the answer section is 1,
        the authority section is 2, and the additional section is 3.

        *section* is one of the section attributes of this message.

        Raises ``ValueError`` if the section isn't known.

        Returns an ``int``.
        """

        if number == QUESTION:
            return self.question
        elif number == ANSWER:
            return self.answer
        elif number == AUTHORITY:
            return self.authority
        elif number == ADDITIONAL:
            return self.additional
        else:
            raise ValueError('unknown section')

    def find_rrset(self, section, name, rdclass, rdtype,
                   covers=dns.rdatatype.NONE, deleting=None, create=False,
                   force_unique=False):
        """Find the RRset with the given attributes in the specified section.

        *section*, an ``int`` section number, or one of the section
        attributes of this message.  This specifies the
        the section of the message to search.  For example::

            my_message.find_rrset(my_message.answer, name, rdclass, rdtype)
            my_message.find_rrset(dns.message.ANSWER, name, rdclass, rdtype)

        *name*, a ``dns.name.Name``, the name of the RRset.

        *rdclass*, an ``int``, the class of the RRset.

        *rdtype*, an ``int``, the type of the RRset.

        *covers*, an ``int`` or ``None``, the covers value of the RRset.
        The default is ``None``.

        *deleting*, an ``int`` or ``None``, the deleting value of the RRset.
        The default is ``None``.

        *create*, a ``bool``.  If ``True``, create the RRset if it is not found.
        The created RRset is appended to *section*.

        *force_unique*, a ``bool``.  If ``True`` and *create* is also ``True``,
        create a new RRset regardless of whether a matching RRset exists
        already.  The default is ``False``.  This is useful when creating
        DDNS Update messages, as order matters for them.

        Raises ``KeyError`` if the RRset was not found and create was
        ``False``.

        Returns a ``dns.rrset.RRset object``.
        """

        if isinstance(section, int):
            section_number = section
            section = self.section_from_number(section_number)
        else:
            section_number = self.section_number(section)
        key = (section_number, name, rdclass, rdtype, covers, deleting)
        if not force_unique:
            if self.index is not None:
                rrset = self.index.get(key)
                if rrset is not None:
                    return rrset
            else:
                for rrset in section:
                    if rrset.match(name, rdclass, rdtype, covers, deleting):
                        return rrset
        if not create:
            raise KeyError
        rrset = dns.rrset.RRset(name, rdclass, rdtype, covers, deleting)
        section.append(rrset)
        if self.index is not None:
            self.index[key] = rrset
        return rrset

    def get_rrset(self, section, name, rdclass, rdtype,
                  covers=dns.rdatatype.NONE, deleting=None, create=False,
                  force_unique=False):
        """Get the RRset with the given attributes in the specified section.

        If the RRset is not found, None is returned.

        *section*, an ``int`` section number, or one of the section
        attributes of this message.  This specifies the
        the section of the message to search.  For example::

            my_message.get_rrset(my_message.answer, name, rdclass, rdtype)
            my_message.get_rrset(dns.message.ANSWER, name, rdclass, rdtype)

        *name*, a ``dns.name.Name``, the name of the RRset.

        *rdclass*, an ``int``, the class of the RRset.

        *rdtype*, an ``int``, the type of the RRset.

        *covers*, an ``int`` or ``None``, the covers value of the RRset.
        The default is ``None``.

        *deleting*, an ``int`` or ``None``, the deleting value of the RRset.
        The default is ``None``.

        *create*, a ``bool``.  If ``True``, create the RRset if it is not found.
        The created RRset is appended to *section*.

        *force_unique*, a ``bool``.  If ``True`` and *create* is also ``True``,
        create a new RRset regardless of whether a matching RRset exists
        already.  The default is ``False``.  This is useful when creating
        DDNS Update messages, as order matters for them.

        Returns a ``dns.rrset.RRset object`` or ``None``.
        """

        try:
            rrset = self.find_rrset(section, name, rdclass, rdtype, covers,
                                    deleting, create, force_unique)
        except KeyError:
            rrset = None
        return rrset

    def to_wire(self, origin=None, max_size=0, **kw):
        """Return a string containing the message in DNS compressed wire
        format.

        Additional keyword arguments are passed to the RRset ``to_wire()``
        method.

        *origin*, a ``dns.name.Name`` or ``None``, the origin to be appended
        to any relative names.

        *max_size*, an ``int``, the maximum size of the wire format
        output; default is 0, which means "the message's request
        payload, if nonzero, or 65535".

        Raises ``dns.exception.TooBig`` if *max_size* was exceeded.

        Returns a ``binary``.
        """

        if max_size == 0:
            if self.request_payload != 0:
                max_size = self.request_payload
            else:
                max_size = 65535
        if max_size < 512:
            max_size = 512
        elif max_size > 65535:
            max_size = 65535
        r = dns.renderer.Renderer(self.id, self.flags, max_size, origin)
        for rrset in self.question:
            r.add_question(rrset.name, rrset.rdtype, rrset.rdclass)
        for rrset in self.answer:
            r.add_rrset(dns.renderer.ANSWER, rrset, **kw)
        for rrset in self.authority:
            r.add_rrset(dns.renderer.AUTHORITY, rrset, **kw)
        if self.edns >= 0:
            r.add_edns(self.edns, self.ednsflags, self.payload, self.options)
        for rrset in self.additional:
            r.add_rrset(dns.renderer.ADDITIONAL, rrset, **kw)
        r.write_header()
        if self.keyname is not None:
            r.add_tsig(self.keyname, self.keyring[self.keyname],
                       self.fudge, self.original_id, self.tsig_error,
                       self.other_data, self.request_mac,
                       self.keyalgorithm)
            self.mac = r.mac
        return r.get_wire()

    def use_tsig(self, keyring, keyname=None, fudge=300,
                 original_id=None, tsig_error=0, other_data=b'',
                 algorithm=dns.tsig.default_algorithm):
        """When sending, a TSIG signature using the specified keyring
        and keyname should be added.

        See the documentation of the Message class for a complete
        description of the keyring dictionary.

        *keyring*, a ``dict``, the TSIG keyring to use.  If a
        *keyring* is specified but a *keyname* is not, then the key
        used will be the first key in the *keyring*.  Note that the
        order of keys in a dictionary is not defined, so applications
        should supply a keyname when a keyring is used, unless they
        know the keyring contains only one key.

        *keyname*, a ``dns.name.Name`` or ``None``, the name of the TSIG key
        to use; defaults to ``None``. The key must be defined in the keyring.

        *fudge*, an ``int``, the TSIG time fudge.

        *original_id*, an ``int``, the TSIG original id.  If ``None``,
        the message's id is used.

        *tsig_error*, an ``int``, the TSIG error code.

        *other_data*, a ``binary``, the TSIG other data.

        *algorithm*, a ``dns.name.Name``, the TSIG algorithm to use.
        """

        self.keyring = keyring
        if keyname is None:
            self.keyname = list(self.keyring.keys())[0]
        else:
            if isinstance(keyname, string_types):
                keyname = dns.name.from_text(keyname)
            self.keyname = keyname
        self.keyalgorithm = algorithm
        self.fudge = fudge
        if original_id is None:
            self.original_id = self.id
        else:
            self.original_id = original_id
        self.tsig_error = tsig_error
        self.other_data = other_data

    def use_edns(self, edns=0, ednsflags=0, payload=1280, request_payload=None,
                 options=None):
        """Configure EDNS behavior.

        *edns*, an ``int``, is the EDNS level to use.  Specifying
        ``None``, ``False``, or ``-1`` means "do not use EDNS", and in this case
        the other parameters are ignored.  Specifying ``True`` is
        equivalent to specifying 0, i.e. "use EDNS0".

        *ednsflags*, an ``int``, the EDNS flag values.

        *payload*, an ``int``, is the EDNS sender's payload field, which is the
        maximum size of UDP datagram the sender can handle.  I.e. how big
        a response to this message can be.

        *request_payload*, an ``int``, is the EDNS payload size to use when
        sending this message.  If not specified, defaults to the value of
        *payload*.

        *options*, a list of ``dns.edns.Option`` objects or ``None``, the EDNS
        options.
        """

        if edns is None or edns is False:
            edns = -1
        if edns is True:
            edns = 0
        if request_payload is None:
            request_payload = payload
        if edns < 0:
            ednsflags = 0
            payload = 0
            request_payload = 0
            options = []
        else:
            # make sure the EDNS version in ednsflags agrees with edns
            ednsflags &= long(0xFF00FFFF)
            ednsflags |= (edns << 16)
            if options is None:
                options = []
        self.edns = edns
        self.ednsflags = ednsflags
        self.payload = payload
        self.options = options
        self.request_payload = request_payload

    def want_dnssec(self, wanted=True):
        """Enable or disable 'DNSSEC desired' flag in requests.

        *wanted*, a ``bool``.  If ``True``, then DNSSEC data is
        desired in the response, EDNS is enabled if required, and then
        the DO bit is set.  If ``False``, the DO bit is cleared if
        EDNS is enabled.
        """

        if wanted:
            if self.edns < 0:
                self.use_edns()
            self.ednsflags |= dns.flags.DO
        elif self.edns >= 0:
            self.ednsflags &= ~dns.flags.DO

    def rcode(self):
        """Return the rcode.

        Returns an ``int``.
        """
        return dns.rcode.from_flags(self.flags, self.ednsflags)

    def set_rcode(self, rcode):
        """Set the rcode.

        *rcode*, an ``int``, is the rcode to set.
        """
        (value, evalue) = dns.rcode.to_flags(rcode)
        self.flags &= 0xFFF0
        self.flags |= value
        self.ednsflags &= long(0x00FFFFFF)
        self.ednsflags |= evalue
        if self.ednsflags != 0 and self.edns < 0:
            self.edns = 0

    def opcode(self):
        """Return the opcode.

        Returns an ``int``.
        """
        return dns.opcode.from_flags(self.flags)

    def set_opcode(self, opcode):
        """Set the opcode.

        *opcode*, an ``int``, is the opcode to set.
        """
        self.flags &= 0x87FF
        self.flags |= dns.opcode.to_flags(opcode)


class _WireReader(object):

    """Wire format reader.

    wire: a binary, is the wire-format message.
    message: The message object being built
    current: When building a message object from wire format, this
    variable contains the offset from the beginning of wire of the next octet
    to be read.
    updating: Is the message a dynamic update?
    one_rr_per_rrset: Put each RR into its own RRset?
    ignore_trailing: Ignore trailing junk at end of request?
    zone_rdclass: The class of the zone in messages which are
    DNS dynamic updates.
    """

    def __init__(self, wire, message, question_only=False,
                 one_rr_per_rrset=False, ignore_trailing=False):
        self.wire = dns.wiredata.maybe_wrap(wire)
        self.message = message
        self.current = 0
        self.updating = False
        self.zone_rdclass = dns.rdataclass.IN
        self.question_only = question_only
        self.one_rr_per_rrset = one_rr_per_rrset
        self.ignore_trailing = ignore_trailing

    def _get_question(self, qcount):
        """Read the next *qcount* records from the wire data and add them to
        the question section.
        """

        if self.updating and qcount > 1:
            raise dns.exception.FormError

        for i in xrange(0, qcount):
            (qname, used) = dns.name.from_wire(self.wire, self.current)
            if self.message.origin is not None:
                qname = qname.relativize(self.message.origin)
            self.current = self.current + used
            (rdtype, rdclass) = \
                struct.unpack('!HH',
                              self.wire[self.current:self.current + 4])
            self.current = self.current + 4
            self.message.find_rrset(self.message.question, qname,
                                    rdclass, rdtype, create=True,
                                    force_unique=True)
            if self.updating:
                self.zone_rdclass = rdclass

    def _get_section(self, section, count):
        """Read the next I{count} records from the wire data and add them to
        the specified section.

        section: the section of the message to which to add records
        count: the number of records to read
        """

        if self.updating or self.one_rr_per_rrset:
            force_unique = True
        else:
            force_unique = False
        seen_opt = False
        for i in xrange(0, count):
            rr_start = self.current
            (name, used) = dns.name.from_wire(self.wire, self.current)
            absolute_name = name
            if self.message.origin is not None:
                name = name.relativize(self.message.origin)
            self.current = self.current + used
            (rdtype, rdclass, ttl, rdlen) = \
                struct.unpack('!HHIH',
                              self.wire[self.current:self.current + 10])
            self.current = self.current + 10
            if rdtype == dns.rdatatype.OPT:
                if section is not self.message.additional or seen_opt:
                    raise BadEDNS
                self.message.payload = rdclass
                self.message.ednsflags = ttl
                self.message.edns = (ttl & 0xff0000) >> 16
                self.message.options = []
                current = self.current
                optslen = rdlen
                while optslen > 0:
                    (otype, olen) = \
                        struct.unpack('!HH',
                                      self.wire[current:current + 4])
                    current = current + 4
                    opt = dns.edns.option_from_wire(
                        otype, self.wire, current, olen)
                    self.message.options.append(opt)
                    current = current + olen
                    optslen = optslen - 4 - olen
                seen_opt = True
            elif rdtype == dns.rdatatype.TSIG:
                if not (section is self.message.additional and
                        i == (count - 1)):
                    raise BadTSIG
                if self.message.keyring is None:
                    raise UnknownTSIGKey('got signed message without keyring')
                secret = self.message.keyring.get(absolute_name)
                if secret is None:
                    raise UnknownTSIGKey("key '%s' unknown" % name)
                self.message.keyname = absolute_name
                (self.message.keyalgorithm, self.message.mac) = \
                    dns.tsig.get_algorithm_and_mac(self.wire, self.current,
                                                   rdlen)
                self.message.tsig_ctx = \
                    dns.tsig.validate(self.wire,
                                      absolute_name,
                                      secret,
                                      int(time.time()),
                                      self.message.request_mac,
                                      rr_start,
                                      self.current,
                                      rdlen,
                                      self.message.tsig_ctx,
                                      self.message.multi,
                                      self.message.first)
                self.message.had_tsig = True
            else:
                if ttl < 0:
                    ttl = 0
                if self.updating and \
                   (rdclass == dns.rdataclass.ANY or
                        rdclass == dns.rdataclass.NONE):
                    deleting = rdclass
                    rdclass = self.zone_rdclass
                else:
                    deleting = None
                if deleting == dns.rdataclass.ANY or \
                   (deleting == dns.rdataclass.NONE and
                        section is self.message.answer):
                    covers = dns.rdatatype.NONE
                    rd = None
                else:
                    rd = dns.rdata.from_wire(rdclass, rdtype, self.wire,
                                             self.current, rdlen,
                                             self.message.origin)
                    covers = rd.covers()
                if self.message.xfr and rdtype == dns.rdatatype.SOA:
                    force_unique = True
                rrset = self.message.find_rrset(section, name,
                                                rdclass, rdtype, covers,
                                                deleting, True, force_unique)
                if rd is not None:
                    rrset.add(rd, ttl)
            self.current = self.current + rdlen

    def read(self):
        """Read a wire format DNS message and build a dns.message.Message
        object."""

        l = len(self.wire)
        if l < 12:
            raise ShortHeader
        (self.message.id, self.message.flags, qcount, ancount,
         aucount, adcount) = struct.unpack('!HHHHHH', self.wire[:12])
        self.current = 12
        if dns.opcode.is_update(self.message.flags):
            self.updating = True
        self._get_question(qcount)
        if self.question_only:
            return
        self._get_section(self.message.answer, ancount)
        self._get_section(self.message.authority, aucount)
        self._get_section(self.message.additional, adcount)
        if not self.ignore_trailing and self.current != l:
            raise TrailingJunk
        if self.message.multi and self.message.tsig_ctx and \
                not self.message.had_tsig:
            self.message.tsig_ctx.update(self.wire)


def from_wire(wire, keyring=None, request_mac=b'', xfr=False, origin=None,
              tsig_ctx=None, multi=False, first=True,
              question_only=False, one_rr_per_rrset=False,
              ignore_trailing=False):
    """Convert a DNS wire format message into a message
    object.

    *keyring*, a ``dict``, the keyring to use if the message is signed.

    *request_mac*, a ``binary``.  If the message is a response to a
    TSIG-signed request, *request_mac* should be set to the MAC of
    that request.

    *xfr*, a ``bool``, should be set to ``True`` if this message is part of
    a zone transfer.

    *origin*, a ``dns.name.Name`` or ``None``.  If the message is part
    of a zone transfer, *origin* should be the origin name of the
    zone.

    *tsig_ctx*, a ``hmac.HMAC`` objext, the ongoing TSIG context, used
    when validating zone transfers.

    *multi*, a ``bool``, should be set to ``True`` if this message
    part of a multiple message sequence.

    *first*, a ``bool``, should be set to ``True`` if this message is
    stand-alone, or the first message in a multi-message sequence.

    *question_only*, a ``bool``.  If ``True``, read only up to
    the end of the question section.

    *one_rr_per_rrset*, a ``bool``.  If ``True``, put each RR into its
    own RRset.

    *ignore_trailing*, a ``bool``.  If ``True``, ignore trailing
    junk at end of the message.

    Raises ``dns.message.ShortHeader`` if the message is less than 12 octets
    long.

    Raises ``dns.messaage.TrailingJunk`` if there were octets in the message
    past the end of the proper DNS message, and *ignore_trailing* is ``False``.

    Raises ``dns.message.BadEDNS`` if an OPT record was in the
    wrong section, or occurred more than once.

    Raises ``dns.message.BadTSIG`` if a TSIG record was not the last
    record of the additional data section.

    Returns a ``dns.message.Message``.
    """

    m = Message(id=0)
    m.keyring = keyring
    m.request_mac = request_mac
    m.xfr = xfr
    m.origin = origin
    m.tsig_ctx = tsig_ctx
    m.multi = multi
    m.first = first

    reader = _WireReader(wire, m, question_only, one_rr_per_rrset,
                         ignore_trailing)
    reader.read()

    return m


class _TextReader(object):

    """Text format reader.

    tok: the tokenizer.
    message: The message object being built.
    updating: Is the message a dynamic update?
    zone_rdclass: The class of the zone in messages which are
    DNS dynamic updates.
    last_name: The most recently read name when building a message object.
    """

    def __init__(self, text, message):
        self.message = message
        self.tok = dns.tokenizer.Tokenizer(text)
        self.last_name = None
        self.zone_rdclass = dns.rdataclass.IN
        self.updating = False

    def _header_line(self, section):
        """Process one line from the text format header section."""

        token = self.tok.get()
        what = token.value
        if what == 'id':
            self.message.id = self.tok.get_int()
        elif what == 'flags':
            while True:
                token = self.tok.get()
                if not token.is_identifier():
                    self.tok.unget(token)
                    break
                self.message.flags = self.message.flags | \
                    dns.flags.from_text(token.value)
            if dns.opcode.is_update(self.message.flags):
                self.updating = True
        elif what == 'edns':
            self.message.edns = self.tok.get_int()
            self.message.ednsflags = self.message.ednsflags | \
                (self.message.edns << 16)
        elif what == 'eflags':
            if self.message.edns < 0:
                self.message.edns = 0
            while True:
                token = self.tok.get()
                if not token.is_identifier():
                    self.tok.unget(token)
                    break
                self.message.ednsflags = self.message.ednsflags | \
                    dns.flags.edns_from_text(token.value)
        elif what == 'payload':
            self.message.payload = self.tok.get_int()
            if self.message.edns < 0:
                self.message.edns = 0
        elif what == 'opcode':
            text = self.tok.get_string()
            self.message.flags = self.message.flags | \
                dns.opcode.to_flags(dns.opcode.from_text(text))
        elif what == 'rcode':
            text = self.tok.get_string()
            self.message.set_rcode(dns.rcode.from_text(text))
        else:
            raise UnknownHeaderField
        self.tok.get_eol()

    def _question_line(self, section):
        """Process one line from the text format question section."""

        token = self.tok.get(want_leading=True)
        if not token.is_whitespace():
            self.last_name = dns.name.from_text(token.value, None)
        name = self.last_name
        token = self.tok.get()
        if not token.is_identifier():
            raise dns.exception.SyntaxError
        # Class
        try:
            rdclass = dns.rdataclass.from_text(token.value)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except dns.exception.SyntaxError:
            raise dns.exception.SyntaxError
        except Exception:
            rdclass = dns.rdataclass.IN
        # Type
        rdtype = dns.rdatatype.from_text(token.value)
        self.message.find_rrset(self.message.question, name,
                                rdclass, rdtype, create=True,
                                force_unique=True)
        if self.updating:
            self.zone_rdclass = rdclass
        self.tok.get_eol()

    def _rr_line(self, section):
        """Process one line from the text format answer, authority, or
        additional data sections.
        """

        deleting = None
        # Name
        token = self.tok.get(want_leading=True)
        if not token.is_whitespace():
            self.last_name = dns.name.from_text(token.value, None)
        name = self.last_name
        token = self.tok.get()
        if not token.is_identifier():
            raise dns.exception.SyntaxError
        # TTL
        try:
            ttl = int(token.value, 0)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
        except dns.exception.SyntaxError:
            raise dns.exception.SyntaxError
        except Exception:
            ttl = 0
        # Class
        try:
            rdclass = dns.rdataclass.from_text(token.value)
            token = self.tok.get()
            if not token.is_identifier():
                raise dns.exception.SyntaxError
            if rdclass == dns.rdataclass.ANY or rdclass == dns.rdataclass.NONE:
                deleting = rdclass
                rdclass = self.zone_rdclass
        except dns.exception.SyntaxError:
            raise dns.exception.SyntaxError
        except Exception:
            rdclass = dns.rdataclass.IN
        # Type
        rdtype = dns.rdatatype.from_text(token.value)
        token = self.tok.get()
        if not token.is_eol_or_eof():
            self.tok.unget(token)
            rd = dns.rdata.from_text(rdclass, rdtype, self.tok, None)
            covers = rd.covers()
        else:
            rd = None
            covers = dns.rdatatype.NONE
        rrset = self.message.find_rrset(section, name,
                                        rdclass, rdtype, covers,
                                        deleting, True, self.updating)
        if rd is not None:
            rrset.add(rd, ttl)

    def read(self):
        """Read a text format DNS message and build a dns.message.Message
        object."""

        line_method = self._header_line
        section = None
        while 1:
            token = self.tok.get(True, True)
            if token.is_eol_or_eof():
                break
            if token.is_comment():
                u = token.value.upper()
                if u == 'HEADER':
                    line_method = self._header_line
                elif u == 'QUESTION' or u == 'ZONE':
                    line_method = self._question_line
                    section = self.message.question
                elif u == 'ANSWER' or u == 'PREREQ':
                    line_method = self._rr_line
                    section = self.message.answer
                elif u == 'AUTHORITY' or u == 'UPDATE':
                    line_method = self._rr_line
                    section = self.message.authority
                elif u == 'ADDITIONAL':
                    line_method = self._rr_line
                    section = self.message.additional
                self.tok.get_eol()
                continue
            self.tok.unget(token)
            line_method(section)


def from_text(text):
    """Convert the text format message into a message object.

    *text*, a ``text``, the text format message.

    Raises ``dns.message.UnknownHeaderField`` if a header is unknown.

    Raises ``dns.exception.SyntaxError`` if the text is badly formed.

    Returns a ``dns.message.Message object``
    """

    # 'text' can also be a file, but we don't publish that fact
    # since it's an implementation detail.  The official file
    # interface is from_file().

    m = Message()

    reader = _TextReader(text, m)
    reader.read()

    return m


def from_file(f):
    """Read the next text format message from the specified file.

    *f*, a ``file`` or ``text``.  If *f* is text, it is treated as the
    pathname of a file to open.

    Raises ``dns.message.UnknownHeaderField`` if a header is unknown.

    Raises ``dns.exception.SyntaxError`` if the text is badly formed.

    Returns a ``dns.message.Message object``
    """

    str_type = string_types
    opts = 'rU'

    if isinstance(f, str_type):
        f = open(f, opts)
        want_close = True
    else:
        want_close = False

    try:
        m = from_text(f)
    finally:
        if want_close:
            f.close()
    return m


def make_query(qname, rdtype, rdclass=dns.rdataclass.IN, use_edns=None,
               want_dnssec=False, ednsflags=None, payload=None,
               request_payload=None, options=None):
    """Make a query message.

    The query name, type, and class may all be specified either
    as objects of the appropriate type, or as strings.

    The query will have a randomly chosen query id, and its DNS flags
    will be set to dns.flags.RD.

    qname, a ``dns.name.Name`` or ``text``, the query name.

    *rdtype*, an ``int`` or ``text``, the desired rdata type.

    *rdclass*, an ``int`` or ``text``,  the desired rdata class; the default
    is class IN.

    *use_edns*, an ``int``, ``bool`` or ``None``.  The EDNS level to use; the
    default is None (no EDNS).
    See the description of dns.message.Message.use_edns() for the possible
    values for use_edns and their meanings.

    *want_dnssec*, a ``bool``.  If ``True``, DNSSEC data is desired.

    *ednsflags*, an ``int``, the EDNS flag values.

    *payload*, an ``int``, is the EDNS sender's payload field, which is the
    maximum size of UDP datagram the sender can handle.  I.e. how big
    a response to this message can be.

    *request_payload*, an ``int``, is the EDNS payload size to use when
    sending this message.  If not specified, defaults to the value of
    *payload*.

    *options*, a list of ``dns.edns.Option`` objects or ``None``, the EDNS
    options.

    Returns a ``dns.message.Message``
    """

    if isinstance(qname, string_types):
        qname = dns.name.from_text(qname)
    if isinstance(rdtype, string_types):
        rdtype = dns.rdatatype.from_text(rdtype)
    if isinstance(rdclass, string_types):
        rdclass = dns.rdataclass.from_text(rdclass)
    m = Message()
    m.flags |= dns.flags.RD
    m.find_rrset(m.question, qname, rdclass, rdtype, create=True,
                 force_unique=True)
    # only pass keywords on to use_edns if they have been set to a
    # non-None value.  Setting a field will turn EDNS on if it hasn't
    # been configured.
    kwargs = {}
    if ednsflags is not None:
        kwargs['ednsflags'] = ednsflags
        if use_edns is None:
            use_edns = 0
    if payload is not None:
        kwargs['payload'] = payload
        if use_edns is None:
            use_edns = 0
    if request_payload is not None:
        kwargs['request_payload'] = request_payload
        if use_edns is None:
            use_edns = 0
    if options is not None:
        kwargs['options'] = options
        if use_edns is None:
            use_edns = 0
    kwargs['edns'] = use_edns
    m.use_edns(**kwargs)
    m.want_dnssec(want_dnssec)
    return m


def make_response(query, recursion_available=False, our_payload=8192,
                  fudge=300):
    """Make a message which is a response for the specified query.
    The message returned is really a response skeleton; it has all
    of the infrastructure required of a response, but none of the
    content.

    The response's question section is a shallow copy of the query's
    question section, so the query's question RRsets should not be
    changed.

    *query*, a ``dns.message.Message``, the query to respond to.

    *recursion_available*, a ``bool``, should RA be set in the response?

    *our_payload*, an ``int``, the payload size to advertise in EDNS
    responses.

    *fudge*, an ``int``, the TSIG time fudge.

    Returns a ``dns.message.Message`` object.
    """

    if query.flags & dns.flags.QR:
        raise dns.exception.FormError('specified query message is not a query')
    response = dns.message.Message(query.id)
    response.flags = dns.flags.QR | (query.flags & dns.flags.RD)
    if recursion_available:
        response.flags |= dns.flags.RA
    response.set_opcode(query.opcode())
    response.question = list(query.question)
    if query.edns >= 0:
        response.use_edns(0, 0, our_payload, query.payload)
    if query.had_tsig:
        response.use_tsig(query.keyring, query.keyname, fudge, None, 0, b'',
                          query.keyalgorithm)
        response.request_mac = query.mac
    return response
