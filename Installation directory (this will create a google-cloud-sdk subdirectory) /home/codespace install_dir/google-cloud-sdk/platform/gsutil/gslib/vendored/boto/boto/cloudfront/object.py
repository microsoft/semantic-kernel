# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

from boto.s3.key import Key

class Object(Key):

    def __init__(self, bucket, name=None):
        super(Object, self).__init__(bucket, name=name)
        self.distribution = bucket.distribution

    def __repr__(self):
        return '<Object: %s/%s>' % (self.distribution.config.origin, self.name)

    def url(self, scheme='http'):
        url = '%s://' % scheme
        url += self.distribution.domain_name
        if scheme.lower().startswith('rtmp'):
            url += '/cfx/st/'
        else:
            url += '/'
        url += self.name
        return url

class StreamingObject(Object):

    def url(self, scheme='rtmp'):
        return super(StreamingObject, self).url(scheme)


