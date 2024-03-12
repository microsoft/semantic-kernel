#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
# Read X.509 CRL on stdin, print them pretty and encode back into 
# original wire format.
# CRL can be generated with "openssl openssl ca -gencrl ..." commands.
#
import sys

from pyasn1.codec.der import decoder
from pyasn1.codec.der import encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc2459

if len(sys.argv) != 1:
    print("""Usage:
$ cat crl.pem | %s""" % sys.argv[0])
    sys.exit(-1)

asn1Spec = rfc2459.CertificateList()

cnt = 0

while True:
    idx, substrate = pem.readPemBlocksFromFile(sys.stdin, ('-----BEGIN X509 CRL-----', '-----END X509 CRL-----'))
    if not substrate:
        break

    key, rest = decoder.decode(substrate, asn1Spec=asn1Spec)

    if rest:
        substrate = substrate[:-len(rest)]

    print(key.prettyPrint())

    assert encoder.encode(key) == substrate, 'pkcs8 recode fails'

    cnt += 1

print('*** %s CRL(s) re/serialized' % cnt)
