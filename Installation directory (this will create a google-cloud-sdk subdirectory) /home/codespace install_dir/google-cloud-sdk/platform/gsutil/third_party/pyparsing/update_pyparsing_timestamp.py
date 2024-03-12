from pyparsing import quotedString
from datetime import datetime

nw = datetime.utcnow()
nowstring = '"%s"' % (nw.strftime("%d %b %Y %X")[:-3] + " UTC")
print (nowstring)

quoted_time = quotedString()
quoted_time.setParseAction(lambda: nowstring)

version_time = "__versionTime__ = " + quoted_time
with open('pyparsing.py', encoding='utf-8') as oldpp:
    orig_code = oldpp.read()
    new_code = version_time.transformString(orig_code)

with open('pyparsing.py','w', encoding='utf-8') as newpp:
    newpp.write(new_code)
