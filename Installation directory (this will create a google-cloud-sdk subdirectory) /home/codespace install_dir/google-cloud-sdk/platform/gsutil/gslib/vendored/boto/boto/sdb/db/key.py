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

class Key(object):

    @classmethod
    def from_path(cls, *args, **kwds):
        raise NotImplementedError("Paths are not currently supported")

    def __init__(self, encoded=None, obj=None):
        self.name = None
        if obj:
            self.id = obj.id
            self.kind = obj.kind()
        else:
            self.id = None
            self.kind = None

    def app(self):
        raise NotImplementedError("Applications are not currently supported")

    def kind(self):
        return self.kind

    def id(self):
        return self.id

    def name(self):
        raise NotImplementedError("Key Names are not currently supported")

    def id_or_name(self):
        return self.id

    def has_id_or_name(self):
        return self.id is not None

    def parent(self):
        raise NotImplementedError("Key parents are not currently supported")

    def __str__(self):
        return self.id_or_name()
