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
from pyasn1_modules import rfc5652
from pyasn1_modules import rfc6402

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class ContentInfoTestCase(unittest.TestCase):
    pem_text = """\
MIIEJQYJKoZIhvcNAQcCoIIEFjCCBBICAQMxCzAJBgUrDgMCGgUAMIIDAgYIKwYBBQUHDAKgggL0
BIIC8DCCAuwweDB2AgECBgorBgEEAYI3CgoBMWUwYwIBADADAgEBMVkwVwYJKwYBBAGCNxUUMUow
SAIBBQwZcGl0dWNoYTEuZW1lYS5ocHFjb3JwLm5ldAwMRU1FQVxwaXR1Y2hhDBpDTUNSZXFHZW5l
cmF0b3IudnNob3N0LmV4ZTCCAmqgggJmAgEBMIICXzCCAcgCAQAwADCBnzANBgkqhkiG9w0BAQEF
AAOBjQAwgYkCgYEA0jm7SSSm2wyEAzuNKtFZFJKo91SrJq9wQwEhEKHDavZwMQOm1rZ2PF8NWCEb
PqrhToQ7rtiGLSZa4dF4bzgmBqQ9aoSfEX4jISt31Vy+skHidXjHHpbsjT24NPhrZgANivL7CxD6
Ft+s7qS1gL4HRm2twQkqSwOLrE/q2QeXl2UCAwEAAaCCAR0wGgYKKwYBBAGCNw0CAzEMFgo2LjIu
OTIwMC4yMD4GCSqGSIb3DQEJDjExMC8wHQYDVR0OBBYEFMW2skn88gxhONWZQA4sWGBDb68yMA4G
A1UdDwEB/wQEAwIHgDBXBgkrBgEEAYI3FRQxSjBIAgEFDBlwaXR1Y2hhMS5lbWVhLmhwcWNvcnAu
bmV0DAxFTUVBXHBpdHVjaGEMGkNNQ1JlcUdlbmVyYXRvci52c2hvc3QuZXhlMGYGCisGAQQBgjcN
AgIxWDBWAgECHk4ATQBpAGMAcgBvAHMAbwBmAHQAIABTAHQAcgBvAG4AZwAgAEMAcgB5AHAAdABv
AGcAcgBhAHAAaABpAGMAIABQAHIAbwB2AGkAZABlAHIDAQAwDQYJKoZIhvcNAQEFBQADgYEAJZlu
mxjtCxSOQi27jsVdd3y8NSIlzNv0b3LqmzvAly6L+CstXcnuG2MPQqPH9R7tbJonGUniBQO9sQ7C
KhYWj2gfhiEkSID82lV5chINVUFKoUlSiEhWr0tPGgvOaqdsKQcrHfzrsBbFkhDqrFSVy7Yivbnh
qYszKrOjJKiiCPMwADAAMYH5MIH2AgEDgBTFtrJJ/PIMYTjVmUAOLFhgQ2+vMjAJBgUrDgMCGgUA
oD4wFwYJKoZIhvcNAQkDMQoGCCsGAQUFBwwCMCMGCSqGSIb3DQEJBDEWBBTFTkK/OifaFjwqHiJu
xM7qXcg/VzANBgkqhkiG9w0BAQEFAASBgKfC6jOi1Wgy4xxDCQVK9+e5tktL8wE/j2cb9JSqq+aU
5UxEgXEw7q7BoYZCAzcxMRriGzakXr8aXHcgkRJ7XcFvLPUjpmGg9SOZ2sGW4zQdWAwImN/i8loc
xicQmJP+VoMHo/ZpjFY9fYCjNZUArgKsEwK/s+p9yrVVeB1Nf8Mn
"""

    def setUp(self):
        self.asn1Spec = rfc5652.ContentInfo()

    def testDerCodec(self):

        substrate = pem.readBase64fromText(self.pem_text)

        layers = {
            rfc5652.id_ct_contentInfo: rfc5652.ContentInfo(),
            rfc5652.id_signedData: rfc5652.SignedData(),
            rfc6402.id_cct_PKIData: rfc6402.PKIData()
        }

        getNextLayer = {
            rfc5652.id_ct_contentInfo: lambda x: x['contentType'],
            rfc5652.id_signedData: lambda x: x['encapContentInfo']['eContentType'],
            rfc6402.id_cct_PKIData: lambda x: None
        }

        getNextSubstrate = {
            rfc5652.id_ct_contentInfo: lambda x: x['content'],
            rfc5652.id_signedData: lambda x: x['encapContentInfo']['eContent'],
            rfc6402.id_cct_PKIData: lambda x: None
        }


        next_layer = rfc5652.id_ct_contentInfo

        while next_layer:

            asn1Object, rest = der_decoder.decode(
                substrate, asn1Spec=layers[next_layer]
            )

            assert not rest
            assert asn1Object.prettyPrint()
            assert der_encoder.encode(asn1Object) == substrate

            substrate = getNextSubstrate[next_layer](asn1Object)
            next_layer = getNextLayer[next_layer](asn1Object)


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
