from boto.compat import six
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

def query_lister(domain, query='', max_items=None, attr_names=None):
    more_results = True
    num_results = 0
    next_token = None
    while more_results:
        rs = domain.connection.query_with_attributes(domain, query, attr_names,
                                                     next_token=next_token)
        for item in rs:
            if max_items:
                if num_results == max_items:
                    raise StopIteration
            yield item
            num_results += 1
        next_token = rs.next_token
        more_results = next_token is not None

class QueryResultSet(object):

    def __init__(self, domain=None, query='', max_items=None, attr_names=None):
        self.max_items = max_items
        self.domain = domain
        self.query = query
        self.attr_names = attr_names

    def __iter__(self):
        return query_lister(self.domain, self.query, self.max_items, self.attr_names)

def select_lister(domain, query='', max_items=None):
    more_results = True
    num_results = 0
    next_token = None
    while more_results:
        rs = domain.connection.select(domain, query, next_token=next_token)
        for item in rs:
            if max_items:
                if num_results == max_items:
                    raise StopIteration
            yield item
            num_results += 1
        next_token = rs.next_token
        more_results = next_token is not None

class SelectResultSet(object):

    def __init__(self, domain=None, query='', max_items=None,
                 next_token=None, consistent_read=False):
        self.domain = domain
        self.query = query
        self.consistent_read = consistent_read
        self.max_items = max_items
        self.next_token = next_token

    def __iter__(self):
        more_results = True
        num_results = 0
        while more_results:
            rs = self.domain.connection.select(self.domain, self.query,
                                               next_token=self.next_token,
                                               consistent_read=self.consistent_read)
            for item in rs:
                if self.max_items and num_results >= self.max_items:
                    raise StopIteration
                yield item
                num_results += 1
            self.next_token = rs.next_token
            if self.max_items and num_results >= self.max_items:
                raise StopIteration
            more_results = self.next_token is not None

    def next(self):
        return next(self.__iter__())
