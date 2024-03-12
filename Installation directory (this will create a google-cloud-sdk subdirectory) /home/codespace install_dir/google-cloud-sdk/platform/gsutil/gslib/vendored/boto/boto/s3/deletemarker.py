# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
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

from boto.s3.user import User

class DeleteMarker(object):
    def __init__(self, bucket=None, name=None):
        self.bucket = bucket
        self.name = name
        self.version_id = None
        self.is_latest = False
        self.last_modified = None
        self.owner = None

    def startElement(self, name, attrs, connection):
        if name == 'Owner':
            self.owner = User(self)
            return self.owner
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Key':
            self.name = value
        elif name == 'IsLatest':
            if value == 'true':
                self.is_latest = True
            else:
                self.is_latest = False
        elif name == 'LastModified':
            self.last_modified = value
        elif name == 'Owner':
            pass
        elif name == 'VersionId':
            self.version_id = value
        else:
            setattr(self, name, value)
