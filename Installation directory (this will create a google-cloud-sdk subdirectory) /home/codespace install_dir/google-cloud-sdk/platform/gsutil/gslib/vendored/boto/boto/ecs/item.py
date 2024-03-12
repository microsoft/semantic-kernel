# Copyright (c) 2010 Chris Moyer http://coredumped.org/
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


import xml.sax
import cgi
from boto.compat import six, StringIO

class ResponseGroup(xml.sax.ContentHandler):
    """A Generic "Response Group", which can
    be anything from the entire list of Items to
    specific response elements within an item"""

    def __init__(self, connection=None, nodename=None):
        """Initialize this Item"""
        self._connection = connection
        self._nodename = nodename
        self._nodepath = []
        self._curobj = None
        self._xml = StringIO()

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__dict__)

    #
    # Attribute Functions
    #
    def get(self, name):
        return self.__dict__.get(name)

    def set(self, name, value):
        self.__dict__[name] = value

    def to_xml(self):
        return "<%s>%s</%s>" % (self._nodename, self._xml.getvalue(), self._nodename)

    #
    # XML Parser functions
    #
    def startElement(self, name, attrs, connection):
        self._xml.write("<%s>" % name)
        self._nodepath.append(name)
        if len(self._nodepath) == 1:
            obj = ResponseGroup(self._connection)
            self.set(name, obj)
            self._curobj = obj
        elif self._curobj:
            self._curobj.startElement(name, attrs, connection)
        return None

    def endElement(self, name, value, connection):
        self._xml.write("%s</%s>" % (cgi.escape(value).replace("&amp;amp;", "&amp;"), name))
        if len(self._nodepath) == 0:
            return
        obj = None
        curval = self.get(name)
        if len(self._nodepath) == 1:
            if value or not curval:
                self.set(name, value)
            if self._curobj:
                self._curobj = None
        #elif len(self._nodepath) == 2:
            #self._curobj = None
        elif self._curobj:
            self._curobj.endElement(name, value, connection)
        self._nodepath.pop()
        return None


class Item(ResponseGroup):
    """A single Item"""

    def __init__(self, connection=None):
        """Initialize this Item"""
        ResponseGroup.__init__(self, connection, "Item")

class ItemSet(ResponseGroup):
    """A special ResponseGroup that has built-in paging, and
    only creates new Items on the "Item" tag"""

    def __init__(self, connection, action, params, page=0):
        ResponseGroup.__init__(self, connection, "Items")
        self.objs = []
        self.iter = None
        self.page = page
        self.action = action
        self.params = params
        self.curItem = None
        self.total_results = 0
        self.total_pages = 0
        self.is_valid = False
        self.errors = []

    def startElement(self, name, attrs, connection):
        if name == "Item":
            self.curItem = Item(self._connection)
        elif self.curItem is not None:
            self.curItem.startElement(name, attrs, connection)
        return None

    def endElement(self, name, value, connection):
        if name == 'TotalResults':
            self.total_results = value
        elif name == 'TotalPages':
            self.total_pages = value
        elif name == 'IsValid':
            if value == 'True':
                self.is_valid = True
        elif name == 'Code':
            self.errors.append({'Code': value, 'Message': None})
        elif name == 'Message':
            self.errors[-1]['Message'] = value
        elif name == 'Item':
            self.objs.append(self.curItem)
            self._xml.write(self.curItem.to_xml())
            self.curItem = None
        elif self.curItem is not None:
            self.curItem.endElement(name, value, connection)
        return None

    def __next__(self):
        """Special paging functionality"""
        if self.iter is None:
            self.iter = iter(self.objs)
        try:
            return next(self.iter)
        except StopIteration:
            self.iter = None
            self.objs = []
            if int(self.page) < int(self.total_pages):
                self.page += 1
                self._connection.get_response(self.action, self.params, self.page, self)
                return next(self)
            else:
                raise

    next = __next__

    def __iter__(self):
        return self

    def to_xml(self):
        """Override to first fetch everything"""
        for item in self:
            pass
        return ResponseGroup.to_xml(self)
