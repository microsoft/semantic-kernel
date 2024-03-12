#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
import sys

from pyasn1.codec.der import decoder as der_decoder
from pyasn1.codec.der import encoder as der_encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc2511

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class CertificateReqTestCase(unittest.TestCase):
    pem_text = """\
MIIBozCCAZ8wggEFAgUAwTnj2jCByoABAqURMA8xDTALBgNVBAMTBHVzZXKmgZ8w
DQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAJ6ZQ2cYbn/lFsmBOlRltbRbFQUvvE0Q
nbopOu1kC7Bmaaz7QTx8nxeiHi4m7uxCbGGxHNoGCt7EmdG8eZUBNAcHyGlXrJdm
0z3/uNEGiBHq+xB8FnFJCA5EIJ3RWFnlbu9otSITLxWK7c5+/NHmWM+yaeHD/f/h
rp01c/8qXZfZAgMBAAGpEDAOBgNVHQ8BAf8EBAMCBeAwLzASBgkrBgEFBQcFAQEM
BTExMTExMBkGCSsGAQUFBwUBAgwMc2VydmVyX21hZ2ljoYGTMA0GCSqGSIb3DQEB
BQUAA4GBAEI3KNEvTq/n1kNVhNhPkovk1AZxyJrN1u1+7Gkc4PLjWwjLOjcEVWt4
AajUk/gkIJ6bbeO+fZlMjHfPSDKcD6AV2hN+n72QZwfzcw3icNvBG1el9EU4XfIm
xfu5YVWi81/fw8QQ6X6YGHFQkomLd7jxakVyjxSng9BhO6GpjJNF
"""

    def setUp(self):
        self.asn1Spec = rfc2511.CertReqMessages()

    def testDerCodec(self):

        substrate = pem.readBase64fromText(self.pem_text)

        asn1Object, rest = der_decoder.decode(substrate, asn1Spec=self.asn1Spec)

        assert not rest
        assert asn1Object.prettyPrint()
        assert der_encoder.encode(asn1Object) == substrate


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
