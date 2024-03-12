# getNTPserversNew.py
#
# Demonstration of the parsing module, implementing a HTML page scanner,
# to extract a list of NTP time servers from the NIST web site.
#
# Copyright 2004-2010, by Paul McGuire
# September, 2010 - updated to more current use of setResultsName, new NIST URL
#
import pyparsing as pp
ppc = pp.pyparsing_common
from contextlib import closing

try:
    import urllib.request
    urlopen = urllib.request.urlopen
except ImportError:
    import urllib
    urlopen = urllib.urlopen

integer = pp.Word(pp.nums)
ipAddress = ppc.ipv4_address()
hostname = pp.delimitedList(pp.Word(pp.alphas, pp.alphanums+"-_"), ".", combine=True)
tdStart, tdEnd = pp.makeHTMLTags("td")
timeServerPattern = (tdStart + hostname("hostname") + tdEnd
                     + tdStart + ipAddress("ipAddr") + tdEnd
                     + tdStart + tdStart.tag_body("loc") + tdEnd)

# get list of time servers
nistTimeServerURL = "https://tf.nist.gov/tf-cgi/servers.cgi#"
with closing(urlopen(nistTimeServerURL)) as serverListPage:
    serverListHTML = serverListPage.read().decode("UTF-8")

addrs = {}
for srvr, startloc, endloc in timeServerPattern.scanString(serverListHTML):
    print("{0} ({1}) - {2}".format(srvr.ipAddr, srvr.hostname.strip(), srvr.loc.strip()))
    addrs[srvr.ipAddr] = srvr.loc
