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
#

from boto.sdb.regioninfo import SDBRegionInfo
from boto.regioninfo import get_regions
from boto.regioninfo import connect


def regions():
    """
    Get all available regions for the SDB service.

    :rtype: list
    :return: A list of :class:`boto.sdb.regioninfo.RegionInfo` instances
    """
    return get_regions(
        'sdb',
        region_cls=SDBRegionInfo
    )


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.sdb.connection.SDBConnection`.

    :type: str
    :param region_name: The name of the region to connect to.

    :rtype: :class:`boto.sdb.connection.SDBConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
             name is given
    """
    return connect('sdb', region_name, region_cls=SDBRegionInfo, **kw_params)
