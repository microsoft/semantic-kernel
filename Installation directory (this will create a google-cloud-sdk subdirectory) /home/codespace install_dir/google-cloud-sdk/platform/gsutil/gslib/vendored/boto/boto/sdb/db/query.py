from boto.compat import six
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

class Query(object):
    __local_iter__ = None
    def __init__(self, model_class, limit=None, next_token=None, manager=None):
        self.model_class = model_class
        self.limit = limit
        self.offset = 0
        if manager:
            self.manager = manager
        else:
            self.manager = self.model_class._manager
        self.filters = []
        self.select = None
        self.sort_by = None
        self.rs = None
        self.next_token = next_token

    def __iter__(self):
        return iter(self.manager.query(self))

    def next(self):
        if self.__local_iter__ is None:
            self.__local_iter__ = self.__iter__()
        return next(self.__local_iter__)

    def filter(self, property_operator, value):
        self.filters.append((property_operator, value))
        return self

    def fetch(self, limit, offset=0):
        """Not currently fully supported, but we can use this
        to allow them to set a limit in a chainable method"""
        self.limit = limit
        self.offset = offset
        return self

    def count(self, quick=True):
        return self.manager.count(self.model_class, self.filters, quick, self.sort_by, self.select)

    def get_query(self):
        return self.manager._build_filter_part(self.model_class, self.filters, self.sort_by, self.select)

    def order(self, key):
        self.sort_by = key
        return self

    def to_xml(self, doc=None):
        if not doc:
            xmlmanager = self.model_class.get_xmlmanager()
            doc = xmlmanager.new_doc()
        for obj in self:
            obj.to_xml(doc)
        return doc

    def get_next_token(self):
        if self.rs:
            return self.rs.next_token
        if self._next_token:
            return self._next_token
        return None

    def set_next_token(self, token):
        self._next_token = token

    next_token = property(get_next_token, set_next_token)
