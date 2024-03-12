#!/usr/bin/env python

import codecs
import sys
import unittest

import idna.codec

class IDNACodecTests(unittest.TestCase):
    
    def testCodec(self):
        pass

    def testIncrementalDecoder(self):

        # Tests derived from Python standard library test/test_codecs.py

        incremental_tests = (
            ("python.org", b"python.org"),
            ("python.org.", b"python.org."),
            ("pyth\xf6n.org", b"xn--pythn-mua.org"),
            ("pyth\xf6n.org.", b"xn--pythn-mua.org."),
        )

        for decoded, encoded in incremental_tests:
            self.assertEqual("".join(codecs.iterdecode((bytes([c]) for c in encoded), "idna")),
                             decoded)

        decoder = codecs.getincrementaldecoder("idna")()
        self.assertEqual(decoder.decode(b"xn--xam", ), "")
        self.assertEqual(decoder.decode(b"ple-9ta.o", ), "\xe4xample.")
        self.assertEqual(decoder.decode(b"rg"), "")
        self.assertEqual(decoder.decode(b"", True), "org")

        decoder.reset()
        self.assertEqual(decoder.decode(b"xn--xam", ), "")
        self.assertEqual(decoder.decode(b"ple-9ta.o", ), "\xe4xample.")
        self.assertEqual(decoder.decode(b"rg."), "org.")
        self.assertEqual(decoder.decode(b"", True), "")


    def testIncrementalEncoder(self):

        # Tests derived from Python standard library test/test_codecs.py

        incremental_tests = (
            ("python.org", b"python.org"),
            ("python.org.", b"python.org."),
            ("pyth\xf6n.org", b"xn--pythn-mua.org"),
            ("pyth\xf6n.org.", b"xn--pythn-mua.org."),
        )
        for decoded, encoded in incremental_tests:
            self.assertEqual(b"".join(codecs.iterencode(decoded, "idna")),
                             encoded)

        encoder = codecs.getincrementalencoder("idna")()
        self.assertEqual(encoder.encode("\xe4x"), b"")
        self.assertEqual(encoder.encode("ample.org"), b"xn--xample-9ta.")
        self.assertEqual(encoder.encode("", True), b"org")

        encoder.reset()
        self.assertEqual(encoder.encode("\xe4x"), b"")
        self.assertEqual(encoder.encode("ample.org."), b"xn--xample-9ta.org.")
        self.assertEqual(encoder.encode("", True), b"")

if __name__ == '__main__':
    unittest.main()
