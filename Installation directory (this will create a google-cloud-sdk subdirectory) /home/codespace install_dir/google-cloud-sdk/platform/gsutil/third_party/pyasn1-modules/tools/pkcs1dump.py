#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
# Read unencrypted PKCS#1/PKIX-compliant, PEM&DER encoded private keys on
# stdin, print them pretty and encode back into original wire format.
# Private keys can be generated with "openssl genrsa|gendsa" commands.
#
import sys

from pyasn1.codec.der import decoder
from pyasn1.codec.der import encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc2437
from pyasn1_modules import rfc2459

if len(sys.argv) != 1:
    print("""Usage:
$ cat rsakey.pem | %s""" % sys.argv[0])
    sys.exit(-1)

cnt = 0

while True:
    idx, substrate = pem.readPemBlocksFromFile(
        sys.stdin,
        ('-----BEGIN RSA PRIVATE KEY-----', '-----END RSA PRIVATE KEY-----'),
        ('-----BEGIN DSA PRIVATE KEY-----', '-----END DSA PRIVATE KEY-----')
    )
    if not substrate:
        break

    if idx == 0:
        asn1Spec = rfc2437.RSAPrivateKey()
    elif idx == 1:
        asn1Spec = rfc2459.DSAPrivateKey()
    else:
        break

    key, rest = decoder.decode(substrate, asn1Spec=asn1Spec)

    if rest:
        substrate = substrate[:-len(rest)]

    print(key.prettyPrint())

    assert encoder.encode(key) == substrate, 'pkcs8 recode fails'

    cnt += 1

print('*** %s key(s) re/serialized' % cnt)
