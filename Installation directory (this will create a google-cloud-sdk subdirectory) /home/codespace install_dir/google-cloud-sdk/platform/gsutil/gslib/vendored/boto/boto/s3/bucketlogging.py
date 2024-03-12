# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

import xml.sax.saxutils
from boto.s3.acl import Grant

class BucketLogging(object):

    def __init__(self, target=None, prefix=None, grants=None):
        self.target = target
        self.prefix = prefix
        if grants is None:
            self.grants = []
        else:
            self.grants = grants

    def __repr__(self):
        if self.target is None:
            return "<BucketLoggingStatus: Disabled>"
        grants = []
        for g in self.grants:
            if g.type == 'CanonicalUser':
                u = g.display_name
            elif g.type == 'Group':
                u = g.uri
            else:
                u = g.email_address
            grants.append("%s = %s" % (u, g.permission))
        return "<BucketLoggingStatus: %s/%s (%s)>" % (self.target, self.prefix, ", ".join(grants))

    def add_grant(self, grant):
        self.grants.append(grant)

    def startElement(self, name, attrs, connection):
        if name == 'Grant':
            self.grants.append(Grant())
            return self.grants[-1]
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'TargetBucket':
            self.target = value
        elif name == 'TargetPrefix':
            self.prefix = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        # caller is responsible to encode to utf-8
        s = u'<?xml version="1.0" encoding="UTF-8"?>'
        s += u'<BucketLoggingStatus xmlns="http://doc.s3.amazonaws.com/2006-03-01">'
        if self.target is not None:
            s += u'<LoggingEnabled>'
            s += u'<TargetBucket>%s</TargetBucket>' % self.target
            prefix = self.prefix or ''
            s += u'<TargetPrefix>%s</TargetPrefix>' % xml.sax.saxutils.escape(prefix)
            if self.grants:
                s += '<TargetGrants>'
                for grant in self.grants:
                    s += grant.to_xml()
                s += '</TargetGrants>'
            s += u'</LoggingEnabled>'
        s += u'</BucketLoggingStatus>'
        return s
