# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
import os

import boto
from boto.compat import json
from boto.exception import BotoClientError
from boto.endpoints import BotoEndpointResolver
from boto.endpoints import StaticEndpointBuilder


_endpoints_cache = {}


def load_endpoint_json(path):
    """
    Loads a given JSON file & returns it.

    :param path: The path to the JSON file
    :type path: string

    :returns: The loaded data
    """
    return _load_json_file(path)


def _load_json_file(path):
    """
    Loads a given JSON file & returns it.

    :param path: The path to the JSON file
    :type path: string

    :returns: The loaded data
    """
    with open(path, 'r') as endpoints_file:
        return json.load(endpoints_file)


def merge_endpoints(defaults, additions):
    """
    Given an existing set of endpoint data, this will deep-update it with
    any similarly structured data in the additions.

    :param defaults: The existing endpoints data
    :type defaults: dict

    :param defaults: The additional endpoints data
    :type defaults: dict

    :returns: The modified endpoints data
    :rtype: dict
    """
    # We can't just do an ``defaults.update(...)`` here, as that could
    # *overwrite* regions if present in both.
    # We'll iterate instead, essentially doing a deeper merge.
    for service, region_info in additions.items():
        # Set the default, if not present, to an empty dict.
        defaults.setdefault(service, {})
        defaults[service].update(region_info)

    return defaults


def load_regions():
    """
    Actually load the region/endpoint information from the JSON files.

    By default, this loads from the default included ``boto/endpoints.json``
    file.

    Users can override/extend this by supplying either a ``BOTO_ENDPOINTS``
    environment variable or a ``endpoints_path`` config variable, either of
    which should be an absolute path to the user's JSON file.

    :returns: The endpoints data
    :rtype: dict
    """
    # Load the defaults first.
    endpoints = _load_builtin_endpoints()
    additional_path = None

    # Try the ENV var. If not, check the config file.
    if os.environ.get('BOTO_ENDPOINTS'):
        additional_path = os.environ['BOTO_ENDPOINTS']
    elif boto.config.get('Boto', 'endpoints_path'):
        additional_path = boto.config.get('Boto', 'endpoints_path')

    # If there's a file provided, we'll load it & additively merge it into
    # the endpoints.
    if additional_path:
        additional = load_endpoint_json(additional_path)
        endpoints = merge_endpoints(endpoints, additional)

    return endpoints


def _load_builtin_endpoints(_cache=_endpoints_cache):
    """Loads the builtin endpoints in the legacy format."""
    # If there's a cached response, return it
    if _cache:
        return _cache

    # Load the endpoints file
    endpoints = _load_json_file(boto.ENDPOINTS_PATH)

    # Build the endpoints into the legacy format
    resolver = BotoEndpointResolver(endpoints)
    builder = StaticEndpointBuilder(resolver)
    endpoints = builder.build_static_endpoints()

    # Cache the endpoints and then return them
    _cache.update(endpoints)
    return _cache


def get_regions(service_name, region_cls=None, connection_cls=None):
    """
    Given a service name (like ``ec2``), returns a list of ``RegionInfo``
    objects for that service.

    This leverages the ``endpoints.json`` file (+ optional user overrides) to
    configure/construct all the objects.

    :param service_name: The name of the service to construct the ``RegionInfo``
        objects for. Ex: ``ec2``, ``s3``, ``sns``, etc.
    :type service_name: string

    :param region_cls: (Optional) The class to use when constructing. By
        default, this is ``RegionInfo``.
    :type region_cls: class

    :param connection_cls: (Optional) The connection class for the
        ``RegionInfo`` object. Providing this allows the ``connect`` method on
        the ``RegionInfo`` to work. Default is ``None`` (no connection).
    :type connection_cls: class

    :returns: A list of configured ``RegionInfo`` objects
    :rtype: list
    """
    endpoints = load_regions()

    if service_name not in endpoints:
        raise BotoClientError(
            "Service '%s' not found in endpoints." % service_name
        )

    if region_cls is None:
        region_cls = RegionInfo

    region_objs = []

    for region_name, endpoint in endpoints.get(service_name, {}).items():
        region_objs.append(
            region_cls(
                name=region_name,
                endpoint=endpoint,
                connection_cls=connection_cls
            )
        )

    return region_objs


def connect(service_name, region_name, region_cls=None,
            connection_cls=None, **kw_params):
    """Create a connection class for a given service in a given region.

    :param service_name: The name of the service to construct the
        ``RegionInfo`` object for, e.g. ``ec2``, ``s3``, etc.
    :type service_name: str

    :param region_name: The name of the region to connect to, e.g.
        ``us-west-2``, ``eu-central-1``, etc.
    :type region_name: str

    :param region_cls: (Optional) The class to use when constructing. By
        default, this is ``RegionInfo``.
    :type region_cls: class

    :param connection_cls: (Optional) The connection class for the
        ``RegionInfo`` object. Providing this allows the ``connect`` method on
        the ``RegionInfo`` to work. Default is ``None`` (no connection).
    :type connection_cls: class

    :returns: A configured connection class.
    """
    if region_cls is None:
        region_cls = RegionInfo
    region = _get_region(service_name, region_name, region_cls, connection_cls)

    if region is None and _use_endpoint_heuristics():
        region = _get_region_with_heuristics(
            service_name, region_name, region_cls, connection_cls
        )

    if region is None:
        return None

    return region.connect(**kw_params)


def _get_region(service_name, region_name, region_cls=None,
                connection_cls=None):
    """Finds the region by searching through the known regions."""
    for region in get_regions(service_name, region_cls, connection_cls):
        if region.name == region_name:
            return region
    return None


def _get_region_with_heuristics(service_name, region_name, region_cls=None,
                                connection_cls=None):
    """Finds the region using known regions and heuristics."""
    endpoints = load_endpoint_json(boto.ENDPOINTS_PATH)
    resolver = BotoEndpointResolver(endpoints)
    hostname = resolver.resolve_hostname(service_name, region_name)

    return region_cls(
        name=region_name,
        endpoint=hostname,
        connection_cls=connection_cls
    )


def _use_endpoint_heuristics():
    env_var = os.environ.get('BOTO_USE_ENDPOINT_HEURISTICS', 'false').lower()
    config_var = boto.config.getbool('Boto', 'use_endpoint_heuristics', False)
    return env_var == 'true' or config_var


class RegionInfo(object):
    """
    Represents an AWS Region
    """

    def __init__(self, connection=None, name=None, endpoint=None,
                 connection_cls=None):
        self.connection = connection
        self.name = name
        self.endpoint = endpoint
        self.connection_cls = connection_cls

    def __repr__(self):
        return 'RegionInfo:%s' % self.name

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'regionName':
            self.name = value
        elif name == 'regionEndpoint':
            self.endpoint = value
        else:
            setattr(self, name, value)

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
            return self.connection_cls(region=self, **kw_params)
