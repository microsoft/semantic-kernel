# httpServerLogParser.py
#
# Copyright (c) 2016, Paul McGuire
#
"""
Parser for HTTP server log output, of the form:

195.146.134.15 - - [20/Jan/2003:08:55:36 -0800]
"GET /path/to/page.html HTTP/1.0" 200 4649 "http://www.somedomain.com/020602/page.html"
"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
127.0.0.1 - u.surname@domain.com [12/Sep/2006:14:13:53 +0300]
"GET /skins/monobook/external.png HTTP/1.0" 304 - "http://wiki.mysite.com/skins/monobook/main.css"
"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.6) Gecko/20060728 Firefox/1.5.0.6"

You can then break it up as follows:
IP ADDRESS - -
Server Date / Time [SPACE]
"GET /path/to/page
HTTP/Type Request"
Success Code
Bytes Sent To Client
Referer
Client Software
"""

from pyparsing import alphas,nums, dblQuotedString, Combine, Word, Group, delimitedList, Suppress, removeQuotes
import string

def getCmdFields( s, l, t ):
    t["method"],t["requestURI"],t["protocolVersion"] = t[0].strip('"').split()

logLineBNF = None
def getLogLineBNF():
    global logLineBNF

    if logLineBNF is None:
        integer = Word( nums )
        ipAddress = delimitedList( integer, ".", combine=True )

        timeZoneOffset = Word("+-",nums)
        month = Word(string.ascii_uppercase, string.ascii_lowercase, exact=3)
        serverDateTime = Group( Suppress("[") +
                                Combine( integer + "/" + month + "/" + integer +
                                        ":" + integer + ":" + integer + ":" + integer ) +
                                timeZoneOffset +
                                Suppress("]") )

        logLineBNF = ( ipAddress.setResultsName("ipAddr") +
                       Suppress("-") +
                       ("-" | Word( alphas+nums+"@._" )).setResultsName("auth") +
                       serverDateTime.setResultsName("timestamp") +
                       dblQuotedString.setResultsName("cmd").setParseAction(getCmdFields) +
                       (integer | "-").setResultsName("statusCode") +
                       (integer | "-").setResultsName("numBytesSent")  +
                       dblQuotedString.setResultsName("referrer").setParseAction(removeQuotes) +
                       dblQuotedString.setResultsName("clientSfw").setParseAction(removeQuotes) )
    return logLineBNF

testdata = """
195.146.134.15 - - [20/Jan/2003:08:55:36 -0800] "GET /path/to/page.html HTTP/1.0" 200 4649 "http://www.somedomain.com/020602/page.html" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
111.111.111.11 - - [16/Feb/2004:04:09:49 -0800] "GET /ads/redirectads/336x280redirect.htm HTTP/1.1" 304 - "http://www.foobarp.org/theme_detail.php?type=vs&cat=0&mid=27512" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
11.111.11.111 - - [16/Feb/2004:10:35:12 -0800] "GET /ads/redirectads/468x60redirect.htm HTTP/1.1" 200 541 "http://11.11.111.11/adframe.php?n=ad1f311a&what=zone:56" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1) Opera 7.20  [ru\"]"
127.0.0.1 - u.surname@domain.com [12/Sep/2006:14:13:53 +0300] "GET /skins/monobook/external.png HTTP/1.0" 304 - "http://wiki.mysite.com/skins/monobook/main.css" "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.0.6) Gecko/20060728 Firefox/1.5.0.6"
"""
for line in testdata.split("\n"):
    if not line: continue
    fields = getLogLineBNF().parseString(line)
    print(fields.dump())
    #~ print repr(fields)
    #~ for k in fields.keys():
        #~ print "fields." + k + " =", fields[k]
    print()
