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

from boto.sqs.message import MHMessage
from boto.utils import get_ts
from socket import gethostname
import os, mimetypes, time

class ServiceMessage(MHMessage):

    def for_key(self, key, params=None, bucket_name=None):
        if params:
            self.update(params)
        if key.path:
            t = os.path.split(key.path)
            self['OriginalLocation'] = t[0]
            self['OriginalFileName'] = t[1]
            mime_type = mimetypes.guess_type(t[1])[0]
            if mime_type is None:
                mime_type = 'application/octet-stream'
            self['Content-Type'] = mime_type
            s = os.stat(key.path)
            t = time.gmtime(s[7])
            self['FileAccessedDate'] = get_ts(t)
            t = time.gmtime(s[8])
            self['FileModifiedDate'] = get_ts(t)
            t = time.gmtime(s[9])
            self['FileCreateDate'] = get_ts(t)
        else:
            self['OriginalFileName'] = key.name
            self['OriginalLocation'] = key.bucket.name
            self['ContentType'] = key.content_type
        self['Host'] = gethostname()
        if bucket_name:
            self['Bucket'] = bucket_name
        else:
            self['Bucket'] = key.bucket.name
        self['InputKey'] = key.name
        self['Size'] = key.size

