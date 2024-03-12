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

"""DNS Names.
"""

from io import BytesIO
import struct
import sys
import copy
import encodings.idna
try:
    import idna
    have_idna_2008 = True
except ImportError:
    have_idna_2008 = False

import dns.exception
import dns.wiredata

from ._compat import long, binary_type, text_type, unichr, maybe_decode

try:
    maxint = sys.maxint  # pylint: disable=sys-max-int
except AttributeError:
    maxint = (1 << (8 * struct.calcsize("P"))) // 2 - 1


# fullcompare() result values

#: The compared names have no relationship to each other.
NAMERELN_NONE = 0
#: the first name is a superdomain of the second.
NAMERELN_SUPERDOMAIN = 1
#: The first name is a subdomain of the second.
NAMERELN_SUBDOMAIN = 2
#: The compared names are equal.
NAMERELN_EQUAL = 3
#: The compared names have a common ancestor.
NAMERELN_COMMONANCESTOR = 4


class EmptyLabel(dns.exception.SyntaxError):
    """A DNS label is empty."""


class BadEscape(dns.exception.SyntaxError):
    """An escaped code in a text format of DNS name is invalid."""


class BadPointer(dns.exception.FormError):
    """A DNS compression pointer points forward instead of backward."""


class BadLabelType(dns.exception.FormError):
    """The label type in DNS name wire format is unknown."""


class NeedAbsoluteNameOrOrigin(dns.exception.DNSException):
    """An attempt was made to convert a non-absolute name to
    wire when there was also a non-absolute (or missing) origin."""


class NameTooLong(dns.exception.FormError):
    """A DNS name is > 255 octets long."""


class LabelTooLong(dns.exception.SyntaxError):
    """A DNS label is > 63 octets long."""


class AbsoluteConcatenation(dns.exception.DNSException):
    """An attempt was made to append anything other than the
    empty name to an absolute DNS name."""


class NoParent(dns.exception.DNSException):
    """An attempt was made to get the parent of the root name
    or the empty name."""

class NoIDNA2008(dns.exception.DNSException):
    """IDNA 2008 processing was requested but the idna module is not
    available."""


class IDNAException(dns.exception.DNSException):
    """IDNA processing raised an exception."""

    supp_kwargs = {'idna_exception'}
    fmt = "IDNA processing exception: {idna_exception}"


class IDNACodec(object):
    """Abstract base class for IDNA encoder/decoders."""

    def __init__(self):
        pass

    def encode(self, label):
        raise NotImplementedError

    def decode(self, label):
        # We do not apply any IDNA policy on decode; we just
        downcased = label.lower()
        if downcased.startswith(b'xn--'):
            try:
                label = downcased[4:].decode('punycode')
            except Exception as e:
                raise IDNAException(idna_exception=e)
        else:
            label = maybe_decode(label)
        return _escapify(label, True)


class IDNA2003Codec(IDNACodec):
    """IDNA 2003 encoder/decoder."""

    def __init__(self, strict_decode=False):
        """Initialize the IDNA 2003 encoder/decoder.

        *strict_decode* is a ``bool``. If `True`, then IDNA2003 checking
        is done when decoding.  This can cause failures if the name
        was encoded with IDNA2008.  The default is `False`.
        """

        super(IDNA2003Codec, self).__init__()
        self.strict_decode = strict_decode

    def encode(self, label):
        """Encode *label*."""

        if label == '':
            return b''
        try:
            return encodings.idna.ToASCII(label)
        except UnicodeError:
            raise LabelTooLong

    def decode(self, label):
        """Decode *label*."""
        if not self.strict_decode:
            return super(IDNA2003Codec, self).decode(label)
        if label == b'':
            return u''
        try:
            return _escapify(encodings.idna.ToUnicode(label), True)
        except Exception as e:
            raise IDNAException(idna_exception=e)


class IDNA2008Codec(IDNACodec):
    """IDNA 2008 encoder/decoder.

        *uts_46* is a ``bool``.  If True, apply Unicode IDNA
        compatibility processing as described in Unicode Technical
        Standard #46 (http://unicode.org/reports/tr46/).
        If False, do not apply the mapping.  The default is False.

        *transitional* is a ``bool``: If True, use the
        "transitional" mode described in Unicode Technical Standard
        #46.  The default is False.

        *allow_pure_ascii* is a ``bool``.  If True, then a label which
        consists of only ASCII characters is allowed.  This is less
        strict than regular IDNA 2008, but is also necessary for mixed
        names, e.g. a name with starting with "_sip._tcp." and ending
        in an IDN suffix which would otherwise be disallowed.  The
        default is False.

        *strict_decode* is a ``bool``: If True, then IDNA2008 checking
        is done when decoding.  This can cause failures if the name
        was encoded with IDNA2003.  The default is False.
        """

    def __init__(self, uts_46=False, transitional=False,
                 allow_pure_ascii=False, strict_decode=False):
        """Initialize the IDNA 2008 encoder/decoder."""
        super(IDNA2008Codec, self).__init__()
        self.uts_46 = uts_46
        self.transitional = transitional
        self.allow_pure_ascii = allow_pure_ascii
        self.strict_decode = strict_decode

    def is_all_ascii(self, label):
        for c in label:
            if ord(c) > 0x7f:
                return False
        return True

    def encode(self, label):
        if label == '':
            return b''
        if self.allow_pure_ascii and self.is_all_ascii(label):
            return label.encode('ascii')
        if not have_idna_2008:
            raise NoIDNA2008
        try:
            if self.uts_46:
                label = idna.uts46_remap(label, False, self.transitional)
            return idna.alabel(label)
        except idna.IDNAError as e:
            raise IDNAException(idna_exception=e)

    def decode(self, label):
        if not self.strict_decode:
            return super(IDNA2008Codec, self).decode(label)
        if label == b'':
            return u''
        if not have_idna_2008:
            raise NoIDNA2008
        try:
            if self.uts_46:
                label = idna.uts46_remap(label, False, False)
            return _escapify(idna.ulabel(label), True)
        except idna.IDNAError as e:
            raise IDNAException(idna_exception=e)

_escaped = bytearray(b'"().;\\@$')

IDNA_2003_Practical = IDNA2003Codec(False)
IDNA_2003_Strict = IDNA2003Codec(True)
IDNA_2003 = IDNA_2003_Practical
IDNA_2008_Practical = IDNA2008Codec(True, False, True, False)
IDNA_2008_UTS_46 = IDNA2008Codec(True, False, False, False)
IDNA_2008_Strict = IDNA2008Codec(False, False, False, True)
IDNA_2008_Transitional = IDNA2008Codec(True, True, False, False)
IDNA_2008 = IDNA_2008_Practical

def _escapify(label, unicode_mode=False):
    """Escape the characters in label which need it.
    @param unicode_mode: escapify only special and whitespace (<= 0x20)
    characters
    @returns: the escaped string
    @rtype: string"""
    if not unicode_mode:
        text = ''
        if isinstance(label, text_type):
            label = label.encode()
        for c in bytearray(label):
            if c in _escaped:
                text += '\\' + chr(c)
            elif c > 0x20 and c < 0x7F:
                text += chr(c)
            else:
                text += '\\%03d' % c
        return text.encode()

    text = u''
    if isinstance(label, binary_type):
        label = label.decode()
    for c in label:
        if c > u'\x20' and c < u'\x7f':
            text += c
        else:
            if c >= u'\x7f':
                text += c
            else:
                text += u'\\%03d' % ord(c)
    return text

def _validate_labels(labels):
    """Check for empty labels in the middle of a label sequence,
    labels that are too long, and for too many labels.

    Raises ``dns.name.NameTooLong`` if the name as a whole is too long.

    Raises ``dns.name.EmptyLabel`` if a label is empty (i.e. the root
    label) and appears in a position other than the end of the label
    sequence

    """

    l = len(labels)
    total = 0
    i = -1
    j = 0
    for label in labels:
        ll = len(label)
        total += ll + 1
        if ll > 63:
            raise LabelTooLong
        if i < 0 and label == b'':
            i = j
        j += 1
    if total > 255:
        raise NameTooLong
    if i >= 0 and i != l - 1:
        raise EmptyLabel


def _maybe_convert_to_binary(label):
    """If label is ``text``, convert it to ``binary``.  If it is already
    ``binary`` just return it.

    """

    if isinstance(label, binary_type):
        return label
    if isinstance(label, text_type):
        return label.encode()
    raise ValueError


class Name(object):

    """A DNS name.

    The dns.name.Name class represents a DNS name as a tuple of
    labels.  Each label is a `binary` in DNS wire format.  Instances
    of the class are immutable.
    """

    __slots__ = ['labels']

    def __init__(self, labels):
        """*labels* is any iterable whose values are ``text`` or ``binary``.
        """

        labels = [_maybe_convert_to_binary(x) for x in labels]
        super(Name, self).__setattr__('labels', tuple(labels))
        _validate_labels(self.labels)

    def __setattr__(self, name, value):
        # Names are immutable
        raise TypeError("object doesn't support attribute assignment")

    def __copy__(self):
        return Name(self.labels)

    def __deepcopy__(self, memo):
        return Name(copy.deepcopy(self.labels, memo))

    def __getstate__(self):
        # Names can be pickled
        return {'labels': self.labels}

    def __setstate__(self, state):
        super(Name, self).__setattr__('labels', state['labels'])
        _validate_labels(self.labels)

    def is_absolute(self):
        """Is the most significant label of this name the root label?

        Returns a ``bool``.
        """

        return len(self.labels) > 0 and self.labels[-1] == b''

    def is_wild(self):
        """Is this name wild?  (I.e. Is the least significant label '*'?)

        Returns a ``bool``.
        """

        return len(self.labels) > 0 and self.labels[0] == b'*'

    def __hash__(self):
        """Return a case-insensitive hash of the name.

        Returns an ``int``.
        """

        h = long(0)
        for label in self.labels:
            for c in bytearray(label.lower()):
                h += (h << 3) + c
        return int(h % maxint)

    def fullcompare(self, other):
        """Compare two names, returning a 3-tuple
        ``(relation, order, nlabels)``.

        *relation* describes the relation ship between the names,
        and is one of: ``dns.name.NAMERELN_NONE``,
        ``dns.name.NAMERELN_SUPERDOMAIN``, ``dns.name.NAMERELN_SUBDOMAIN``,
        ``dns.name.NAMERELN_EQUAL``, or ``dns.name.NAMERELN_COMMONANCESTOR``.

        *order* is < 0 if *self* < *other*, > 0 if *self* > *other*, and ==
        0 if *self* == *other*.  A relative name is always less than an
        absolute name.  If both names have the same relativity, then
        the DNSSEC order relation is used to order them.

        *nlabels* is the number of significant labels that the two names
        have in common.

        Here are some examples.  Names ending in "." are absolute names,
        those not ending in "." are relative names.

        =============  =============  ===========  =====  =======
        self           other          relation     order  nlabels
        =============  =============  ===========  =====  =======
        www.example.   www.example.   equal        0      3
        www.example.   example.       subdomain    > 0    2
        example.       www.example.   superdomain  < 0    2
        example1.com.  example2.com.  common anc.  < 0    2
        example1       example2.      none         < 0    0
        example1.      example2       none         > 0    0
        =============  =============  ===========  =====  =======
        """

        sabs = self.is_absolute()
        oabs = other.is_absolute()
        if sabs != oabs:
            if sabs:
                return (NAMERELN_NONE, 1, 0)
            else:
                return (NAMERELN_NONE, -1, 0)
        l1 = len(self.labels)
        l2 = len(other.labels)
        ldiff = l1 - l2
        if ldiff < 0:
            l = l1
        else:
            l = l2

        order = 0
        nlabels = 0
        namereln = NAMERELN_NONE
        while l > 0:
            l -= 1
            l1 -= 1
            l2 -= 1
            label1 = self.labels[l1].lower()
            label2 = other.labels[l2].lower()
            if label1 < label2:
                order = -1
                if nlabels > 0:
                    namereln = NAMERELN_COMMONANCESTOR
                return (namereln, order, nlabels)
            elif label1 > label2:
                order = 1
                if nlabels > 0:
                    namereln = NAMERELN_COMMONANCESTOR
                return (namereln, order, nlabels)
            nlabels += 1
        order = ldiff
        if ldiff < 0:
            namereln = NAMERELN_SUPERDOMAIN
        elif ldiff > 0:
            namereln = NAMERELN_SUBDOMAIN
        else:
            namereln = NAMERELN_EQUAL
        return (namereln, order, nlabels)

    def is_subdomain(self, other):
        """Is self a subdomain of other?

        Note that the notion of subdomain includes equality, e.g.
        "dnpython.org" is a subdomain of itself.

        Returns a ``bool``.
        """

        (nr, o, nl) = self.fullcompare(other)
        if nr == NAMERELN_SUBDOMAIN or nr == NAMERELN_EQUAL:
            return True
        return False

    def is_superdomain(self, other):
        """Is self a superdomain of other?

        Note that the notion of superdomain includes equality, e.g.
        "dnpython.org" is a superdomain of itself.

        Returns a ``bool``.
        """

        (nr, o, nl) = self.fullcompare(other)
        if nr == NAMERELN_SUPERDOMAIN or nr == NAMERELN_EQUAL:
            return True
        return False

    def canonicalize(self):
        """Return a name which is equal to the current name, but is in
        DNSSEC canonical form.
        """

        return Name([x.lower() for x in self.labels])

    def __eq__(self, other):
        if isinstance(other, Name):
            return self.fullcompare(other)[1] == 0
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, Name):
            return self.fullcompare(other)[1] != 0
        else:
            return True

    def __lt__(self, other):
        if isinstance(other, Name):
            return self.fullcompare(other)[1] < 0
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, Name):
            return self.fullcompare(other)[1] <= 0
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Name):
            return self.fullcompare(other)[1] >= 0
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Name):
            return self.fullcompare(other)[1] > 0
        else:
            return NotImplemented

    def __repr__(self):
        return '<DNS name ' + self.__str__() + '>'

    def __str__(self):
        return self.to_text(False)

    def to_text(self, omit_final_dot=False):
        """Convert name to DNS text format.

        *omit_final_dot* is a ``bool``.  If True, don't emit the final
        dot (denoting the root label) for absolute names.  The default
        is False.

        Returns a ``text``.
        """

        if len(self.labels) == 0:
            return maybe_decode(b'@')
        if len(self.labels) == 1 and self.labels[0] == b'':
            return maybe_decode(b'.')
        if omit_final_dot and self.is_absolute():
            l = self.labels[:-1]
        else:
            l = self.labels
        s = b'.'.join(map(_escapify, l))
        return maybe_decode(s)

    def to_unicode(self, omit_final_dot=False, idna_codec=None):
        """Convert name to Unicode text format.

        IDN ACE labels are converted to Unicode.

        *omit_final_dot* is a ``bool``.  If True, don't emit the final
        dot (denoting the root label) for absolute names.  The default
        is False.
        *idna_codec* specifies the IDNA encoder/decoder.  If None, the
        dns.name.IDNA_2003_Practical encoder/decoder is used.
        The IDNA_2003_Practical decoder does
        not impose any policy, it just decodes punycode, so if you
        don't want checking for compliance, you can use this decoder
        for IDNA2008 as well.

        Returns a ``text``.
        """

        if len(self.labels) == 0:
            return u'@'
        if len(self.labels) == 1 and self.labels[0] == b'':
            return u'.'
        if omit_final_dot and self.is_absolute():
            l = self.labels[:-1]
        else:
            l = self.labels
        if idna_codec is None:
            idna_codec = IDNA_2003_Practical
        return u'.'.join([idna_codec.decode(x) for x in l])

    def to_digestable(self, origin=None):
        """Convert name to a format suitable for digesting in hashes.

        The name is canonicalized and converted to uncompressed wire
        format.  All names in wire format are absolute.  If the name
        is a relative name, then an origin must be supplied.

        *origin* is a ``dns.name.Name`` or ``None``.  If the name is
        relative and origin is not ``None``, then origin will be appended
        to the name.

        Raises ``dns.name.NeedAbsoluteNameOrOrigin`` if the name is
        relative and no origin was provided.

        Returns a ``binary``.
        """

        if not self.is_absolute():
            if origin is None or not origin.is_absolute():
                raise NeedAbsoluteNameOrOrigin
            labels = list(self.labels)
            labels.extend(list(origin.labels))
        else:
            labels = self.labels
        dlabels = [struct.pack('!B%ds' % len(x), len(x), x.lower())
                   for x in labels]
        return b''.join(dlabels)

    def to_wire(self, file=None, compress=None, origin=None):
        """Convert name to wire format, possibly compressing it.

        *file* is the file where the name is emitted (typically a
        BytesIO file).  If ``None`` (the default), a ``binary``
        containing the wire name will be returned.

        *compress*, a ``dict``, is the compression table to use.  If
        ``None`` (the default), names will not be compressed.

        *origin* is a ``dns.name.Name`` or ``None``.  If the name is
        relative and origin is not ``None``, then *origin* will be appended
        to it.

        Raises ``dns.name.NeedAbsoluteNameOrOrigin`` if the name is
        relative and no origin was provided.

        Returns a ``binary`` or ``None``.
        """

        if file is None:
            file = BytesIO()
            want_return = True
        else:
            want_return = False

        if not self.is_absolute():
            if origin is None or not origin.is_absolute():
                raise NeedAbsoluteNameOrOrigin
            labels = list(self.labels)
            labels.extend(list(origin.labels))
        else:
            labels = self.labels
        i = 0
        for label in labels:
            n = Name(labels[i:])
            i += 1
            if compress is not None:
                pos = compress.get(n)
            else:
                pos = None
            if pos is not None:
                value = 0xc000 + pos
                s = struct.pack('!H', value)
                file.write(s)
                break
            else:
                if compress is not None and len(n) > 1:
                    pos = file.tell()
                    if pos <= 0x3fff:
                        compress[n] = pos
                l = len(label)
                file.write(struct.pack('!B', l))
                if l > 0:
                    file.write(label)
        if want_return:
            return file.getvalue()

    def __len__(self):
        """The length of the name (in labels).

        Returns an ``int``.
        """

        return len(self.labels)

    def __getitem__(self, index):
        return self.labels[index]

    def __add__(self, other):
        return self.concatenate(other)

    def __sub__(self, other):
        return self.relativize(other)

    def split(self, depth):
        """Split a name into a prefix and suffix names at the specified depth.

        *depth* is an ``int`` specifying the number of labels in the suffix

        Raises ``ValueError`` if *depth* was not >= 0 and <= the length of the
        name.

        Returns the tuple ``(prefix, suffix)``.
        """

        l = len(self.labels)
        if depth == 0:
            return (self, dns.name.empty)
        elif depth == l:
            return (dns.name.empty, self)
        elif depth < 0 or depth > l:
            raise ValueError(
                'depth must be >= 0 and <= the length of the name')
        return (Name(self[: -depth]), Name(self[-depth:]))

    def concatenate(self, other):
        """Return a new name which is the concatenation of self and other.

        Raises ``dns.name.AbsoluteConcatenation`` if the name is
        absolute and *other* is not the empty name.

        Returns a ``dns.name.Name``.
        """

        if self.is_absolute() and len(other) > 0:
            raise AbsoluteConcatenation
        labels = list(self.labels)
        labels.extend(list(other.labels))
        return Name(labels)

    def relativize(self, origin):
        """If the name is a subdomain of *origin*, return a new name which is
        the name relative to origin.  Otherwise return the name.

        For example, relativizing ``www.dnspython.org.`` to origin
        ``dnspython.org.`` returns the name ``www``.  Relativizing ``example.``
        to origin ``dnspython.org.`` returns ``example.``.

        Returns a ``dns.name.Name``.
        """

        if origin is not None and self.is_subdomain(origin):
            return Name(self[: -len(origin)])
        else:
            return self

    def derelativize(self, origin):
        """If the name is a relative name, return a new name which is the
        concatenation of the name and origin.  Otherwise return the name.

        For example, derelativizing ``www`` to origin ``dnspython.org.``
        returns the name ``www.dnspython.org.``.  Derelativizing ``example.``
        to origin ``dnspython.org.`` returns ``example.``.

        Returns a ``dns.name.Name``.
        """

        if not self.is_absolute():
            return self.concatenate(origin)
        else:
            return self

    def choose_relativity(self, origin=None, relativize=True):
        """Return a name with the relativity desired by the caller.

        If *origin* is ``None``, then the name is returned.
        Otherwise, if *relativize* is ``True`` the name is
        relativized, and if *relativize* is ``False`` the name is
        derelativized.

        Returns a ``dns.name.Name``.
        """

        if origin:
            if relativize:
                return self.relativize(origin)
            else:
                return self.derelativize(origin)
        else:
            return self

    def parent(self):
        """Return the parent of the name.

        For example, the parent of ``www.dnspython.org.`` is ``dnspython.org``.

        Raises ``dns.name.NoParent`` if the name is either the root name or the
        empty name, and thus has no parent.

        Returns a ``dns.name.Name``.
        """

        if self == root or self == empty:
            raise NoParent
        return Name(self.labels[1:])

#: The root name, '.'
root = Name([b''])

#: The empty name.
empty = Name([])

def from_unicode(text, origin=root, idna_codec=None):
    """Convert unicode text into a Name object.

    Labels are encoded in IDN ACE form according to rules specified by
    the IDNA codec.

    *text*, a ``text``, is the text to convert into a name.

    *origin*, a ``dns.name.Name``, specifies the origin to
    append to non-absolute names.  The default is the root name.

    *idna_codec*, a ``dns.name.IDNACodec``, specifies the IDNA
    encoder/decoder.  If ``None``, the default IDNA 2003 encoder/decoder
    is used.

    Returns a ``dns.name.Name``.
    """

    if not isinstance(text, text_type):
        raise ValueError("input to from_unicode() must be a unicode string")
    if not (origin is None or isinstance(origin, Name)):
        raise ValueError("origin must be a Name or None")
    labels = []
    label = u''
    escaping = False
    edigits = 0
    total = 0
    if idna_codec is None:
        idna_codec = IDNA_2003
    if text == u'@':
        text = u''
    if text:
        if text == u'.':
            return Name([b''])        # no Unicode "u" on this constant!
        for c in text:
            if escaping:
                if edigits == 0:
                    if c.isdigit():
                        total = int(c)
                        edigits += 1
                    else:
                        label += c
                        escaping = False
                else:
                    if not c.isdigit():
                        raise BadEscape
                    total *= 10
                    total += int(c)
                    edigits += 1
                    if edigits == 3:
                        escaping = False
                        label += unichr(total)
            elif c in [u'.', u'\u3002', u'\uff0e', u'\uff61']:
                if len(label) == 0:
                    raise EmptyLabel
                labels.append(idna_codec.encode(label))
                label = u''
            elif c == u'\\':
                escaping = True
                edigits = 0
                total = 0
            else:
                label += c
        if escaping:
            raise BadEscape
        if len(label) > 0:
            labels.append(idna_codec.encode(label))
        else:
            labels.append(b'')

    if (len(labels) == 0 or labels[-1] != b'') and origin is not None:
        labels.extend(list(origin.labels))
    return Name(labels)


def from_text(text, origin=root, idna_codec=None):
    """Convert text into a Name object.

    *text*, a ``text``, is the text to convert into a name.

    *origin*, a ``dns.name.Name``, specifies the origin to
    append to non-absolute names.  The default is the root name.

    *idna_codec*, a ``dns.name.IDNACodec``, specifies the IDNA
    encoder/decoder.  If ``None``, the default IDNA 2003 encoder/decoder
    is used.

    Returns a ``dns.name.Name``.
    """

    if isinstance(text, text_type):
        return from_unicode(text, origin, idna_codec)
    if not isinstance(text, binary_type):
        raise ValueError("input to from_text() must be a string")
    if not (origin is None or isinstance(origin, Name)):
        raise ValueError("origin must be a Name or None")
    labels = []
    label = b''
    escaping = False
    edigits = 0
    total = 0
    if text == b'@':
        text = b''
    if text:
        if text == b'.':
            return Name([b''])
        for c in bytearray(text):
            byte_ = struct.pack('!B', c)
            if escaping:
                if edigits == 0:
                    if byte_.isdigit():
                        total = int(byte_)
                        edigits += 1
                    else:
                        label += byte_
                        escaping = False
                else:
                    if not byte_.isdigit():
                        raise BadEscape
                    total *= 10
                    total += int(byte_)
                    edigits += 1
                    if edigits == 3:
                        escaping = False
                        label += struct.pack('!B', total)
            elif byte_ == b'.':
                if len(label) == 0:
                    raise EmptyLabel
                labels.append(label)
                label = b''
            elif byte_ == b'\\':
                escaping = True
                edigits = 0
                total = 0
            else:
                label += byte_
        if escaping:
            raise BadEscape
        if len(label) > 0:
            labels.append(label)
        else:
            labels.append(b'')
    if (len(labels) == 0 or labels[-1] != b'') and origin is not None:
        labels.extend(list(origin.labels))
    return Name(labels)


def from_wire(message, current):
    """Convert possibly compressed wire format into a Name.

    *message* is a ``binary`` containing an entire DNS message in DNS
    wire form.

    *current*, an ``int``, is the offset of the beginning of the name
    from the start of the message

    Raises ``dns.name.BadPointer`` if a compression pointer did not
    point backwards in the message.

    Raises ``dns.name.BadLabelType`` if an invalid label type was encountered.

    Returns a ``(dns.name.Name, int)`` tuple consisting of the name
    that was read and the number of bytes of the wire format message
    which were consumed reading it.
    """

    if not isinstance(message, binary_type):
        raise ValueError("input to from_wire() must be a byte string")
    message = dns.wiredata.maybe_wrap(message)
    labels = []
    biggest_pointer = current
    hops = 0
    count = message[current]
    current += 1
    cused = 1
    while count != 0:
        if count < 64:
            labels.append(message[current: current + count].unwrap())
            current += count
            if hops == 0:
                cused += count
        elif count >= 192:
            current = (count & 0x3f) * 256 + message[current]
            if hops == 0:
                cused += 1
            if current >= biggest_pointer:
                raise BadPointer
            biggest_pointer = current
            hops += 1
        else:
            raise BadLabelType
        count = message[current]
        current += 1
        if hops == 0:
            cused += 1
    labels.append('')
    return (Name(labels), cused)
