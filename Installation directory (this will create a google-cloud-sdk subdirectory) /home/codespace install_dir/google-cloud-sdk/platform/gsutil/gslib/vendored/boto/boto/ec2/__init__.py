# Copyright (c) 2006-2008 Mitch Garnaat http://garnaat.org/
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
"""
This module provides an interface to the Elastic Compute Cloud (EC2)
service from AWS.
"""
from boto.ec2.connection import EC2Connection
from boto.regioninfo import RegionInfo, get_regions, load_regions
from boto.regioninfo import connect


RegionData = load_regions().get('ec2', {})


def regions(**kw_params):
    """
    Get all available regions for the EC2 service.
    You may pass any of the arguments accepted by the EC2Connection
    object's constructor as keyword arguments and they will be
    passed along to the EC2Connection object.

    :rtype: list
    :return: A list of :class:`boto.ec2.regioninfo.RegionInfo`
    """
    return get_regions('ec2', connection_cls=EC2Connection)


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.ec2.connection.EC2Connection`.
    Any additional parameters after the region_name are passed on to
    the connect method of the region object.

    :type: str
    :param region_name: The name of the region to connect to.

    :rtype: :class:`boto.ec2.connection.EC2Connection` or ``None``
    :return: A connection to the given region, or None if an invalid region
             name is given
    """
    if 'region' in kw_params and isinstance(kw_params['region'], RegionInfo)\
       and region_name == kw_params['region'].name:
        return EC2Connection(**kw_params)

    return connect('ec2', region_name,
                   connection_cls=EC2Connection, **kw_params)


def get_region(region_name, **kw_params):
    """
    Find and return a :class:`boto.ec2.regioninfo.RegionInfo` object
    given a region name.

    :type: str
    :param: The name of the region.

    :rtype: :class:`boto.ec2.regioninfo.RegionInfo`
    :return: The RegionInfo object for the given region or None if
             an invalid region name is provided.
    """
    for region in regions(**kw_params):
        if region.name == region_name:
            return region
    return None
