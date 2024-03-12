# Copyright (c) 2006,2007,2008 Mitch Garnaat http://garnaat.org/
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

from boto.compat import six


class Blob(object):
    """Blob object"""
    def __init__(self, value=None, file=None, id=None):
        self._file = file
        self.id = id
        self.value = value

    @property
    def file(self):
        from StringIO import StringIO
        if self._file:
            f = self._file
        else:
            f = StringIO(self.value)
        return f

    def __str__(self):
        return six.text_type(self).encode('utf-8')

    def __unicode__(self):
        if hasattr(self.file, "get_contents_as_string"):
            value = self.file.get_contents_as_string()
        else:
            value = self.file.getvalue()
        if isinstance(value, six.text_type):
            return value
        else:
            return value.decode('utf-8')

    def read(self):
        if hasattr(self.file, "get_contents_as_string"):
            return self.file.get_contents_as_string()
        else:
            return self.file.read()

    def readline(self):
        return self.file.readline()

    def next(self):
        return next(self.file)

    def __iter__(self):
        return iter(self.file)

    @property
    def size(self):
        if self._file:
            return self._file.size
        elif self.value:
            return len(self.value)
        else:
            return 0
