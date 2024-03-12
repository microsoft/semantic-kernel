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
from pyasn1_modules import rfc2437

try:
    import unittest2 as unittest

except ImportError:
    import unittest


class RSAPrivateKeyTestCase(unittest.TestCase):
    pem_text = """\
MIIBPAIBAAJBAMfAjvBNDDYBCl1w3yNcagZkPhqd0q5KqeOTgKSLuJWfe5+VSeR5
Y1PcF3DyH8dvS3t8PIQjxJLoKS7HVRlsfhECAwEAAQJBAIr93/gxhIenXbD7MykF
yvi7k8MtgkWoymICZwcX+c6RudFyuPPfQJ/sf6RmFZlRA9X9CQm5NwVG7+x1Yi6t
KoECIQDmJUCWkPCiQYow6YxetpXFa0K6hTzOPmax7MNHVWNgmQIhAN4xOZ4JFT34
xVhK+8EudBCYRomJUHmOJfoQAxiIXVw5AiEAyB7ecc5on/5zhqKef4Eu7LKfHIdc
304diFuDVpTmTAkCIC2ZmKOQZaWkSowGR4isCfHl7oQHhFaOD8k0RA5i3hYxAiEA
n8lDw3JT6NjvMnD6aM8KBsLyhazWSVVkaUSqmJzgCF0=
"""

    def setUp(self):
        self.asn1Spec = rfc2437.RSAPrivateKey()

    def testDerCodec(self):

        substrate = pem.readBase64fromText(self.pem_text)

        asn1Object, rest = der_decoder.decode(substrate, asn1Spec=self.asn1Spec)

        assert not rest
        assert asn1Object.prettyPrint()
        assert der_encoder.encode(asn1Object) == substrate


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
