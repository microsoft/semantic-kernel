#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
# Read ASN.1/PEM CMP message on stdin, parse into
# plain text, then build substrate from it
#
import sys

from pyasn1 import debug
from pyasn1.codec.der import decoder
from pyasn1.codec.der import encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc4210

if len(sys.argv) == 2 and sys.argv[1] == '-d':
    debug.setLogger(debug.Debug('all'))
elif len(sys.argv) != 1:
    print("""Usage:
$ cat cmp.pem | %s [-d]""" % sys.argv[0])
    sys.exit(-1)

pkiMessage = rfc4210.PKIMessage()

substrate = pem.readBase64FromFile(sys.stdin)
if not substrate:
    sys.exit(0)

pkiMsg, rest = decoder.decode(substrate, asn1Spec=pkiMessage)

print(pkiMsg.prettyPrint())

assert encoder.encode(pkiMsg) == substrate, 'CMP message recode fails'
