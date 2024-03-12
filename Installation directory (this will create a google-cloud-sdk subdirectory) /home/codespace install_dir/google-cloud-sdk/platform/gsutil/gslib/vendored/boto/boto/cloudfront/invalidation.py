# Copyright (c) 2006-2010 Chris Moyer http://coredumped.org/
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

import uuid

from boto.compat import urllib
from boto.resultset import ResultSet


class InvalidationBatch(object):
    """A simple invalidation request.
        :see: http://docs.amazonwebservices.com/AmazonCloudFront/2010-08-01/APIReference/index.html?InvalidationBatchDatatype.html
    """

    def __init__(self, paths=None, connection=None, distribution=None, caller_reference=''):
        """Create a new invalidation request:
            :paths: An array of paths to invalidate
        """
        self.paths = paths or []
        self.distribution = distribution
        self.caller_reference = caller_reference
        if not self.caller_reference:
            self.caller_reference = str(uuid.uuid4())

        # If we passed in a distribution,
        # then we use that as the connection object
        if distribution:
            self.connection = distribution
        else:
            self.connection = connection

    def __repr__(self):
        return '<InvalidationBatch: %s>' % self.id

    def add(self, path):
        """Add another path to this invalidation request"""
        return self.paths.append(path)

    def remove(self, path):
        """Remove a path from this invalidation request"""
        return self.paths.remove(path)

    def __iter__(self):
        return iter(self.paths)

    def __getitem__(self, i):
        return self.paths[i]

    def __setitem__(self, k, v):
        self.paths[k] = v

    def escape(self, p):
        """Escape a path, make sure it begins with a slash and contains no invalid characters. Retain literal wildcard characters."""
        if not p[0] == "/":
            p = "/%s" % p
        return urllib.parse.quote(p, safe = "/*")

    def to_xml(self):
        """Get this batch as XML"""
        assert self.connection is not None
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s += '<InvalidationBatch xmlns="http://cloudfront.amazonaws.com/doc/%s/">\n' % self.connection.Version
        for p in self.paths:
            s += '    <Path>%s</Path>\n' % self.escape(p)
        s += '    <CallerReference>%s</CallerReference>\n' % self.caller_reference
        s += '</InvalidationBatch>\n'
        return s

    def startElement(self, name, attrs, connection):
        if name == "InvalidationBatch":
            self.paths = []
        return None

    def endElement(self, name, value, connection):
        if name == 'Path':
            self.paths.append(value)
        elif name == "Status":
            self.status = value
        elif name == "Id":
            self.id = value
        elif name == "CreateTime":
            self.create_time = value
        elif name == "CallerReference":
            self.caller_reference = value
        return None


class InvalidationListResultSet(object):
    """
    A resultset for listing invalidations on a given CloudFront distribution.
    Implements the iterator interface and transparently handles paging results
    from CF so even if you have many thousands of invalidations on the
    distribution you can iterate over all invalidations in a reasonably
    efficient manner.
    """
    def __init__(self, markers=None, connection=None, distribution_id=None,
                 invalidations=None, marker='', next_marker=None,
                 max_items=None, is_truncated=False):
        self.markers = markers or []
        self.connection = connection
        self.distribution_id = distribution_id
        self.marker = marker
        self.next_marker = next_marker
        self.max_items = max_items
        self.auto_paginate = max_items is None
        self.is_truncated = is_truncated
        self._inval_cache = invalidations or []

    def __iter__(self):
        """
        A generator function for listing invalidation requests for a given
        CloudFront distribution.
        """
        conn = self.connection
        distribution_id = self.distribution_id
        result_set = self
        for inval in result_set._inval_cache:
            yield inval
        if not self.auto_paginate:
            return
        while result_set.is_truncated:
            result_set = conn.get_invalidation_requests(distribution_id,
                                                        marker=result_set.next_marker,
                                                        max_items=result_set.max_items)
            for i in result_set._inval_cache:
                yield i

    def startElement(self, name, attrs, connection):
        for root_elem, handler in self.markers:
            if name == root_elem:
                obj = handler(connection, distribution_id=self.distribution_id)
                self._inval_cache.append(obj)
                return obj

    def endElement(self, name, value, connection):
        if name == 'IsTruncated':
            self.is_truncated = self.to_boolean(value)
        elif name == 'Marker':
            self.marker = value
        elif name == 'NextMarker':
            self.next_marker = value
        elif name == 'MaxItems':
            self.max_items = int(value)

    def to_boolean(self, value, true_value='true'):
        if value == true_value:
            return True
        else:
            return False

class InvalidationSummary(object):
    """
    Represents InvalidationSummary complex type in CloudFront API that lists
    the id and status of a given invalidation request.
    """
    def __init__(self, connection=None, distribution_id=None, id='',
                 status=''):
        self.connection = connection
        self.distribution_id = distribution_id
        self.id = id
        self.status = status

    def __repr__(self):
        return '<InvalidationSummary: %s>' % self.id

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value
        elif name == 'Status':
            self.status = value

    def get_distribution(self):
        """
        Returns a Distribution object representing the parent CloudFront
        distribution of the invalidation request listed in the
        InvalidationSummary.

        :rtype: :class:`boto.cloudfront.distribution.Distribution`
        :returns: A Distribution object representing the parent CloudFront
                  distribution  of the invalidation request listed in the
                  InvalidationSummary
        """
        return self.connection.get_distribution_info(self.distribution_id)

    def get_invalidation_request(self):
        """
        Returns an InvalidationBatch object representing the invalidation
        request referred to in the InvalidationSummary.

        :rtype: :class:`boto.cloudfront.invalidation.InvalidationBatch`
        :returns: An InvalidationBatch object representing the invalidation
                  request referred to by the InvalidationSummary
        """
        return self.connection.invalidation_request_status(
            self.distribution_id, self.id)
