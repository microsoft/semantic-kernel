#
# dhcpd_leases_parser.py
#
# Copyright 2008, Paul McGuire
#
# Sample parser to parse a dhcpd.leases file to extract leases
# and lease attributes
#
# format ref: http://www.linuxmanpages.com/man5/dhcpd.leases.5.php
#

sample = r"""\
# All times in this file are in UTC (GMT), not your local timezone.   This is
# not a bug, so please don't ask about it.   There is no portable way to
# store leases in the local timezone, so please don't request this as a
# feature.   If this is inconvenient or confusing to you, we sincerely
# apologize.   Seriously, though - don't ask.
# The format of this file is documented in the dhcpd.leases(5) manual page.
# This lease file was written by isc-dhcp-V3.0.4

lease 192.168.0.250 {
  starts 3 2008/01/23 17:16:41;
  ends 6 2008/02/02 17:16:41;
  tstp 6 2008/02/02 17:16:41;
  binding state free;
  hardware ethernet 00:17:f2:9b:d8:19;
  uid "\001\000\027\362\233\330\031";
}
lease 192.168.0.198 {
  starts 1 2008/02/04 13:46:55;
  ends never;
  tstp 1 2008/02/04 17:04:14;
  binding state free;
  hardware ethernet 00:13:72:d3:3b:98;
  uid "\001\000\023r\323;\230";
}
lease 192.168.0.239 {
  starts 3 2008/02/06 12:12:03;
  ends 4 2008/02/07 12:12:03;
  tstp 4 2008/02/07 12:12:03;
  binding state free;
  hardware ethernet 00:1d:09:65:93:26;
}
"""

from pyparsing import *
import datetime,time

LBRACE,RBRACE,SEMI,QUOTE = map(Suppress,'{};"')
ipAddress = Combine(Word(nums) + ('.' + Word(nums))*3)
hexint = Word(hexnums,exact=2)
macAddress = Combine(hexint + (':'+hexint)*5)
hdwType = Word(alphanums)

yyyymmdd = Combine((Word(nums,exact=4)|Word(nums,exact=2))+
                    ('/'+Word(nums,exact=2))*2)
hhmmss = Combine(Word(nums,exact=2)+(':'+Word(nums,exact=2))*2)
dateRef = oneOf(list("0123456"))("weekday") + yyyymmdd("date") + \
                                                        hhmmss("time")

def utcToLocalTime(tokens):
    utctime = datetime.datetime.strptime("%(date)s %(time)s" % tokens,
                                                    "%Y/%m/%d %H:%M:%S")
    localtime = utctime-datetime.timedelta(0,time.timezone,0)
    tokens["utcdate"],tokens["utctime"] = tokens["date"],tokens["time"]
    tokens["localdate"],tokens["localtime"] = str(localtime).split()
    del tokens["date"]
    del tokens["time"]
dateRef.setParseAction(utcToLocalTime)

startsStmt = "starts" + dateRef + SEMI
endsStmt = "ends" + (dateRef | "never") + SEMI
tstpStmt = "tstp" + dateRef + SEMI
tsfpStmt = "tsfp" + dateRef + SEMI
hdwStmt = "hardware" + hdwType("type") + macAddress("mac") + SEMI
uidStmt = "uid" + QuotedString('"')("uid") + SEMI
bindingStmt = "binding" + Word(alphanums) + Word(alphanums) + SEMI

leaseStatement = startsStmt | endsStmt | tstpStmt | tsfpStmt | hdwStmt | \
                                                        uidStmt | bindingStmt
leaseDef = "lease" + ipAddress("ipaddress") + LBRACE + \
                            Dict(ZeroOrMore(Group(leaseStatement))) + RBRACE

for lease in leaseDef.searchString(sample):
    print(lease.dump())
    print(lease.ipaddress,'->',lease.hardware.mac)
    print()
