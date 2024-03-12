import unittest
from charset_normalizer.legacy import detect


class TestDetectLegacy(unittest.TestCase):

    def test_detect_dict_keys(self):

        r = detect(
            (u'\uFEFF' + '我没有埋怨，磋砣的只是一些时间。').encode('gb18030')
        )

        with self.subTest('encoding key present'):
            self.assertIn(
                'encoding',
                r.keys()
            )

        with self.subTest('language key present'):
            self.assertIn(
                'language',
                r.keys()
            )

        with self.subTest('confidence key present'):
            self.assertIn(
                'confidence',
                r.keys()
            )

    def test_detect_dict_value_type(self):

        r = detect(
            '我没有埋怨，磋砣的只是一些时间。'.encode('utf_8')
        )

        with self.subTest('encoding instance of str'):
            self.assertIsInstance(
                r['encoding'],
                str
            )

        with self.subTest('language instance of str'):
            self.assertIsInstance(
                r['language'],
                str
            )

        with self.subTest('confidence instance of float'):
            self.assertIsInstance(
                r['confidence'],
                float
            )

    def test_detect_dict_value(self):
        r = detect(
            '我没有埋怨，磋砣的只是一些时间。'.encode('utf_32')
        )

        with self.subTest('encoding is equal to utf_32'):
            self.assertEqual(
                r['encoding'],
                'UTF-32'
            )

    def test_utf8_sig_not_striped(self):
        r = detect(
            "Hello World".encode('utf-8-sig')
        )

        with self.subTest("Verify that UTF-8-SIG is returned when using legacy detect"):
            self.assertEqual(
                r['encoding'],
                "UTF-8-SIG"
            )
