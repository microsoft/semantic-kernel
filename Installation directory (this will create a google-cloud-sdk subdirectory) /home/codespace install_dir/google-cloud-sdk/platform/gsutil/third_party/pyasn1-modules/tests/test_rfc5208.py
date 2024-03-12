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
from pyasn1_modules import rfc5208

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class PrivateKeyInfoTestCase(unittest.TestCase):
    pem_text = """\
MIIBVgIBADANBgkqhkiG9w0BAQEFAASCAUAwggE8AgEAAkEAx8CO8E0MNgEKXXDf
I1xqBmQ+Gp3Srkqp45OApIu4lZ97n5VJ5HljU9wXcPIfx29Le3w8hCPEkugpLsdV
GWx+EQIDAQABAkEAiv3f+DGEh6ddsPszKQXK+LuTwy2CRajKYgJnBxf5zpG50XK4
899An+x/pGYVmVED1f0JCbk3BUbv7HViLq0qgQIhAOYlQJaQ8KJBijDpjF62lcVr
QrqFPM4+ZrHsw0dVY2CZAiEA3jE5ngkVPfjFWEr7wS50EJhGiYlQeY4l+hADGIhd
XDkCIQDIHt5xzmif/nOGop5/gS7ssp8ch1zfTh2IW4NWlOZMCQIgLZmYo5BlpaRK
jAZHiKwJ8eXuhAeEVo4PyTREDmLeFjECIQCfyUPDclPo2O8ycPpozwoGwvKFrNZJ
VWRpRKqYnOAIXQ==
"""

    def setUp(self):
        self.asn1Spec = rfc5208.PrivateKeyInfo()

    def testDerCodec(self):

        substrate = pem.readBase64fromText(self.pem_text)

        asn1Object, rest = der_decoder.decode(substrate, asn1Spec=self.asn1Spec)

        assert not rest
        assert asn1Object.prettyPrint()
        assert der_encoder.encode(asn1Object) == substrate


class EncryptedPrivateKeyInfoInfoTestCase(unittest.TestCase):
    pem_text = """\
MIIBgTAbBgkqhkiG9w0BBQMwDgQIdtFgDWnipT8CAggABIIBYN0hkm2xqkTCt8dJ
iZS8+HNiyHxy8g+rmWSXv/i+bTHFUReZA2GINtTRUkWpXqWcSHxNslgf7QdfgbVJ
xQiUM+lLhwOFh85iAHR3xmPU1wfN9NvY9DiLSpM0DMhF3OvAMZD75zIhA0GSKu7w
dUu7ey7H4fv7bez6RhEyLdKw9/Lf2KNStNOs4ow9CAtCoxeoMSniTt6CNhbvCkve
9vNHKiGavX1tS/YTog4wiiGzh2YxuW1RiQpTdhWiKyECgD8qQVg2tY5t3QRcXrzi
OkStpkiAPAbiwS/gyHpsqiLo0al63SCxRefugbn1ucZyc5Ya59e3xNFQXCNhYl+Z
Hl3hIl3cssdWZkJ455Z/bBE29ks1HtsL+bTfFi+kw/4yuMzoaB8C7rXScpGNI/8E
pvTU2+wtuoOFcttJregtR94ZHu5wgdYqRydmFNG8PnvZT1mRMmQgUe/vp88FMmsZ
dLsZjNQ=
"""

    def setUp(self):
        self.asn1Spec = rfc5208.EncryptedPrivateKeyInfo()

    def testDerCodec(self):
        substrate = pem.readBase64fromText(self.pem_text)

        asn1Object, rest = der_decoder.decode(substrate, asn1Spec=self.asn1Spec)

        assert not rest
        assert asn1Object.prettyPrint()
        assert der_encoder.encode(asn1Object) == substrate


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
