"""Tests for other functions"""

import unittest

import idna


class OtherUTS46Tests(unittest.TestCase):

    def test_std3(self):

        self.assertEqual(idna.uts46_remap('A_', std3_rules=False), 'a_')
        self.assertRaises(idna.InvalidCodepoint, idna.uts46_remap, 'A_', std3_rules=True)

