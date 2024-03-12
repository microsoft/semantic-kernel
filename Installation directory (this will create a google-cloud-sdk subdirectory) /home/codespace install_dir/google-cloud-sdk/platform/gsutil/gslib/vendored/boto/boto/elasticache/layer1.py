# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import boto
from boto.compat import json
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo


class ElastiCacheConnection(AWSQueryConnection):
    """
    Amazon ElastiCache
    Amazon ElastiCache is a web service that makes it easier to set
    up, operate, and scale a distributed cache in the cloud.

    With ElastiCache, customers gain all of the benefits of a high-
    performance, in-memory cache with far less of the administrative
    burden of launching and managing a distributed cache. The service
    makes set-up, scaling, and cluster failure handling much simpler
    than in a self-managed cache deployment.

    In addition, through integration with Amazon CloudWatch, customers
    get enhanced visibility into the key performance statistics
    associated with their cache and can receive alarms if a part of
    their cache runs hot.
    """
    APIVersion = "2013-06-15"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "elasticache.us-east-1.amazonaws.com"

    def __init__(self, **kwargs):
        region = kwargs.get('region')
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        else:
            del kwargs['region']
        kwargs['host'] = region.endpoint
        super(ElastiCacheConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def authorize_cache_security_group_ingress(self,
                                               cache_security_group_name,
                                               ec2_security_group_name,
                                               ec2_security_group_owner_id):
        """
        The AuthorizeCacheSecurityGroupIngress operation allows
        network ingress to a cache security group. Applications using
        ElastiCache must be running on Amazon EC2, and Amazon EC2
        security groups are used as the authorization mechanism.
        You cannot authorize ingress from an Amazon EC2 security group
        in one Region to an ElastiCache cluster in another Region.

        :type cache_security_group_name: string
        :param cache_security_group_name: The cache security group which will
            allow network ingress.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The Amazon EC2 security group to be
            authorized for ingress to the cache security group.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The AWS account number of the
            Amazon EC2 security group owner. Note that this is not the same
            thing as an AWS access key ID - you must provide a valid AWS
            account number for this parameter.

        """
        params = {
            'CacheSecurityGroupName': cache_security_group_name,
            'EC2SecurityGroupName': ec2_security_group_name,
            'EC2SecurityGroupOwnerId': ec2_security_group_owner_id,
        }
        return self._make_request(
            action='AuthorizeCacheSecurityGroupIngress',
            verb='POST',
            path='/', params=params)

    def create_cache_cluster(self, cache_cluster_id, num_cache_nodes=None,
                             cache_node_type=None, engine=None,
                             replication_group_id=None, engine_version=None,
                             cache_parameter_group_name=None,
                             cache_subnet_group_name=None,
                             cache_security_group_names=None,
                             security_group_ids=None, snapshot_arns=None,
                             preferred_availability_zone=None,
                             preferred_maintenance_window=None, port=None,
                             notification_topic_arn=None,
                             auto_minor_version_upgrade=None):
        """
        The CreateCacheCluster operation creates a new cache cluster.
        All nodes in the cache cluster run the same protocol-compliant
        cache engine software - either Memcached or Redis.

        :type cache_cluster_id: string
        :param cache_cluster_id:
        The cache cluster identifier. This parameter is stored as a lowercase
            string.

        Constraints:


        + Must contain from 1 to 20 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type replication_group_id: string
        :param replication_group_id: The replication group to which this cache
            cluster should belong. If this parameter is specified, the cache
            cluster will be added to the specified replication group as a read
            replica; otherwise, the cache cluster will be a standalone primary
            that is not part of any replication group.

        :type num_cache_nodes: integer
        :param num_cache_nodes: The initial number of cache nodes that the
            cache cluster will have.
        For a Memcached cluster, valid values are between 1 and 20. If you need
            to exceed this limit, please fill out the ElastiCache Limit
            Increase Request form at ``_ .

        For Redis, only single-node cache clusters are supported at this time,
            so the value for this parameter must be 1.

        :type cache_node_type: string
        :param cache_node_type: The compute and memory capacity of the nodes in
            the cache cluster.
        Valid values for Memcached:

        `cache.t1.micro` | `cache.m1.small` | `cache.m1.medium` |
            `cache.m1.large` | `cache.m1.xlarge` | `cache.m3.xlarge` |
            `cache.m3.2xlarge` | `cache.m2.xlarge` | `cache.m2.2xlarge` |
            `cache.m2.4xlarge` | `cache.c1.xlarge`

        Valid values for Redis:

        `cache.t1.micro` | `cache.m1.small` | `cache.m1.medium` |
            `cache.m1.large` | `cache.m1.xlarge` | `cache.m2.xlarge` |
            `cache.m2.2xlarge` | `cache.m2.4xlarge` | `cache.c1.xlarge`

        For a complete listing of cache node types and specifications, see `.

        :type engine: string
        :param engine: The name of the cache engine to be used for this cache
            cluster.
        Valid values for this parameter are:

        `memcached` | `redis`

        :type engine_version: string
        :param engine_version: The version number of the cache engine to be
            used for this cluster. To view the supported cache engine versions,
            use the DescribeCacheEngineVersions operation.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of the cache parameter
            group to associate with this cache cluster. If this argument is
            omitted, the default cache parameter group for the specified engine
            will be used.

        :type cache_subnet_group_name: string
        :param cache_subnet_group_name: The name of the cache subnet group to
            be used for the cache cluster.
        Use this parameter only when you are creating a cluster in an Amazon
            Virtual Private Cloud (VPC).

        :type cache_security_group_names: list
        :param cache_security_group_names: A list of cache security group names
            to associate with this cache cluster.
        Use this parameter only when you are creating a cluster outside of an
            Amazon Virtual Private Cloud (VPC).

        :type security_group_ids: list
        :param security_group_ids: One or more VPC security groups associated
            with the cache cluster.
        Use this parameter only when you are creating a cluster in an Amazon
            Virtual Private Cloud (VPC).

        :type snapshot_arns: list
        :param snapshot_arns: A single-element string list containing an Amazon
            Resource Name (ARN) that uniquely identifies a Redis RDB snapshot
            file stored in Amazon S3. The snapshot file will be used to
            populate the Redis cache in the new cache cluster. The Amazon S3
            object name in the ARN cannot contain any commas.
        Here is an example of an Amazon S3 ARN:
            `arn:aws:s3:::my_bucket/snapshot1.rdb`

        **Note:** This parameter is only valid if the `Engine` parameter is
            `redis`.

        :type preferred_availability_zone: string
        :param preferred_availability_zone: The EC2 Availability Zone in which
            the cache cluster will be created.
        All cache nodes belonging to a cache cluster are placed in the
            preferred availability zone.

        Default: System chosen availability zone.

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which system maintenance can occur.
        Example: `sun:05:00-sun:09:00`

        :type port: integer
        :param port: The port number on which each of the cache nodes will
            accept connections.

        :type notification_topic_arn: string
        :param notification_topic_arn:
        The Amazon Resource Name (ARN) of the Amazon Simple Notification
            Service (SNS) topic to which notifications will be sent.

        The Amazon SNS topic owner must be the same as the cache cluster owner.

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Determines whether minor engine
            upgrades will be applied automatically to the cache cluster during
            the maintenance window. A value of `True` allows these upgrades to
            occur; `False` disables automatic upgrades.
        Default: `True`

        """
        params = {
            'CacheClusterId': cache_cluster_id,
        }
        if num_cache_nodes is not None:
            params['NumCacheNodes'] = num_cache_nodes
        if cache_node_type is not None:
            params['CacheNodeType'] = cache_node_type
        if engine is not None:
            params['Engine'] = engine
        if replication_group_id is not None:
            params['ReplicationGroupId'] = replication_group_id
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if cache_parameter_group_name is not None:
            params['CacheParameterGroupName'] = cache_parameter_group_name
        if cache_subnet_group_name is not None:
            params['CacheSubnetGroupName'] = cache_subnet_group_name
        if cache_security_group_names is not None:
            self.build_list_params(params,
                                   cache_security_group_names,
                                   'CacheSecurityGroupNames.member')
        if security_group_ids is not None:
            self.build_list_params(params,
                                   security_group_ids,
                                   'SecurityGroupIds.member')
        if snapshot_arns is not None:
            self.build_list_params(params,
                                   snapshot_arns,
                                   'SnapshotArns.member')
        if preferred_availability_zone is not None:
            params['PreferredAvailabilityZone'] = preferred_availability_zone
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if port is not None:
            params['Port'] = port
        if notification_topic_arn is not None:
            params['NotificationTopicArn'] = notification_topic_arn
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        return self._make_request(
            action='CreateCacheCluster',
            verb='POST',
            path='/', params=params)

    def create_cache_parameter_group(self, cache_parameter_group_name,
                                     cache_parameter_group_family,
                                     description):
        """
        The CreateCacheParameterGroup operation creates a new cache
        parameter group. A cache parameter group is a collection of
        parameters that you apply to all of the nodes in a cache
        cluster.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: A user-specified name for the cache
            parameter group.

        :type cache_parameter_group_family: string
        :param cache_parameter_group_family: The name of the cache parameter
            group family the cache parameter group can be used with.
        Valid values are: `memcached1.4` | `redis2.6`

        :type description: string
        :param description: A user-specified description for the cache
            parameter group.

        """
        params = {
            'CacheParameterGroupName': cache_parameter_group_name,
            'CacheParameterGroupFamily': cache_parameter_group_family,
            'Description': description,
        }
        return self._make_request(
            action='CreateCacheParameterGroup',
            verb='POST',
            path='/', params=params)

    def create_cache_security_group(self, cache_security_group_name,
                                    description):
        """
        The CreateCacheSecurityGroup operation creates a new cache
        security group. Use a cache security group to control access
        to one or more cache clusters.

        Cache security groups are only used when you are creating a
        cluster outside of an Amazon Virtual Private Cloud (VPC). If
        you are creating a cluster inside of a VPC, use a cache subnet
        group instead. For more information, see
        CreateCacheSubnetGroup .

        :type cache_security_group_name: string
        :param cache_security_group_name: A name for the cache security group.
            This value is stored as a lowercase string.
        Constraints: Must contain no more than 255 alphanumeric characters.
            Must not be the word "Default".

        Example: `mysecuritygroup`

        :type description: string
        :param description: A description for the cache security group.

        """
        params = {
            'CacheSecurityGroupName': cache_security_group_name,
            'Description': description,
        }
        return self._make_request(
            action='CreateCacheSecurityGroup',
            verb='POST',
            path='/', params=params)

    def create_cache_subnet_group(self, cache_subnet_group_name,
                                  cache_subnet_group_description, subnet_ids):
        """
        The CreateCacheSubnetGroup operation creates a new cache
        subnet group.

        Use this parameter only when you are creating a cluster in an
        Amazon Virtual Private Cloud (VPC).

        :type cache_subnet_group_name: string
        :param cache_subnet_group_name: A name for the cache subnet group. This
            value is stored as a lowercase string.
        Constraints: Must contain no more than 255 alphanumeric characters or
            hyphens.

        Example: `mysubnetgroup`

        :type cache_subnet_group_description: string
        :param cache_subnet_group_description: A description for the cache
            subnet group.

        :type subnet_ids: list
        :param subnet_ids: A list of VPC subnet IDs for the cache subnet group.

        """
        params = {
            'CacheSubnetGroupName': cache_subnet_group_name,
            'CacheSubnetGroupDescription': cache_subnet_group_description,
        }
        self.build_list_params(params,
                               subnet_ids,
                               'SubnetIds.member')
        return self._make_request(
            action='CreateCacheSubnetGroup',
            verb='POST',
            path='/', params=params)

    def create_replication_group(self, replication_group_id,
                                 primary_cluster_id,
                                 replication_group_description):
        """
        The CreateReplicationGroup operation creates a replication
        group. A replication group is a collection of cache clusters,
        where one of the clusters is a read/write primary and the
        other clusters are read-only replicas. Writes to the primary
        are automatically propagated to the replicas.

        When you create a replication group, you must specify an
        existing cache cluster that is in the primary role. When the
        replication group has been successfully created, you can add
        one or more read replica replicas to it, up to a total of five
        read replicas.

        :type replication_group_id: string
        :param replication_group_id:
        The replication group identifier. This parameter is stored as a
            lowercase string.

        Constraints:


        + Must contain from 1 to 20 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type primary_cluster_id: string
        :param primary_cluster_id: The identifier of the cache cluster that
            will serve as the primary for this replication group. This cache
            cluster must already exist and have a status of available .

        :type replication_group_description: string
        :param replication_group_description: A user-specified description for
            the replication group.

        """
        params = {
            'ReplicationGroupId': replication_group_id,
            'PrimaryClusterId': primary_cluster_id,
            'ReplicationGroupDescription': replication_group_description,
        }
        return self._make_request(
            action='CreateReplicationGroup',
            verb='POST',
            path='/', params=params)

    def delete_cache_cluster(self, cache_cluster_id):
        """
        The DeleteCacheCluster operation deletes a previously
        provisioned cache cluster. DeleteCacheCluster deletes all
        associated cache nodes, node endpoints and the cache cluster
        itself. When you receive a successful response from this
        operation, Amazon ElastiCache immediately begins deleting the
        cache cluster; you cannot cancel or revert this operation.

        :type cache_cluster_id: string
        :param cache_cluster_id: The cache cluster identifier for the cluster
            to be deleted. This parameter is not case sensitive.

        """
        params = {'CacheClusterId': cache_cluster_id, }
        return self._make_request(
            action='DeleteCacheCluster',
            verb='POST',
            path='/', params=params)

    def delete_cache_parameter_group(self, cache_parameter_group_name):
        """
        The DeleteCacheParameterGroup operation deletes the specified
        cache parameter group. You cannot delete a cache parameter
        group if it is associated with any cache clusters.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name:
        The name of the cache parameter group to delete.

        The specified cache security group must not be associated with any
            cache clusters.

        """
        params = {
            'CacheParameterGroupName': cache_parameter_group_name,
        }
        return self._make_request(
            action='DeleteCacheParameterGroup',
            verb='POST',
            path='/', params=params)

    def delete_cache_security_group(self, cache_security_group_name):
        """
        The DeleteCacheSecurityGroup operation deletes a cache
        security group.
        You cannot delete a cache security group if it is associated
        with any cache clusters.

        :type cache_security_group_name: string
        :param cache_security_group_name:
        The name of the cache security group to delete.

        You cannot delete the default security group.

        """
        params = {
            'CacheSecurityGroupName': cache_security_group_name,
        }
        return self._make_request(
            action='DeleteCacheSecurityGroup',
            verb='POST',
            path='/', params=params)

    def delete_cache_subnet_group(self, cache_subnet_group_name):
        """
        The DeleteCacheSubnetGroup operation deletes a cache subnet
        group.
        You cannot delete a cache subnet group if it is associated
        with any cache clusters.

        :type cache_subnet_group_name: string
        :param cache_subnet_group_name: The name of the cache subnet group to
            delete.
        Constraints: Must contain no more than 255 alphanumeric characters or
            hyphens.

        """
        params = {'CacheSubnetGroupName': cache_subnet_group_name, }
        return self._make_request(
            action='DeleteCacheSubnetGroup',
            verb='POST',
            path='/', params=params)

    def delete_replication_group(self, replication_group_id):
        """
        The DeleteReplicationGroup operation deletes an existing
        replication group. DeleteReplicationGroup deletes the primary
        cache cluster and all of the read replicas in the replication
        group. When you receive a successful response from this
        operation, Amazon ElastiCache immediately begins deleting the
        entire replication group; you cannot cancel or revert this
        operation.

        :type replication_group_id: string
        :param replication_group_id: The identifier for the replication group
            to be deleted. This parameter is not case sensitive.

        """
        params = {'ReplicationGroupId': replication_group_id, }
        return self._make_request(
            action='DeleteReplicationGroup',
            verb='POST',
            path='/', params=params)

    def describe_cache_clusters(self, cache_cluster_id=None,
                                max_records=None, marker=None,
                                show_cache_node_info=None):
        """
        The DescribeCacheClusters operation returns information about
        all provisioned cache clusters if no cache cluster identifier
        is specified, or about a specific cache cluster if a cache
        cluster identifier is supplied.

        By default, abbreviated information about the cache
        clusters(s) will be returned. You can use the optional
        ShowDetails flag to retrieve detailed information about the
        cache nodes associated with the cache clusters. These details
        include the DNS address and port for the cache node endpoint.

        If the cluster is in the CREATING state, only cluster level
        information will be displayed until all of the nodes are
        successfully provisioned.

        If the cluster is in the DELETING state, only cluster level
        information will be displayed.

        If cache nodes are currently being added to the cache cluster,
        node endpoint information and creation time for the additional
        nodes will not be displayed until they are completely
        provisioned. When the cache cluster state is available , the
        cluster is ready for use.

        If cache nodes are currently being removed from the cache
        cluster, no endpoint information for the removed nodes is
        displayed.

        :type cache_cluster_id: string
        :param cache_cluster_id: The user-supplied cluster identifier. If this
            parameter is specified, only information about that specific cache
            cluster is returned. This parameter isn't case sensitive.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        :type show_cache_node_info: boolean
        :param show_cache_node_info: An optional flag that can be included in
            the DescribeCacheCluster request to retrieve information about the
            individual cache nodes.

        """
        params = {}
        if cache_cluster_id is not None:
            params['CacheClusterId'] = cache_cluster_id
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        if show_cache_node_info is not None:
            params['ShowCacheNodeInfo'] = str(
                show_cache_node_info).lower()
        return self._make_request(
            action='DescribeCacheClusters',
            verb='POST',
            path='/', params=params)

    def describe_cache_engine_versions(self, engine=None,
                                       engine_version=None,
                                       cache_parameter_group_family=None,
                                       max_records=None, marker=None,
                                       default_only=None):
        """
        The DescribeCacheEngineVersions operation returns a list of
        the available cache engines and their versions.

        :type engine: string
        :param engine: The cache engine to return. Valid values: `memcached` |
            `redis`

        :type engine_version: string
        :param engine_version: The cache engine version to return.
        Example: `1.4.14`

        :type cache_parameter_group_family: string
        :param cache_parameter_group_family:
        The name of a specific cache parameter group family to return details
            for.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        :type default_only: boolean
        :param default_only: If true , specifies that only the default version
            of the specified engine or engine and major version combination is
            to be returned.

        """
        params = {}
        if engine is not None:
            params['Engine'] = engine
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if cache_parameter_group_family is not None:
            params['CacheParameterGroupFamily'] = cache_parameter_group_family
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        if default_only is not None:
            params['DefaultOnly'] = str(
                default_only).lower()
        return self._make_request(
            action='DescribeCacheEngineVersions',
            verb='POST',
            path='/', params=params)

    def describe_cache_parameter_groups(self,
                                        cache_parameter_group_name=None,
                                        max_records=None, marker=None):
        """
        The DescribeCacheParameterGroups operation returns a list of
        cache parameter group descriptions. If a cache parameter group
        name is specified, the list will contain only the descriptions
        for that group.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of a specific cache
            parameter group to return details for.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if cache_parameter_group_name is not None:
            params['CacheParameterGroupName'] = cache_parameter_group_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeCacheParameterGroups',
            verb='POST',
            path='/', params=params)

    def describe_cache_parameters(self, cache_parameter_group_name,
                                  source=None, max_records=None, marker=None):
        """
        The DescribeCacheParameters operation returns the detailed
        parameter list for a particular cache parameter group.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of a specific cache
            parameter group to return details for.

        :type source: string
        :param source: The parameter types to return.
        Valid values: `user` | `system` | `engine-default`

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {
            'CacheParameterGroupName': cache_parameter_group_name,
        }
        if source is not None:
            params['Source'] = source
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeCacheParameters',
            verb='POST',
            path='/', params=params)

    def describe_cache_security_groups(self, cache_security_group_name=None,
                                       max_records=None, marker=None):
        """
        The DescribeCacheSecurityGroups operation returns a list of
        cache security group descriptions. If a cache security group
        name is specified, the list will contain only the description
        of that group.

        :type cache_security_group_name: string
        :param cache_security_group_name: The name of the cache security group
            to return details for.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if cache_security_group_name is not None:
            params['CacheSecurityGroupName'] = cache_security_group_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeCacheSecurityGroups',
            verb='POST',
            path='/', params=params)

    def describe_cache_subnet_groups(self, cache_subnet_group_name=None,
                                     max_records=None, marker=None):
        """
        The DescribeCacheSubnetGroups operation returns a list of
        cache subnet group descriptions. If a subnet group name is
        specified, the list will contain only the description of that
        group.

        :type cache_subnet_group_name: string
        :param cache_subnet_group_name: The name of the cache subnet group to
            return details for.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if cache_subnet_group_name is not None:
            params['CacheSubnetGroupName'] = cache_subnet_group_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeCacheSubnetGroups',
            verb='POST',
            path='/', params=params)

    def describe_engine_default_parameters(self,
                                           cache_parameter_group_family,
                                           max_records=None, marker=None):
        """
        The DescribeEngineDefaultParameters operation returns the
        default engine and system parameter information for the
        specified cache engine.

        :type cache_parameter_group_family: string
        :param cache_parameter_group_family: The name of the cache parameter
            group family. Valid values are: `memcached1.4` | `redis2.6`

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {
            'CacheParameterGroupFamily': cache_parameter_group_family,
        }
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeEngineDefaultParameters',
            verb='POST',
            path='/', params=params)

    def describe_events(self, source_identifier=None, source_type=None,
                        start_time=None, end_time=None, duration=None,
                        max_records=None, marker=None):
        """
        The DescribeEvents operation returns events related to cache
        clusters, cache security groups, and cache parameter groups.
        You can obtain events specific to a particular cache cluster,
        cache security group, or cache parameter group by providing
        the name as a parameter.

        By default, only the events occurring within the last hour are
        returned; however, you can retrieve up to 14 days' worth of
        events if necessary.

        :type source_identifier: string
        :param source_identifier: The identifier of the event source for which
            events will be returned. If not specified, then all sources are
            included in the response.

        :type source_type: string
        :param source_type: The event source to retrieve events for. If no
            value is specified, all events are returned.
        Valid values are: `cache-cluster` | `cache-parameter-group` | `cache-
            security-group` | `cache-subnet-group`

        :type start_time: timestamp
        :param start_time: The beginning of the time interval to retrieve
            events for, specified in ISO 8601 format.

        :type end_time: timestamp
        :param end_time: The end of the time interval for which to retrieve
            events, specified in ISO 8601 format.

        :type duration: integer
        :param duration: The number of minutes' worth of events to retrieve.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if source_identifier is not None:
            params['SourceIdentifier'] = source_identifier
        if source_type is not None:
            params['SourceType'] = source_type
        if start_time is not None:
            params['StartTime'] = start_time
        if end_time is not None:
            params['EndTime'] = end_time
        if duration is not None:
            params['Duration'] = duration
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeEvents',
            verb='POST',
            path='/', params=params)

    def describe_replication_groups(self, replication_group_id=None,
                                    max_records=None, marker=None):
        """
        The DescribeReplicationGroups operation returns information
        about a particular replication group. If no identifier is
        specified, DescribeReplicationGroups returns information about
        all replication groups.

        :type replication_group_id: string
        :param replication_group_id: The identifier for the replication group
            to be described. This parameter is not case sensitive.
        If you do not specify this parameter, information about all replication
            groups is returned.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if replication_group_id is not None:
            params['ReplicationGroupId'] = replication_group_id
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReplicationGroups',
            verb='POST',
            path='/', params=params)

    def describe_reserved_cache_nodes(self, reserved_cache_node_id=None,
                                      reserved_cache_nodes_offering_id=None,
                                      cache_node_type=None, duration=None,
                                      product_description=None,
                                      offering_type=None, max_records=None,
                                      marker=None):
        """
        The DescribeReservedCacheNodes operation returns information
        about reserved cache nodes for this account, or about a
        specified reserved cache node.

        :type reserved_cache_node_id: string
        :param reserved_cache_node_id: The reserved cache node identifier
            filter value. Use this parameter to show only the reservation that
            matches the specified reservation ID.

        :type reserved_cache_nodes_offering_id: string
        :param reserved_cache_nodes_offering_id: The offering identifier filter
            value. Use this parameter to show only purchased reservations
            matching the specified offering identifier.

        :type cache_node_type: string
        :param cache_node_type: The cache node type filter value. Use this
            parameter to show only those reservations matching the specified
            cache node type.

        :type duration: string
        :param duration: The duration filter value, specified in years or
            seconds. Use this parameter to show only reservations for this
            duration.
        Valid Values: `1 | 3 | 31536000 | 94608000`

        :type product_description: string
        :param product_description: The product description filter value. Use
            this parameter to show only those reservations matching the
            specified product description.

        :type offering_type: string
        :param offering_type: The offering type filter value. Use this
            parameter to show only the available offerings matching the
            specified offering type.
        Valid values: `"Light Utilization" | "Medium Utilization" | "Heavy
            Utilization" `

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if reserved_cache_node_id is not None:
            params['ReservedCacheNodeId'] = reserved_cache_node_id
        if reserved_cache_nodes_offering_id is not None:
            params['ReservedCacheNodesOfferingId'] = reserved_cache_nodes_offering_id
        if cache_node_type is not None:
            params['CacheNodeType'] = cache_node_type
        if duration is not None:
            params['Duration'] = duration
        if product_description is not None:
            params['ProductDescription'] = product_description
        if offering_type is not None:
            params['OfferingType'] = offering_type
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReservedCacheNodes',
            verb='POST',
            path='/', params=params)

    def describe_reserved_cache_nodes_offerings(self,
                                                reserved_cache_nodes_offering_id=None,
                                                cache_node_type=None,
                                                duration=None,
                                                product_description=None,
                                                offering_type=None,
                                                max_records=None,
                                                marker=None):
        """
        The DescribeReservedCacheNodesOfferings operation lists
        available reserved cache node offerings.

        :type reserved_cache_nodes_offering_id: string
        :param reserved_cache_nodes_offering_id: The offering identifier filter
            value. Use this parameter to show only the available offering that
            matches the specified reservation identifier.
        Example: `438012d3-4052-4cc7-b2e3-8d3372e0e706`

        :type cache_node_type: string
        :param cache_node_type: The cache node type filter value. Use this
            parameter to show only the available offerings matching the
            specified cache node type.

        :type duration: string
        :param duration: Duration filter value, specified in years or seconds.
            Use this parameter to show only reservations for a given duration.
        Valid Values: `1 | 3 | 31536000 | 94608000`

        :type product_description: string
        :param product_description: The product description filter value. Use
            this parameter to show only the available offerings matching the
            specified product description.

        :type offering_type: string
        :param offering_type: The offering type filter value. Use this
            parameter to show only the available offerings matching the
            specified offering type.
        Valid Values: `"Light Utilization" | "Medium Utilization" | "Heavy
            Utilization" `

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a marker is included in the response so that the remaining
            results can be retrieved.
        Default: 100

        Constraints: minimum 20; maximum 100.

        :type marker: string
        :param marker: An optional marker returned from a prior request. Use
            this marker for pagination of results from this operation. If this
            parameter is specified, the response includes only records beyond
            the marker, up to the value specified by MaxRecords .

        """
        params = {}
        if reserved_cache_nodes_offering_id is not None:
            params['ReservedCacheNodesOfferingId'] = reserved_cache_nodes_offering_id
        if cache_node_type is not None:
            params['CacheNodeType'] = cache_node_type
        if duration is not None:
            params['Duration'] = duration
        if product_description is not None:
            params['ProductDescription'] = product_description
        if offering_type is not None:
            params['OfferingType'] = offering_type
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReservedCacheNodesOfferings',
            verb='POST',
            path='/', params=params)

    def modify_cache_cluster(self, cache_cluster_id, num_cache_nodes=None,
                             cache_node_ids_to_remove=None,
                             cache_security_group_names=None,
                             security_group_ids=None,
                             preferred_maintenance_window=None,
                             notification_topic_arn=None,
                             cache_parameter_group_name=None,
                             notification_topic_status=None,
                             apply_immediately=None, engine_version=None,
                             auto_minor_version_upgrade=None):
        """
        The ModifyCacheCluster operation modifies the settings for a
        cache cluster. You can use this operation to change one or
        more cluster configuration parameters by specifying the
        parameters and the new values.

        :type cache_cluster_id: string
        :param cache_cluster_id: The cache cluster identifier. This value is
            stored as a lowercase string.

        :type num_cache_nodes: integer
        :param num_cache_nodes: The number of cache nodes that the cache
            cluster should have. If the value for NumCacheNodes is greater than
            the existing number of cache nodes, then more nodes will be added.
            If the value is less than the existing number of cache nodes, then
            cache nodes will be removed.
        If you are removing cache nodes, you must use the CacheNodeIdsToRemove
            parameter to provide the IDs of the specific cache nodes to be
            removed.

        :type cache_node_ids_to_remove: list
        :param cache_node_ids_to_remove: A list of cache node IDs to be
            removed. A node ID is a numeric identifier (0001, 0002, etc.). This
            parameter is only valid when NumCacheNodes is less than the
            existing number of cache nodes. The number of cache node IDs
            supplied in this parameter must match the difference between the
            existing number of cache nodes in the cluster and the value of
            NumCacheNodes in the request.

        :type cache_security_group_names: list
        :param cache_security_group_names: A list of cache security group names
            to authorize on this cache cluster. This change is asynchronously
            applied as soon as possible.
        This parameter can be used only with clusters that are created outside
            of an Amazon Virtual Private Cloud (VPC).

        Constraints: Must contain no more than 255 alphanumeric characters.
            Must not be "Default".

        :type security_group_ids: list
        :param security_group_ids: Specifies the VPC Security Groups associated
            with the cache cluster.
        This parameter can be used only with clusters that are created in an
            Amazon Virtual Private Cloud (VPC).

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which system maintenance can occur. Note that system
            maintenance may result in an outage. This change is made
            immediately. If you are moving this window to the current time,
            there must be at least 120 minutes between the current time and end
            of the window to ensure that pending changes are applied.

        :type notification_topic_arn: string
        :param notification_topic_arn:
        The Amazon Resource Name (ARN) of the SNS topic to which notifications
            will be sent.

        The SNS topic owner must be same as the cache cluster owner.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of the cache parameter
            group to apply to this cache cluster. This change is asynchronously
            applied as soon as possible for parameters when the
            ApplyImmediately parameter is specified as true for this request.

        :type notification_topic_status: string
        :param notification_topic_status: The status of the Amazon SNS
            notification topic. Notifications are sent only if the status is
            active .
        Valid values: `active` | `inactive`

        :type apply_immediately: boolean
        :param apply_immediately: If `True`, this parameter causes the
            modifications in this request and any pending modifications to be
            applied, asynchronously and as soon as possible, regardless of the
            PreferredMaintenanceWindow setting for the cache cluster.
        If `False`, then changes to the cache cluster are applied on the next
            maintenance reboot, or the next failure reboot, whichever occurs
            first.

        Valid values: `True` | `False`

        Default: `False`

        :type engine_version: string
        :param engine_version: The upgraded version of the cache engine to be
            run on the cache cluster nodes.

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: If `True`, then minor engine
            upgrades will be applied automatically to the cache cluster during
            the maintenance window.
        Valid values: `True` | `False`

        Default: `True`

        """
        params = {'CacheClusterId': cache_cluster_id, }
        if num_cache_nodes is not None:
            params['NumCacheNodes'] = num_cache_nodes
        if cache_node_ids_to_remove is not None:
            self.build_list_params(params,
                                   cache_node_ids_to_remove,
                                   'CacheNodeIdsToRemove.member')
        if cache_security_group_names is not None:
            self.build_list_params(params,
                                   cache_security_group_names,
                                   'CacheSecurityGroupNames.member')
        if security_group_ids is not None:
            self.build_list_params(params,
                                   security_group_ids,
                                   'SecurityGroupIds.member')
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if notification_topic_arn is not None:
            params['NotificationTopicArn'] = notification_topic_arn
        if cache_parameter_group_name is not None:
            params['CacheParameterGroupName'] = cache_parameter_group_name
        if notification_topic_status is not None:
            params['NotificationTopicStatus'] = notification_topic_status
        if apply_immediately is not None:
            params['ApplyImmediately'] = str(
                apply_immediately).lower()
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        return self._make_request(
            action='ModifyCacheCluster',
            verb='POST',
            path='/', params=params)

    def modify_cache_parameter_group(self, cache_parameter_group_name,
                                     parameter_name_values):
        """
        The ModifyCacheParameterGroup operation modifies the
        parameters of a cache parameter group. You can modify up to 20
        parameters in a single request by submitting a list parameter
        name and value pairs.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of the cache parameter
            group to modify.

        :type parameter_name_values: list
        :param parameter_name_values: An array of parameter names and values
            for the parameter update. You must supply at least one parameter
            name and value; subsequent arguments are optional. A maximum of 20
            parameters may be modified per request.

        """
        params = {
            'CacheParameterGroupName': cache_parameter_group_name,
        }
        self.build_complex_list_params(
            params, parameter_name_values,
            'ParameterNameValues.member',
            ('ParameterName', 'ParameterValue'))
        return self._make_request(
            action='ModifyCacheParameterGroup',
            verb='POST',
            path='/', params=params)

    def modify_cache_subnet_group(self, cache_subnet_group_name,
                                  cache_subnet_group_description=None,
                                  subnet_ids=None):
        """
        The ModifyCacheSubnetGroup operation modifies an existing
        cache subnet group.

        :type cache_subnet_group_name: string
        :param cache_subnet_group_name: The name for the cache subnet group.
            This value is stored as a lowercase string.
        Constraints: Must contain no more than 255 alphanumeric characters or
            hyphens.

        Example: `mysubnetgroup`

        :type cache_subnet_group_description: string
        :param cache_subnet_group_description: A description for the cache
            subnet group.

        :type subnet_ids: list
        :param subnet_ids: The EC2 subnet IDs for the cache subnet group.

        """
        params = {'CacheSubnetGroupName': cache_subnet_group_name, }
        if cache_subnet_group_description is not None:
            params['CacheSubnetGroupDescription'] = cache_subnet_group_description
        if subnet_ids is not None:
            self.build_list_params(params,
                                   subnet_ids,
                                   'SubnetIds.member')
        return self._make_request(
            action='ModifyCacheSubnetGroup',
            verb='POST',
            path='/', params=params)

    def modify_replication_group(self, replication_group_id,
                                 replication_group_description=None,
                                 cache_security_group_names=None,
                                 security_group_ids=None,
                                 preferred_maintenance_window=None,
                                 notification_topic_arn=None,
                                 cache_parameter_group_name=None,
                                 notification_topic_status=None,
                                 apply_immediately=None, engine_version=None,
                                 auto_minor_version_upgrade=None,
                                 primary_cluster_id=None):
        """
        The ModifyReplicationGroup operation modifies the settings for
        a replication group.

        :type replication_group_id: string
        :param replication_group_id: The identifier of the replication group to
            modify.

        :type replication_group_description: string
        :param replication_group_description: A description for the replication
            group. Maximum length is 255 characters.

        :type cache_security_group_names: list
        :param cache_security_group_names: A list of cache security group names
            to authorize for the clusters in this replication group. This
            change is asynchronously applied as soon as possible.
        This parameter can be used only with replication groups containing
            cache clusters running outside of an Amazon Virtual Private Cloud
            (VPC).

        Constraints: Must contain no more than 255 alphanumeric characters.
            Must not be "Default".

        :type security_group_ids: list
        :param security_group_ids: Specifies the VPC Security Groups associated
            with the cache clusters in the replication group.
        This parameter can be used only with replication groups containing
            cache clusters running in an Amazon Virtual Private Cloud (VPC).

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which replication group system maintenance can occur. Note
            that system maintenance may result in an outage. This change is
            made immediately. If you are moving this window to the current
            time, there must be at least 120 minutes between the current time
            and end of the window to ensure that pending changes are applied.

        :type notification_topic_arn: string
        :param notification_topic_arn:
        The Amazon Resource Name (ARN) of the SNS topic to which notifications
            will be sent.

        The SNS topic owner must be same as the replication group owner.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of the cache parameter
            group to apply to all of the cache nodes in this replication group.
            This change is asynchronously applied as soon as possible for
            parameters when the ApplyImmediately parameter is specified as true
            for this request.

        :type notification_topic_status: string
        :param notification_topic_status: The status of the Amazon SNS
            notification topic for the replication group. Notifications are
            sent only if the status is active .
        Valid values: `active` | `inactive`

        :type apply_immediately: boolean
        :param apply_immediately: If `True`, this parameter causes the
            modifications in this request and any pending modifications to be
            applied, asynchronously and as soon as possible, regardless of the
            PreferredMaintenanceWindow setting for the replication group.
        If `False`, then changes to the nodes in the replication group are
            applied on the next maintenance reboot, or the next failure reboot,
            whichever occurs first.

        Valid values: `True` | `False`

        Default: `False`

        :type engine_version: string
        :param engine_version: The upgraded version of the cache engine to be
            run on the nodes in the replication group..

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Determines whether minor engine
            upgrades will be applied automatically to all of the cache nodes in
            the replication group during the maintenance window. A value of
            `True` allows these upgrades to occur; `False` disables automatic
            upgrades.

        :type primary_cluster_id: string
        :param primary_cluster_id: If this parameter is specified, ElastiCache
            will promote each of the nodes in the specified cache cluster to
            the primary role. The nodes of all other clusters in the
            replication group will be read replicas.

        """
        params = {'ReplicationGroupId': replication_group_id, }
        if replication_group_description is not None:
            params['ReplicationGroupDescription'] = replication_group_description
        if cache_security_group_names is not None:
            self.build_list_params(params,
                                   cache_security_group_names,
                                   'CacheSecurityGroupNames.member')
        if security_group_ids is not None:
            self.build_list_params(params,
                                   security_group_ids,
                                   'SecurityGroupIds.member')
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if notification_topic_arn is not None:
            params['NotificationTopicArn'] = notification_topic_arn
        if cache_parameter_group_name is not None:
            params['CacheParameterGroupName'] = cache_parameter_group_name
        if notification_topic_status is not None:
            params['NotificationTopicStatus'] = notification_topic_status
        if apply_immediately is not None:
            params['ApplyImmediately'] = str(
                apply_immediately).lower()
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        if primary_cluster_id is not None:
            params['PrimaryClusterId'] = primary_cluster_id
        return self._make_request(
            action='ModifyReplicationGroup',
            verb='POST',
            path='/', params=params)

    def purchase_reserved_cache_nodes_offering(self,
                                               reserved_cache_nodes_offering_id,
                                               reserved_cache_node_id=None,
                                               cache_node_count=None):
        """
        The PurchaseReservedCacheNodesOffering operation allows you to
        purchase a reserved cache node offering.

        :type reserved_cache_nodes_offering_id: string
        :param reserved_cache_nodes_offering_id: The ID of the reserved cache
            node offering to purchase.
        Example: 438012d3-4052-4cc7-b2e3-8d3372e0e706

        :type reserved_cache_node_id: string
        :param reserved_cache_node_id: A customer-specified identifier to track
            this reservation.
        Example: myreservationID

        :type cache_node_count: integer
        :param cache_node_count: The number of cache node instances to reserve.
        Default: `1`

        """
        params = {
            'ReservedCacheNodesOfferingId': reserved_cache_nodes_offering_id,
        }
        if reserved_cache_node_id is not None:
            params['ReservedCacheNodeId'] = reserved_cache_node_id
        if cache_node_count is not None:
            params['CacheNodeCount'] = cache_node_count
        return self._make_request(
            action='PurchaseReservedCacheNodesOffering',
            verb='POST',
            path='/', params=params)

    def reboot_cache_cluster(self, cache_cluster_id,
                             cache_node_ids_to_reboot):
        """
        The RebootCacheCluster operation reboots some, or all, of the
        cache cluster nodes within a provisioned cache cluster. This
        API will apply any modified cache parameter groups to the
        cache cluster. The reboot action takes place as soon as
        possible, and results in a momentary outage to the cache
        cluster. During the reboot, the cache cluster status is set to
        REBOOTING.

        The reboot causes the contents of the cache (for each cache
        cluster node being rebooted) to be lost.

        When the reboot is complete, a cache cluster event is created.

        :type cache_cluster_id: string
        :param cache_cluster_id: The cache cluster identifier. This parameter
            is stored as a lowercase string.

        :type cache_node_ids_to_reboot: list
        :param cache_node_ids_to_reboot: A list of cache cluster node IDs to
            reboot. A node ID is a numeric identifier (0001, 0002, etc.). To
            reboot an entire cache cluster, specify all of the cache cluster
            node IDs.

        """
        params = {'CacheClusterId': cache_cluster_id, }
        self.build_list_params(params,
                               cache_node_ids_to_reboot,
                               'CacheNodeIdsToReboot.member')
        return self._make_request(
            action='RebootCacheCluster',
            verb='POST',
            path='/', params=params)

    def reset_cache_parameter_group(self, cache_parameter_group_name,
                                    parameter_name_values,
                                    reset_all_parameters=None):
        """
        The ResetCacheParameterGroup operation modifies the parameters
        of a cache parameter group to the engine or system default
        value. You can reset specific parameters by submitting a list
        of parameter names. To reset the entire cache parameter group,
        specify the ResetAllParameters and CacheParameterGroupName
        parameters.

        :type cache_parameter_group_name: string
        :param cache_parameter_group_name: The name of the cache parameter
            group to reset.

        :type reset_all_parameters: boolean
        :param reset_all_parameters: If true , all parameters in the cache
            parameter group will be reset to default values. If false , no such
            action occurs.
        Valid values: `True` | `False`

        :type parameter_name_values: list
        :param parameter_name_values: An array of parameter names to be reset.
            If you are not resetting the entire cache parameter group, you must
            specify at least one parameter name.

        """
        params = {
            'CacheParameterGroupName': cache_parameter_group_name,
        }
        self.build_complex_list_params(
            params, parameter_name_values,
            'ParameterNameValues.member',
            ('ParameterName', 'ParameterValue'))
        if reset_all_parameters is not None:
            params['ResetAllParameters'] = str(
                reset_all_parameters).lower()
        return self._make_request(
            action='ResetCacheParameterGroup',
            verb='POST',
            path='/', params=params)

    def revoke_cache_security_group_ingress(self, cache_security_group_name,
                                            ec2_security_group_name,
                                            ec2_security_group_owner_id):
        """
        The RevokeCacheSecurityGroupIngress operation revokes ingress
        from a cache security group. Use this operation to disallow
        access from an Amazon EC2 security group that had been
        previously authorized.

        :type cache_security_group_name: string
        :param cache_security_group_name: The name of the cache security group
            to revoke ingress from.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The name of the Amazon EC2 security
            group to revoke access from.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The AWS account number of the
            Amazon EC2 security group owner. Note that this is not the same
            thing as an AWS access key ID - you must provide a valid AWS
            account number for this parameter.

        """
        params = {
            'CacheSecurityGroupName': cache_security_group_name,
            'EC2SecurityGroupName': ec2_security_group_name,
            'EC2SecurityGroupOwnerId': ec2_security_group_owner_id,
        }
        return self._make_request(
            action='RevokeCacheSecurityGroupIngress',
            verb='POST',
            path='/', params=params)

    def _make_request(self, action, verb, path, params):
        params['ContentType'] = 'JSON'
        response = self.make_request(action=action, verb='POST',
                                     path='/', params=params)
        body = response.read().decode('utf-8')
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            raise self.ResponseError(response.status, response.reason, body)
