# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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

# this is here for backward compatibility
# originally, the Route53Connection class was defined here
from boto.route53.connection import Route53Connection
from boto.regioninfo import RegionInfo, get_regions
from boto.regioninfo import connect


class Route53RegionInfo(RegionInfo):

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
    Get all available regions for the Route53 service.

    :rtype: list
    :return: A list of :class:`boto.regioninfo.RegionInfo` instances
    """
    regions = get_regions(
        'route53',
        region_cls=Route53RegionInfo,
        connection_cls=Route53Connection
    )

    # For historical reasons, we had a "universal" endpoint as well.
    regions.append(
        Route53RegionInfo(
            name='universal',
            endpoint='route53.amazonaws.com',
            connection_cls=Route53Connection
        )
    )

    return regions


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.route53.connection.Route53Connection`.

    :type: str
    :param region_name: The name of the region to connect to.

    :rtype: :class:`boto.route53.connection.Route53Connection` or ``None``
    :return: A connection to the given region, or None if an invalid region
             name is given
    """
    if region_name == 'universal':
        region = Route53RegionInfo(
            name='universal',
            endpoint='route53.amazonaws.com',
            connection_cls=Route53Connection
        )
        return region.connect(**kw_params)

    return connect('route53', region_name, region_cls=Route53RegionInfo,
                   connection_cls=Route53Connection, **kw_params)
