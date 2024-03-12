# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
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

from boto.sqs.regioninfo import SQSRegionInfo
from boto.regioninfo import get_regions
from boto.regioninfo import connect


def regions():
    """
    Get all available regions for the SQS service.

    :rtype: list
    :return: A list of :class:`boto.sqs.regioninfo.RegionInfo`
    """
    from boto.sqs.connection import SQSConnection
    return get_regions(
        'sqs',
        region_cls=SQSRegionInfo,
        connection_cls=SQSConnection
    )


def connect_to_region(region_name, **kw_params):
    from boto.sqs.connection import SQSConnection
    return connect('sqs', region_name, region_cls=SQSRegionInfo,
                   connection_cls=SQSConnection, **kw_params)
