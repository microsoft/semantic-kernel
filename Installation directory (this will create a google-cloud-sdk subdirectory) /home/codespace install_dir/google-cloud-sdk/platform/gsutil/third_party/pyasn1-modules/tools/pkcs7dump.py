#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
# Read ASN.1/PEM PKCS#7 on stdin, parse it into plain text,
# then build substrate from it
#
import sys

from pyasn1.codec.der import decoder
from pyasn1.codec.der import encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc2315

if len(sys.argv) != 1:
    print("""Usage:
$ cat pkcs7Certificate.pem | %s""" % sys.argv[0])
    sys.exit(-1)

idx, substrate = pem.readPemBlocksFromFile(
    sys.stdin, ('-----BEGIN PKCS7-----', '-----END PKCS7-----')
)

assert substrate, 'bad PKCS7 data on input'

contentInfo, rest = decoder.decode(substrate, asn1Spec=rfc2315.ContentInfo())

if rest:
    substrate = substrate[:-len(rest)]

print(contentInfo.prettyPrint())

assert encoder.encode(contentInfo) == substrate, 're-encode fails'

contentType = contentInfo.getComponentByName('contentType')

contentInfoMap = {
    (1, 2, 840, 113549, 1, 7, 1): rfc2315.Data(),
    (1, 2, 840, 113549, 1, 7, 2): rfc2315.SignedData(),
    (1, 2, 840, 113549, 1, 7, 3): rfc2315.EnvelopedData(),
    (1, 2, 840, 113549, 1, 7, 4): rfc2315.SignedAndEnvelopedData(),
    (1, 2, 840, 113549, 1, 7, 5): rfc2315.DigestedData(),
    (1, 2, 840, 113549, 1, 7, 6): rfc2315.EncryptedData()
}

content, _ = decoder.decode(
    contentInfo.getComponentByName('content'),
    asn1Spec=contentInfoMap[contentType]
)

print(content.prettyPrint())
