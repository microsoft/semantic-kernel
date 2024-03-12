# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
# Copyright (c) 2014, Steven Richards <sbrichards@mit.edu>
# All rights reserved.
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
#

from boto.regioninfo import RegionInfo, get_regions
from boto.regioninfo import connect


class S3RegionInfo(RegionInfo):

    def connect(self, **kw_params):
        """
        Connect to this Region's endpoint. Returns an connection
        object pointing to the endpoint associated with this region.
        You may pass any of the arguments accepted by the connection
        class's constructor as keyword arguments and they will be
        passed along to the connection object.

        :rtype: Connection object
        :return: The connection to this regions endpoint
        """
        if self.connection_cls:
            return self.connection_cls(host=self.endpoint, **kw_params)


def regions():
    """
    Get all available regions for the Amazon S3 service.

    :rtype: list
    :return: A list of :class:`boto.regioninfo.RegionInfo`
    """
    from boto.s3.connection import S3Connection
    return get_regions(
        's3',
        region_cls=S3RegionInfo,
        connection_cls=S3Connection
    )


def connect_to_region(region_name, **kw_params):
    from boto.s3.connection import S3Connection
    if 'host' in kw_params:
        host = kw_params.pop('host')
        if host not in ['', None]:
            region = S3RegionInfo(
                name='custom',
                endpoint=host,
                connection_cls=S3Connection
            )
            return region.connect(**kw_params)

    return connect('s3', region_name, region_cls=S3RegionInfo,
                   connection_cls=S3Connection, **kw_params)
