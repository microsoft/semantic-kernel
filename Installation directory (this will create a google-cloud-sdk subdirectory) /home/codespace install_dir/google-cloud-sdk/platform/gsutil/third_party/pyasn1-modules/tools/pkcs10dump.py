#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
# Read ASN.1/PEM X.509 certificate requests (PKCS#10 format) on stdin, 
# parse each into plain text, then build substrate from it
#
import sys

from pyasn1.codec.der import decoder
from pyasn1.codec.der import encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc2314

if len(sys.argv) != 1:
    print("""Usage:
$ cat certificateRequest.pem | %s""" % sys.argv[0])
    sys.exit(-1)

certType = rfc2314.CertificationRequest()

certCnt = 0

while True:
    idx, substrate = pem.readPemBlocksFromFile(
        sys.stdin, ('-----BEGIN CERTIFICATE REQUEST-----',
                    '-----END CERTIFICATE REQUEST-----')
    )
    if not substrate:
        break

    cert, rest = decoder.decode(substrate, asn1Spec=certType)

    if rest:
        substrate = substrate[:-len(rest)]

    print(cert.prettyPrint())

    assert encoder.encode(cert) == substrate, 'cert recode fails'

    certCnt += 1

print('*** %s PEM certificate request(s) de/serialized' % certCnt)
