# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import boto.vendored.regions.regions as _regions


class _CompatEndpointResolver(_regions.EndpointResolver):
    """Endpoint resolver which handles boto2 compatibility concerns.

    This is NOT intended for external use whatsoever.
    """

    _DEFAULT_SERVICE_RENAMES = {
        # The botocore resolver is based on endpoint prefix.
        # These don't always sync up to the name that boto2 uses.
        # A mapping can be provided that handles the mapping between
        # "service names" and endpoint prefixes.
        'awslambda': 'lambda',
        'cloudwatch': 'monitoring',
        'ses': 'email',
        'ec2containerservice': 'ecs',
        'configservice': 'config',
    }

    def __init__(self, endpoint_data, service_rename_map=None):
        """
        :type endpoint_data: dict
        :param endpoint_data: Regions and endpoints data in the same format
            as is used by botocore / boto3.

        :type service_rename_map: dict
        :param service_rename_map: A mapping of boto2 service name to
            endpoint prefix.
        """
        super(_CompatEndpointResolver, self).__init__(endpoint_data)
        if service_rename_map is None:
            service_rename_map = self._DEFAULT_SERVICE_RENAMES
        # Mapping of boto2 service name to endpoint prefix
        self._endpoint_prefix_map = service_rename_map
        # Mapping of endpoint prefix to boto2 service name
        self._service_name_map = dict(
            (v, k) for k, v in service_rename_map.items())

    def get_available_endpoints(self, service_name, partition_name='aws',
                                allow_non_regional=False):
        endpoint_prefix = self._endpoint_prefix(service_name)
        return super(_CompatEndpointResolver, self).get_available_endpoints(
            endpoint_prefix, partition_name, allow_non_regional)

    def get_all_available_regions(self, service_name):
        """Retrieve every region across partitions for a service."""
        regions = set()
        endpoint_prefix = self._endpoint_prefix(service_name)

        # Get every region for every partition in the new endpoint format
        for partition_name in self.get_available_partitions():
            if self._is_global_service(service_name, partition_name):
                # Global services are available in every region in the
                # partition in which they are considered global.
                partition = self._get_partition_data(partition_name)
                regions.update(partition['regions'].keys())
                continue
            else:
                regions.update(
                    self.get_available_endpoints(
                        endpoint_prefix, partition_name)
                )

        return list(regions)

    def construct_endpoint(self, service_name, region_name=None):
        endpoint_prefix = self._endpoint_prefix(service_name)
        return super(_CompatEndpointResolver, self).construct_endpoint(
            endpoint_prefix, region_name)

    def get_available_services(self):
        """Get a list of all the available services in the endpoints file(s)"""
        services = set()

        for partition in self._endpoint_data['partitions']:
            services.update(partition['services'].keys())

        return [self._service_name(s) for s in services]

    def _is_global_service(self, service_name, partition_name='aws'):
        """Determines whether a service uses a global endpoint.

        In theory a service can be 'global' in one partition but regional in
        another. In practice, each service is all global or all regional.
        """
        endpoint_prefix = self._endpoint_prefix(service_name)
        partition = self._get_partition_data(partition_name)
        service = partition['services'].get(endpoint_prefix, {})
        return 'partitionEndpoint' in service

    def _get_partition_data(self, partition_name):
        """Get partition information for a particular partition.

        This should NOT be used to get service endpoint data because it only
        loads from the new endpoint format. It should only be used for
        partition metadata and partition specific service metadata.

        :type partition_name: str
        :param partition_name: The name of the partition to search for.

        :returns: Partition info from the new endpoints format.
        :rtype: dict or None
        """
        for partition in self._endpoint_data['partitions']:
            if partition['partition'] == partition_name:
                return partition
        raise ValueError(
            "Could not find partition data for: %s" % partition_name)

    def _endpoint_prefix(self, service_name):
        """Given a boto2 service name, get the endpoint prefix."""
        return self._endpoint_prefix_map.get(service_name, service_name)

    def _service_name(self, endpoint_prefix):
        """Given an endpoint prefix, get the boto2 service name."""
        return self._service_name_map.get(endpoint_prefix, endpoint_prefix)


class BotoEndpointResolver(object):
    """Resolves endpoint hostnames for AWS services.

    This is NOT intended for external use.
    """

    def __init__(self, endpoint_data, service_rename_map=None):
        """
        :type endpoint_data: dict
        :param endpoint_data: Regions and endpoints data in the same format
            as is used by botocore / boto3.

        :type service_rename_map: dict
        :param service_rename_map: A mapping of boto2 service name to
            endpoint prefix.
        """
        self._resolver = _CompatEndpointResolver(
            endpoint_data, service_rename_map)

    def resolve_hostname(self, service_name, region_name):
        """Resolve the hostname for a service in a particular region.

        :type service_name: str
        :param service_name: The service to look up.

        :type region_name: str
        :param region_name: The region to find the endpoint for.

        :return: The hostname for the given service in the given region.
        """
        endpoint = self._resolver.construct_endpoint(service_name, region_name)
        if endpoint is None:
            return None
        return endpoint.get('sslCommonName', endpoint['hostname'])

    def get_all_available_regions(self, service_name):
        """Get all the regions a service is available in.

        :type service_name: str
        :param service_name: The service to look up.

        :rtype: list of str
        :return: A list of all the regions the given service is available in.
        """
        return self._resolver.get_all_available_regions(service_name)

    def get_available_services(self):
        """Get all the services supported by the endpoint data.

        :rtype: list of str
        :return: A list of all the services explicitly contained within the
            endpoint data provided during instantiation.
        """
        return self._resolver.get_available_services()


class StaticEndpointBuilder(object):
    """Builds a static mapping of endpoints in the legacy format."""

    def __init__(self, resolver):
        """
        :type resolver: BotoEndpointResolver
        :param resolver: An endpoint resolver.
        """
        self._resolver = resolver

    def build_static_endpoints(self, service_names=None):
        """Build a set of static endpoints in the legacy boto2 format.

        :param service_names: The names of the services to build. They must
            use the names that boto2 uses, not boto3, e.g "ec2containerservice"
            and not "ecs". If no service names are provided, all available
            services will be built.

        :return: A dict consisting of::
            {"service": {"region": "full.host.name"}}
        """
        if service_names is None:
            service_names = self._resolver.get_available_services()

        static_endpoints = {}
        for name in service_names:
            endpoints_for_service = self._build_endpoints_for_service(name)
            if endpoints_for_service:
                # It's possible that when we try to build endpoints for
                # services we get an empty hash.  In that case we don't
                # bother adding it to the final list of static endpoints.
                static_endpoints[name] = endpoints_for_service
        self._handle_special_cases(static_endpoints)
        return static_endpoints

    def _build_endpoints_for_service(self, service_name):
        # Given a service name, 'ec2', build a dict of
        # 'region' -> 'hostname'
        endpoints = {}
        regions = self._resolver.get_all_available_regions(service_name)
        for region_name in regions:
            endpoints[region_name] = self._resolver.resolve_hostname(
                service_name, region_name)
        return endpoints

    def _handle_special_cases(self, static_endpoints):
        # cloudsearchdomain endpoints use the exact same set of endpoints as
        # cloudsearch.
        if 'cloudsearch' in static_endpoints:
            cloudsearch_endpoints = static_endpoints['cloudsearch']
            static_endpoints['cloudsearchdomain'] = cloudsearch_endpoints
