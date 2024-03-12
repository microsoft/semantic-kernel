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

"""Help for building DNS wire format messages"""

from io import BytesIO
import struct
import random
import time

import dns.exception
import dns.tsig
from ._compat import long


QUESTION = 0
ANSWER = 1
AUTHORITY = 2
ADDITIONAL = 3


class Renderer(object):
    """Helper class for building DNS wire-format messages.

    Most applications can use the higher-level L{dns.message.Message}
    class and its to_wire() method to generate wire-format messages.
    This class is for those applications which need finer control
    over the generation of messages.

    Typical use::

        r = dns.renderer.Renderer(id=1, flags=0x80, max_size=512)
        r.add_question(qname, qtype, qclass)
        r.add_rrset(dns.renderer.ANSWER, rrset_1)
        r.add_rrset(dns.renderer.ANSWER, rrset_2)
        r.add_rrset(dns.renderer.AUTHORITY, ns_rrset)
        r.add_edns(0, 0, 4096)
        r.add_rrset(dns.renderer.ADDTIONAL, ad_rrset_1)
        r.add_rrset(dns.renderer.ADDTIONAL, ad_rrset_2)
        r.write_header()
        r.add_tsig(keyname, secret, 300, 1, 0, '', request_mac)
        wire = r.get_wire()

    output, a BytesIO, where rendering is written

    id: the message id

    flags: the message flags

    max_size: the maximum size of the message

    origin: the origin to use when rendering relative names

    compress: the compression table

    section: an int, the section currently being rendered

    counts: list of the number of RRs in each section

    mac: the MAC of the rendered message (if TSIG was used)
    """

    def __init__(self, id=None, flags=0, max_size=65535, origin=None):
        """Initialize a new renderer."""

        self.output = BytesIO()
        if id is None:
            self.id = random.randint(0, 65535)
        else:
            self.id = id
        self.flags = flags
        self.max_size = max_size
        self.origin = origin
        self.compress = {}
        self.section = QUESTION
        self.counts = [0, 0, 0, 0]
        self.output.write(b'\x00' * 12)
        self.mac = ''

    def _rollback(self, where):
        """Truncate the output buffer at offset *where*, and remove any
        compression table entries that pointed beyond the truncation
        point.
        """

        self.output.seek(where)
        self.output.truncate()
        keys_to_delete = []
        for k, v in self.compress.items():
            if v >= where:
                keys_to_delete.append(k)
        for k in keys_to_delete:
            del self.compress[k]

    def _set_section(self, section):
        """Set the renderer's current section.

        Sections must be rendered order: QUESTION, ANSWER, AUTHORITY,
        ADDITIONAL.  Sections may be empty.

        Raises dns.exception.FormError if an attempt was made to set
        a section value less than the current section.
        """

        if self.section != section:
            if self.section > section:
                raise dns.exception.FormError
            self.section = section

    def add_question(self, qname, rdtype, rdclass=dns.rdataclass.IN):
        """Add a question to the message."""

        self._set_section(QUESTION)
        before = self.output.tell()
        qname.to_wire(self.output, self.compress, self.origin)
        self.output.write(struct.pack("!HH", rdtype, rdclass))
        after = self.output.tell()
        if after >= self.max_size:
            self._rollback(before)
            raise dns.exception.TooBig
        self.counts[QUESTION] += 1

    def add_rrset(self, section, rrset, **kw):
        """Add the rrset to the specified section.

        Any keyword arguments are passed on to the rdataset's to_wire()
        routine.
        """

        self._set_section(section)
        before = self.output.tell()
        n = rrset.to_wire(self.output, self.compress, self.origin, **kw)
        after = self.output.tell()
        if after >= self.max_size:
            self._rollback(before)
            raise dns.exception.TooBig
        self.counts[section] += n

    def add_rdataset(self, section, name, rdataset, **kw):
        """Add the rdataset to the specified section, using the specified
        name as the owner name.

        Any keyword arguments are passed on to the rdataset's to_wire()
        routine.
        """

        self._set_section(section)
        before = self.output.tell()
        n = rdataset.to_wire(name, self.output, self.compress, self.origin,
                             **kw)
        after = self.output.tell()
        if after >= self.max_size:
            self._rollback(before)
            raise dns.exception.TooBig
        self.counts[section] += n

    def add_edns(self, edns, ednsflags, payload, options=None):
        """Add an EDNS OPT record to the message."""

        # make sure the EDNS version in ednsflags agrees with edns
        ednsflags &= long(0xFF00FFFF)
        ednsflags |= (edns << 16)
        self._set_section(ADDITIONAL)
        before = self.output.tell()
        self.output.write(struct.pack('!BHHIH', 0, dns.rdatatype.OPT, payload,
                                      ednsflags, 0))
        if options is not None:
            lstart = self.output.tell()
            for opt in options:
                stuff = struct.pack("!HH", opt.otype, 0)
                self.output.write(stuff)
                start = self.output.tell()
                opt.to_wire(self.output)
                end = self.output.tell()
                assert end - start < 65536
                self.output.seek(start - 2)
                stuff = struct.pack("!H", end - start)
                self.output.write(stuff)
                self.output.seek(0, 2)
            lend = self.output.tell()
            assert lend - lstart < 65536
            self.output.seek(lstart - 2)
            stuff = struct.pack("!H", lend - lstart)
            self.output.write(stuff)
            self.output.seek(0, 2)
        after = self.output.tell()
        if after >= self.max_size:
            self._rollback(before)
            raise dns.exception.TooBig
        self.counts[ADDITIONAL] += 1

    def add_tsig(self, keyname, secret, fudge, id, tsig_error, other_data,
                 request_mac, algorithm=dns.tsig.default_algorithm):
        """Add a TSIG signature to the message."""

        s = self.output.getvalue()
        (tsig_rdata, self.mac, ctx) = dns.tsig.sign(s,
                                                    keyname,
                                                    secret,
                                                    int(time.time()),
                                                    fudge,
                                                    id,
                                                    tsig_error,
                                                    other_data,
                                                    request_mac,
                                                    algorithm=algorithm)
        self._write_tsig(tsig_rdata, keyname)

    def add_multi_tsig(self, ctx, keyname, secret, fudge, id, tsig_error,
                       other_data, request_mac,
                       algorithm=dns.tsig.default_algorithm):
        """Add a TSIG signature to the message. Unlike add_tsig(), this can be
        used for a series of consecutive DNS envelopes, e.g. for a zone
        transfer over TCP [RFC2845, 4.4].

        For the first message in the sequence, give ctx=None. For each
        subsequent message, give the ctx that was returned from the
        add_multi_tsig() call for the previous message."""

        s = self.output.getvalue()
        (tsig_rdata, self.mac, ctx) = dns.tsig.sign(s,
                                                    keyname,
                                                    secret,
                                                    int(time.time()),
                                                    fudge,
                                                    id,
                                                    tsig_error,
                                                    other_data,
                                                    request_mac,
                                                    ctx=ctx,
                                                    first=ctx is None,
                                                    multi=True,
                                                    algorithm=algorithm)
        self._write_tsig(tsig_rdata, keyname)
        return ctx

    def _write_tsig(self, tsig_rdata, keyname):
        self._set_section(ADDITIONAL)
        before = self.output.tell()

        keyname.to_wire(self.output, self.compress, self.origin)
        self.output.write(struct.pack('!HHIH', dns.rdatatype.TSIG,
                                      dns.rdataclass.ANY, 0, 0))
        rdata_start = self.output.tell()
        self.output.write(tsig_rdata)

        after = self.output.tell()
        assert after - rdata_start < 65536
        if after >= self.max_size:
            self._rollback(before)
            raise dns.exception.TooBig

        self.output.seek(rdata_start - 2)
        self.output.write(struct.pack('!H', after - rdata_start))
        self.counts[ADDITIONAL] += 1
        self.output.seek(10)
        self.output.write(struct.pack('!H', self.counts[ADDITIONAL]))
        self.output.seek(0, 2)

    def write_header(self):
        """Write the DNS message header.

        Writing the DNS message header is done after all sections
        have been rendered, but before the optional TSIG signature
        is added.
        """

        self.output.seek(0)
        self.output.write(struct.pack('!HHHHHH', self.id, self.flags,
                                      self.counts[0], self.counts[1],
                                      self.counts[2], self.counts[3]))
        self.output.seek(0, 2)

    def get_wire(self):
        """Return the wire format message."""

        return self.output.getvalue()
