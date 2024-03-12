#!/usr/bin/env python
#
# This file is part of pyasn1-modules software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
# Generate SNMPGET request, parse response
#
import socket
import sys

from pyasn1.codec.ber import decoder
from pyasn1.codec.ber import encoder

from pyasn1_modules import rfc1157

if len(sys.argv) != 4:
    print("""Usage:
$ %s <community> <host> <OID>""" % sys.argv[0])
    sys.exit(-1)

msg = rfc1157.Message()
msg.setComponentByPosition(0)
msg.setComponentByPosition(1, sys.argv[1])
# pdu
pdus = msg.setComponentByPosition(2).getComponentByPosition(2)
pdu = pdus.setComponentByPosition(0).getComponentByPosition(0)
pdu.setComponentByPosition(0, 123)
pdu.setComponentByPosition(1, 0)
pdu.setComponentByPosition(2, 0)
vbl = pdu.setComponentByPosition(3).getComponentByPosition(3)
vb = vbl.setComponentByPosition(0).getComponentByPosition(0)
vb.setComponentByPosition(0, sys.argv[3])
v = vb.setComponentByPosition(1).getComponentByPosition(1).setComponentByPosition(0).getComponentByPosition(0).setComponentByPosition(3).getComponentByPosition(3)

print('sending: %s' % msg.prettyPrint())

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(encoder.encode(msg), (sys.argv[2], 161))

substrate, _ = sock.recvfrom(2048)

# noinspection PyRedeclaration
rMsg, _ = decoder.decode(substrate, asn1Spec=msg)

print('received: %s' % rMsg.prettyPrint())
