"""Tests for TR46 code."""

import os.path
import re
import unittest

import idna

_RE_UNICODE = re.compile("\\\\u([0-9a-fA-F]{4})")
_RE_SURROGATE = re.compile("[\uD800-\uDBFF][\uDC00-\uDFFF]")
_SKIP_TESTS = [
    # These are strings that are illegal in IDNA 2008. Older versions of the UTS-46 test suite
    # had these denoted with the 'NV8' marker but this has been removed, so we need to manually
    # review exceptions and add them here to skip them as text vectors if they are invalid.
    '\U000102F7\u3002\u200D',
    '\U0001D7F5\u9681\u2BEE\uFF0E\u180D\u200C',
    '9\u9681\u2BEE.\u180D\u200C',
    '\u00DF\u200C\uAAF6\u18A5.\u22B6\u2D21\u2D16',
    'ss\u200C\uAAF6\u18A5.\u22B6\u2D21\u2D16',
    '\u00DF\u200C\uAAF6\u18A5\uFF0E\u22B6\u2D21\u2D16',
    'ss\u200C\uAAF6\u18A5\uFF0E\u22B6\u2D21\u2D16',
    '\U00010A57\u200D\u3002\u2D09\u2D15',
    '\U00010A57\u200D\uFF61\u2D09\u2D15',
    '\U0001D7CF\U0001DA19\u2E16.\u200D',
    '1\U0001DA19\u2E16.\u200D',
    '\U0001D7E04\U000E01D7\U0001D23B\uFF0E\u200D\U000102F5\u26E7\u200D',
    '84\U000E01D7\U0001D23B.\u200D\U000102F5\u26E7\u200D',
    '\u00A1', 'xn--7a', '\u19DA', 'xn--pkf', '\u2615', 'xn--53h',
    '\U0001E937.\U00010B90\U0001E881\U00010E60\u0624',
    '\U0001E937.\U00010B90\U0001E881\U00010E60\u0648\u0654',
    '\U0001E915.\U00010B90\U0001E881\U00010E60\u0648\u0654',
    '\U0001E915.\U00010B90\U0001E881\U00010E60\u0624',
    'xn--ve6h.xn--jgb1694kz0b2176a',
    '\u00DF\u3002\U000102F3\u2D0C\u0FB8',
    'ss\u3002\U000102F3\u2D0C\u0FB8',
    'ss.xn--lgd921mvv0m',
    'ss.\U000102F3\u2D0C\u0FB8',
    'xn--zca.xn--lgd921mvv0m',
    '\u00DF.\U000102F3\u2D0C\u0FB8',
    '\u00DF\uFF61\U000102F3\u2D0C\u0FB8',
    'ss\uFF61\U000102F3\u2D0C\u0FB8',
    '\u16AD\uFF61\U0001D320\u00DF\U00016AF1',
    '\u16AD\u3002\U0001D320\u00DF\U00016AF1',
    '\u16AD\u3002\U0001D320SS\U00016AF1',
    '\u16AD\u3002\U0001D320ss\U00016AF1',
    '\u16AD\u3002\U0001D320Ss\U00016AF1',
    'xn--hwe.xn--ss-ci1ub261a',
    '\u16AD.\U0001D320ss\U00016AF1',
    '\u16AD.\U0001D320SS\U00016AF1',
    '\u16AD.\U0001D320Ss\U00016AF1',
    'xn--hwe.xn--zca4946pblnc',
    '\u16AD.\U0001D320\u00DF\U00016AF1',
    '\u16AD\uFF61\U0001D320SS\U00016AF1',
    '\u16AD\uFF61\U0001D320ss\U00016AF1',
    '\u16AD\uFF61\U0001D320Ss\U00016AF1',
    '\u2D1A\U000102F8\U000E0104\u30025\uD7F6\u103A',
    'xn--ilj2659d.xn--5-dug9054m',
    '\u2D1A\U000102F8.5\uD7F6\u103A',
    '\u2D1A\U000102F8\U000E0104\u3002\U0001D7DD\uD7F6\u103A',
    'xn--9-mfs8024b.',
    '9\u9681\u2BEE.',
    'xn--ss-4epx629f.xn--ifh802b6a',
    'ss\uAAF6\u18A5.\u22B6\u2D21\u2D16',
    'xn--pt9c.xn--0kjya',
    '\U00010A57.\u2D09\u2D15',
    '\uA5F7\U00011180.\u075D\U00010A52',
    'xn--ju8a625r.xn--hpb0073k',
    '\u03C2.\u0641\u0645\u064A\U0001F79B1.',
    '\u03A3.\u0641\u0645\u064A\U0001F79B1.',
    '\u03C3.\u0641\u0645\u064A\U0001F79B1.',
    'xn--4xa.xn--1-gocmu97674d.',
    'xn--3xa.xn--1-gocmu97674d.',
    'xn--1-5bt6845n.',
    '1\U0001DA19\u2E16.',
    'xn--84-s850a.xn--59h6326e',
    '84\U0001D23B.\U000102F5\u26E7',
    'xn--r97c.',
    '\U000102F7.',

    # These appear to be errors in the test vectors. All relate to incorrectly applying
    # bidi rules across label boundaries. Appears independently confirmed
    # at http://www.alvestrand.no/pipermail/idna-update/2017-January/007946.html
    '0\u00E0.\u05D0', '0a\u0300.\u05D0', '0A\u0300.\u05D0', '0\u00C0.\u05D0', 'xn--0-sfa.xn--4db',
    '\u00E0\u02c7.\u05D0', 'a\u0300\u02c7.\u05D0', 'A\u0300\u02c7.\u05D0', '\u00C0\u02c7.\u05D0',
    'xn--0ca88g.xn--4db', '0A.\u05D0', '0a.\u05D0', '0a.xn--4db', 'c.xn--0-eha.xn--4db',
    'c.0\u00FC.\u05D0', 'c.0u\u0308.\u05D0', 'C.0U\u0308.\u05D0', 'C.0\u00DC.\u05D0',
    'C.0\u00FC.\u05D0', 'C.0\u0075\u0308.\u05D0', '\u06B6\u06DF\u3002\u2087\uA806', '\u06B6\u06DF\u30027\uA806',
    'xn--pkb6f.xn--7-x93e', '\u06B6\u06DF.7\uA806', '1.\uAC7E6.\U00010C41\u06D0',
    '1.\u1100\u1165\u11B56.\U00010C41\u06D0', '1.xn--6-945e.xn--glb1794k',
]

def unicode_fixup(string):
    """Replace backslash-u-XXXX with appropriate unicode characters."""
    return _RE_SURROGATE.sub(lambda match: chr(
        (ord(match.group(0)[0]) - 0xd800) * 0x400 +
        ord(match.group(0)[1]) - 0xdc00 + 0x10000),
        _RE_UNICODE.sub(lambda match: chr(int(match.group(1), 16)), string))

def parse_idna_test_table(inputstream):
    """Parse IdnaTestV2.txt and return a list of tuples."""
    for lineno, line in enumerate(inputstream):
        line = line.decode('utf-8').strip()
        if '#' in line:
            line = line.split('#', 1)[0]
        if not line:
            continue
        yield((lineno + 1, tuple(field.strip() for field in line.split(';'))))


class TestIdnaTest(unittest.TestCase):
    """Run one of the IdnaTestV2.txt test lines."""
    def __init__(self, lineno=None, fields=None):
        super().__init__()
        self.lineno = lineno
        self.fields = fields

    def id(self):
        return '{}.{}'.format(super().id(), self.lineno)

    def shortDescription(self):
        if not self.fields:
            return ''
        return 'IdnaTestV2.txt line {}: {}'.format(self.lineno, '; '.join(self.fields))

    def runTest(self):
        if not self.fields:
            return ''
        source, to_unicode, to_unicode_status, to_ascii, to_ascii_status, to_ascii_t, to_ascii_t_status = self.fields
        if source in _SKIP_TESTS:
            return
        if not to_unicode:
            to_unicode = source
        if not to_unicode_status:
            to_unicode_status = '[]'
        if not to_ascii:
            to_ascii = to_unicode
        if not to_ascii_status:
            to_ascii_status = to_unicode_status
        if not to_ascii_t:
            to_ascii_t = to_ascii
        if not to_ascii_t_status:
            to_ascii_t_status = to_ascii_status

        try:
            output = idna.decode(source, uts46=True, strict=True)
            if to_unicode_status != '[]':
                self.fail('decode() did not emit required error {} for {}'.format(to_unicode, repr(source)))
            self.assertEqual(output, to_unicode, 'unexpected decode() output')
        except (idna.IDNAError, UnicodeError, ValueError) as exc:
            if str(exc).startswith("Unknown"):
                raise unittest.SkipTest("Test requires support for a newer"
                    " version of Unicode than this Python supports")
            if to_unicode_status == '[]':
                raise

        try:
            output = idna.encode(source, uts46=True, strict=True).decode('ascii')
            if to_ascii_status != '[]':
                self.fail('encode() did not emit required error {} for {}'.
                    format(to_ascii_status, repr(source)))
            self.assertEqual(output, to_ascii, 'unexpected encode() output')
        except (idna.IDNAError, UnicodeError, ValueError) as exc:
            if str(exc).startswith("Unknown"):
                raise unittest.SkipTest("Test requires support for a newer"
                    " version of Unicode than this Python supports")
            if to_ascii_status == '[]':
                raise

        try:
            output = idna.encode(source, uts46=True, strict=True, transitional=True).decode('ascii')
            if to_ascii_t_status != '[]':
                self.fail('encode(transitional=True) did not emit required error {} for {}'.
                    format(to_ascii_t_status, repr(source)))
            self.assertEqual(output, to_ascii_t, 'unexpected encode() output')
        except (idna.IDNAError, UnicodeError, ValueError) as exc:
            if str(exc).startswith("Unknown"):
                raise unittest.SkipTest("Test requires support for a newer"
                    " version of Unicode than this Python supports")
            if to_ascii_t_status == '[]':
                raise


def load_tests(loader, tests, pattern):
    """Create a suite of all the individual tests."""
    suite = unittest.TestSuite()
    with open(os.path.join(os.path.dirname(__file__),
            'IdnaTestV2.txt'), 'rb') as tests_file:
        suite.addTests(TestIdnaTest(lineno, fields)
            for lineno, fields in parse_idna_test_table(tests_file))
    return suite
