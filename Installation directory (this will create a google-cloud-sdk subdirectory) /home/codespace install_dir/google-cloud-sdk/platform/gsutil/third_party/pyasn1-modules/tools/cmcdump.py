#!/usr/bin/env python
#
# Read CMC certificate request with wrappers on stdin, parse each into
# plain text, then build substrate from it
#
import sys

from pyasn1.codec.der import decoder
from pyasn1.codec.der import encoder

from pyasn1_modules import pem
from pyasn1_modules import rfc5652
from pyasn1_modules import rfc6402

if len(sys.argv) != 1:
    print("""Usage:
$ cat cmc_request.pem | %s""" % (sys.argv[0],))
    sys.exit(-1)

reqCnt = 0

substrate = pem.readBase64FromFile(sys.stdin)

_, rest = decoder.decode(substrate, asn1Spec=rfc5652.ContentInfo())
assert not rest

next_layer = rfc5652.id_ct_contentInfo
data = substrate
while next_layer:
    if next_layer == rfc5652.id_ct_contentInfo:
        layer, rest = decoder.decode(data, asn1Spec=rfc5652.ContentInfo())
        assert encoder.encode(layer) == data, 'wrapper recode fails'
        assert not rest

        print(" * New layer (wrapper):")
        print(layer.prettyPrint())

        next_layer = layer['contentType']
        data = layer['content']

    elif next_layer == rfc5652.id_signedData:
        layer, rest = decoder.decode(data, asn1Spec=rfc5652.SignedData())
        assert encoder.encode(layer) == data, 'wrapper recode fails'
        assert not rest

        print(" * New layer (wrapper):")
        print(layer.prettyPrint())

        next_layer = layer['encapContentInfo']['eContentType']
        data = layer['encapContentInfo']['eContent']

    elif next_layer == rfc6402.id_cct_PKIData:
        layer, rest = decoder.decode(data, asn1Spec=rfc6402.PKIData())
        assert encoder.encode(layer) == data, 'pkidata recode fails'
        assert not rest

        print(" * New layer (pkidata):")
        print(layer.prettyPrint())

        next_layer = None
        data = None
