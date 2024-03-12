#!/usr/bin/env python

import unittest

import idna


class IDNATests(unittest.TestCase):

    def setUp(self):
        self.tld_strings = [
            ['\u6d4b\u8bd5', b'xn--0zwm56d'],
            ['\u092a\u0930\u0940\u0915\u094d\u0937\u093e', b'xn--11b5bs3a9aj6g'],
            ['\ud55c\uad6d', b'xn--3e0b707e'],
            ['\u09ad\u09be\u09b0\u09a4', b'xn--45brj9c'],
            ['\u09ac\u09be\u0982\u09b2\u09be', b'xn--54b7fta0cc'],
            ['\u0438\u0441\u043f\u044b\u0442\u0430\u043d\u0438\u0435', b'xn--80akhbyknj4f'],
            ['\u0441\u0440\u0431', b'xn--90a3ac'],
            ['\ud14c\uc2a4\ud2b8', b'xn--9t4b11yi5a'],
            ['\u0b9a\u0bbf\u0b99\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0bc2\u0bb0\u0bcd', b'xn--clchc0ea0b2g2a9gcd'],
            ['\u05d8\u05e2\u05e1\u05d8', b'xn--deba0ad'],
            ['\u4e2d\u56fd', b'xn--fiqs8s'],
            ['\u4e2d\u570b', b'xn--fiqz9s'],
            ['\u0c2d\u0c3e\u0c30\u0c24\u0c4d', b'xn--fpcrj9c3d'],
            ['\u0dbd\u0d82\u0d9a\u0dcf', b'xn--fzc2c9e2c'],
            ['\u6e2c\u8a66', b'xn--g6w251d'],
            ['\u0aad\u0abe\u0ab0\u0aa4', b'xn--gecrj9c'],
            ['\u092d\u093e\u0930\u0924', b'xn--h2brj9c'],
            ['\u0622\u0632\u0645\u0627\u06cc\u0634\u06cc', b'xn--hgbk6aj7f53bba'],
            ['\u0baa\u0bb0\u0bbf\u0b9f\u0bcd\u0b9a\u0bc8', b'xn--hlcj6aya9esc7a'],
            ['\u0443\u043a\u0440', b'xn--j1amh'],
            ['\u9999\u6e2f', b'xn--j6w193g'],
            ['\u03b4\u03bf\u03ba\u03b9\u03bc\u03ae', b'xn--jxalpdlp'],
            ['\u0625\u062e\u062a\u0628\u0627\u0631', b'xn--kgbechtv'],
            ['\u53f0\u6e7e', b'xn--kprw13d'],
            ['\u53f0\u7063', b'xn--kpry57d'],
            ['\u0627\u0644\u062c\u0632\u0627\u0626\u0631', b'xn--lgbbat1ad8j'],
            ['\u0639\u0645\u0627\u0646', b'xn--mgb9awbf'],
            ['\u0627\u06cc\u0631\u0627\u0646', b'xn--mgba3a4f16a'],
            ['\u0627\u0645\u0627\u0631\u0627\u062a', b'xn--mgbaam7a8h'],
            ['\u067e\u0627\u06a9\u0633\u062a\u0627\u0646', b'xn--mgbai9azgqp6j'],
            ['\u0627\u0644\u0627\u0631\u062f\u0646', b'xn--mgbayh7gpa'],
            ['\u0628\u06be\u0627\u0631\u062a', b'xn--mgbbh1a71e'],
            ['\u0627\u0644\u0645\u063a\u0631\u0628', b'xn--mgbc0a9azcg'],
            ['\u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629', b'xn--mgberp4a5d4ar'],
            ['\u10d2\u10d4', b'xn--node'],
            ['\u0e44\u0e17\u0e22', b'xn--o3cw4h'],
            ['\u0633\u0648\u0631\u064a\u0629', b'xn--ogbpf8fl'],
            ['\u0440\u0444', b'xn--p1ai'],
            ['\u062a\u0648\u0646\u0633', b'xn--pgbs0dh'],
            ['\u0a2d\u0a3e\u0a30\u0a24', b'xn--s9brj9c'],
            ['\u0645\u0635\u0631', b'xn--wgbh1c'],
            ['\u0642\u0637\u0631', b'xn--wgbl6a'],
            ['\u0b87\u0bb2\u0b99\u0bcd\u0b95\u0bc8', b'xn--xkc2al3hye2a'],
            ['\u0b87\u0ba8\u0bcd\u0ba4\u0bbf\u0baf\u0bbe', b'xn--xkc2dl3a5ee0h'],
            ['\u65b0\u52a0\u5761', b'xn--yfro4i67o'],
            ['\u0641\u0644\u0633\u0637\u064a\u0646', b'xn--ygbi2ammx'],
            ['\u30c6\u30b9\u30c8', b'xn--zckzah'],
            ['\u049b\u0430\u0437', b'xn--80ao21a'],
            ['\u0645\u0644\u064a\u0633\u064a\u0627', b'xn--mgbx4cd0ab'],
            ['\u043c\u043e\u043d', b'xn--l1acc'],
            ['\u0633\u0648\u062f\u0627\u0646', b'xn--mgbpl2fh'],
        ]

    def testIDNTLDALabels(self):

        for (ulabel, alabel) in self.tld_strings:
            self.assertEqual(alabel, idna.alabel(ulabel))

    def testIDNTLDULabels(self):

        for (ulabel, alabel) in self.tld_strings:
            self.assertEqual(ulabel, idna.ulabel(alabel))

    def test_valid_label_length(self):

        self.assertTrue(idna.valid_label_length('a' * 63))
        self.assertFalse(idna.valid_label_length('a' * 64))
        self.assertRaises(idna.IDNAError, idna.encode, 'a' * 64)

    def test_check_bidi(self):

        l = '\u0061'
        r = '\u05d0'
        al = '\u0627'
        an = '\u0660'
        en = '\u0030'
        es = '\u002d'
        cs = '\u002c'
        et = '\u0024'
        on = '\u0021'
        bn = '\u200c'
        nsm = '\u0610'
        ws = '\u0020'

        # RFC 5893 Rule 1
        self.assertTrue(idna.check_bidi(l))
        self.assertTrue(idna.check_bidi(r))
        self.assertTrue(idna.check_bidi(al))
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, an)

        # RFC 5893 Rule 2
        self.assertTrue(idna.check_bidi(r + al))
        self.assertTrue(idna.check_bidi(r + al))
        self.assertTrue(idna.check_bidi(r + an))
        self.assertTrue(idna.check_bidi(r + en))
        self.assertTrue(idna.check_bidi(r + es + al))
        self.assertTrue(idna.check_bidi(r + cs + al))
        self.assertTrue(idna.check_bidi(r + et + al))
        self.assertTrue(idna.check_bidi(r + on + al))
        self.assertTrue(idna.check_bidi(r + bn + al))
        self.assertTrue(idna.check_bidi(r + nsm))
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, r + l)
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, r + ws)

        # RFC 5893 Rule 3
        self.assertTrue(idna.check_bidi(r + al))
        self.assertTrue(idna.check_bidi(r + en))
        self.assertTrue(idna.check_bidi(r + an))
        self.assertTrue(idna.check_bidi(r + nsm))
        self.assertTrue(idna.check_bidi(r + nsm + nsm))
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, r + on)

        # RFC 5893 Rule 4
        self.assertTrue(idna.check_bidi(r + en))
        self.assertTrue(idna.check_bidi(r + an))
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, r + en + an)
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, r + an + en)

        # RFC 5893 Rule 5
        self.assertTrue(idna.check_bidi(l + en, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + es + l, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + cs + l, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + et + l, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + on + l, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + bn + l, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + nsm, check_ltr=True))

        # RFC 5893 Rule 6
        self.assertTrue(idna.check_bidi(l + l, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + en, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + en + nsm, check_ltr=True))
        self.assertTrue(idna.check_bidi(l + en + nsm + nsm, check_ltr=True))
        self.assertRaises(idna.IDNABidiError, idna.check_bidi, l + cs, check_ltr=True)

    def test_check_initial_combiner(self):

        m = '\u0300'
        a = '\u0061'

        self.assertTrue(idna.check_initial_combiner(a))
        self.assertTrue(idna.check_initial_combiner(a + m))
        self.assertRaises(idna.IDNAError, idna.check_initial_combiner, m + a)

    def test_check_hyphen_ok(self):

        self.assertTrue(idna.check_hyphen_ok('abc'))
        self.assertTrue(idna.check_hyphen_ok('a--b'))
        self.assertRaises(idna.IDNAError, idna.check_hyphen_ok, 'aa--')
        self.assertRaises(idna.IDNAError, idna.check_hyphen_ok, 'a-')
        self.assertRaises(idna.IDNAError, idna.check_hyphen_ok, '-a')

    def test_valid_contextj(self):

        zwnj = '\u200c'
        zwj = '\u200d'
        virama = '\u094d'
        latin = '\u0061'

        # RFC 5892 Appendix A.1 (Zero Width Non-Joiner)
        self.assertFalse(idna.valid_contextj(zwnj, 0))
        self.assertFalse(idna.valid_contextj(latin + zwnj, 1)) # No preceding Virama
        self.assertTrue(idna.valid_contextj(virama + zwnj, 1)) # Preceding Virama

        # RFC 5892 Appendix A.2 (Zero Width Joiner)
        self.assertFalse(idna.valid_contextj(zwj, 0))
        self.assertFalse(idna.valid_contextj(latin + zwj, 1)) # No preceding Virama
        self.assertTrue(idna.valid_contextj(virama + zwj, 1)) # Preceding Virama

    def test_valid_contexto(self):

        latin = '\u0061'
        latin_l = '\u006c'
        greek = '\u03b1'
        hebrew = '\u05d0'
        katakana = '\u30a1'
        hiragana = '\u3041'
        han = '\u6f22'
        arabic_digit = '\u0660'
        ext_arabic_digit = '\u06f0'

        # RFC 5892 Rule A.3 (Middle Dot)
        latin_middle_dot = '\u00b7'
        self.assertTrue(idna.valid_contexto(latin_l + latin_middle_dot + latin_l, 1))
        self.assertFalse(idna.valid_contexto(latin_middle_dot + latin_l, 1))
        self.assertFalse(idna.valid_contexto(latin_l + latin_middle_dot, 0))
        self.assertFalse(idna.valid_contexto(latin_middle_dot, 0))
        self.assertFalse(idna.valid_contexto(latin_l + latin_middle_dot + latin, 1))

        # RFC 5892 Rule A.4 (Greek Lower Numeral Sign)
        glns = '\u0375'
        self.assertTrue(idna.valid_contexto(glns + greek, 0))
        self.assertFalse(idna.valid_contexto(glns + latin, 0))
        self.assertFalse(idna.valid_contexto(glns, 0))
        self.assertFalse(idna.valid_contexto(greek + glns, 1))

        # RFC 5892 Rule A.5 (Hebrew Punctuation Geresh)
        geresh = '\u05f3'
        self.assertTrue(idna.valid_contexto(hebrew + geresh, 1))
        self.assertFalse(idna.valid_contexto(latin + geresh, 1))

        # RFC 5892 Rule A.6 (Hebrew Punctuation Gershayim)
        gershayim = '\u05f4'
        self.assertTrue(idna.valid_contexto(hebrew + gershayim, 1))
        self.assertFalse(idna.valid_contexto(latin + gershayim, 1))

        # RFC 5892 Rule A.7 (Katakana Middle Dot)
        ja_middle_dot = '\u30fb'
        self.assertTrue(idna.valid_contexto(katakana + ja_middle_dot + katakana, 1))
        self.assertTrue(idna.valid_contexto(hiragana + ja_middle_dot + hiragana, 1))
        self.assertTrue(idna.valid_contexto(han + ja_middle_dot + han, 1))
        self.assertTrue(idna.valid_contexto(han + ja_middle_dot + latin, 1))
        self.assertTrue(idna.valid_contexto('\u6f22\u30fb\u5b57', 1))
        self.assertFalse(idna.valid_contexto('\u0061\u30fb\u0061', 1))

        # RFC 5892 Rule A.8 (Arabic-Indic Digits)
        self.assertTrue(idna.valid_contexto(arabic_digit + arabic_digit, 0))
        self.assertFalse(idna.valid_contexto(arabic_digit + ext_arabic_digit, 0))

        # RFC 5892 Rule A.9 (Extended Arabic-Indic Digits)
        self.assertTrue(idna.valid_contexto(ext_arabic_digit + ext_arabic_digit, 0))
        self.assertFalse(idna.valid_contexto(ext_arabic_digit + arabic_digit, 0))

    def test_encode(self):

        self.assertEqual(idna.encode('xn--zckzah.xn--zckzah'), b'xn--zckzah.xn--zckzah')
        self.assertEqual(idna.encode('\u30c6\u30b9\u30c8.xn--zckzah'), b'xn--zckzah.xn--zckzah')
        self.assertEqual(idna.encode('\u30c6\u30b9\u30c8.\u30c6\u30b9\u30c8'), b'xn--zckzah.xn--zckzah')
        self.assertEqual(idna.encode('abc.abc'), b'abc.abc')
        self.assertEqual(idna.encode('xn--zckzah.abc'), b'xn--zckzah.abc')
        self.assertEqual(idna.encode('\u30c6\u30b9\u30c8.abc'), b'xn--zckzah.abc')
        self.assertEqual(idna.encode('\u0521\u0525\u0523-\u0523\u0523-----\u0521\u0523\u0523\u0523.aa'),
                         b'xn---------90gglbagaar.aa')
        self.assertRaises(idna.IDNAError, idna.encode,
                          '\u0521\u0524\u0523-\u0523\u0523-----\u0521\u0523\u0523\u0523.aa', uts46=False)
        self.assertEqual(idna.encode('a'*63), b'a'*63)
        self.assertRaises(idna.IDNAError, idna.encode, 'a'*64)
        self.assertRaises(idna.core.InvalidCodepoint, idna.encode, '*')

    def test_decode(self):

        self.assertEqual(idna.decode('xn--zckzah.xn--zckzah'), '\u30c6\u30b9\u30c8.\u30c6\u30b9\u30c8')
        self.assertEqual(idna.decode('\u30c6\u30b9\u30c8.xn--zckzah'), '\u30c6\u30b9\u30c8.\u30c6\u30b9\u30c8')
        self.assertEqual(idna.decode('\u30c6\u30b9\u30c8.\u30c6\u30b9\u30c8'),
                         '\u30c6\u30b9\u30c8.\u30c6\u30b9\u30c8')
        self.assertEqual(idna.decode('abc.abc'), 'abc.abc')
        self.assertEqual(idna.decode('xn---------90gglbagaar.aa'),
                         '\u0521\u0525\u0523-\u0523\u0523-----\u0521\u0523\u0523\u0523.aa')
        self.assertRaises(idna.IDNAError, idna.decode, 'XN---------90GGLBAGAAC.AA')
        self.assertRaises(idna.IDNAError, idna.decode, 'xn---------90gglbagaac.aa')
        self.assertRaises(idna.IDNAError, idna.decode, 'xn--')
        self.assertRaises(idna.IDNAError, idna.decode, b'\x8d\xd2')
        self.assertRaises(idna.IDNAError, idna.decode, b'A.A.0.a.a.A.0.a.A.A.0.a.A.0A.2.a.A.A.0.a.A.0.A.a.A0.a.a.A.0.a.fB.A.A.a.A.A.B.A.A.a.A.A.B.A.A.a.A.A.0.a.A.a.a.A.A.0.a.A.0.A.a.A0.a.a.A.0.a.fB.A.A.a.A.A.B.0A.A.a.A.A.B.A.A.a.A.A.a.A.A.B.A.A.a.A.0.a.B.A.A.a.A.B.A.a.A.A.5.a.A.0.a.Ba.A.B.A.A.a.A.0.a.Xn--B.A.A.A.a')

if __name__ == '__main__':
    unittest.main()
