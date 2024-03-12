# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.exception import JSONResponseError
from boto.redshift import exceptions


class RedshiftConnection(AWSQueryConnection):
    """
    Amazon Redshift **Overview**
    This is an interface reference for Amazon Redshift. It contains
    documentation for one of the programming or command line
    interfaces you can use to manage Amazon Redshift clusters. Note
    that Amazon Redshift is asynchronous, which means that some
    interfaces may require techniques, such as polling or asynchronous
    callback handlers, to determine when a command has been applied.
    In this reference, the parameter descriptions indicate whether a
    change is applied immediately, on the next instance reboot, or
    during the next maintenance window. For a summary of the Amazon
    Redshift cluster management interfaces, go to `Using the Amazon
    Redshift Management Interfaces `_.

    Amazon Redshift manages all the work of setting up, operating, and
    scaling a data warehouse: provisioning capacity, monitoring and
    backing up the cluster, and applying patches and upgrades to the
    Amazon Redshift engine. You can focus on using your data to
    acquire new insights for your business and customers.

    If you are a first-time user of Amazon Redshift, we recommend that
    you begin by reading the The `Amazon Redshift Getting Started
    Guide`_

    If you are a database developer, the `Amazon Redshift Database
    Developer Guide`_ explains how to design, build, query, and
    maintain the databases that make up your data warehouse.
    """
    APIVersion = "2012-12-01"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "redshift.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "SnapshotCopyAlreadyDisabled": exceptions.SnapshotCopyAlreadyDisabled,
        "ClusterNotFound": exceptions.ClusterNotFound,
        "UnknownSnapshotCopyRegion": exceptions.UnknownSnapshotCopyRegion,
        "InvalidClusterSubnetState": exceptions.InvalidClusterSubnetState,
        "InvalidSubnet": exceptions.InvalidSubnet,
        "ReservedNodeQuotaExceeded": exceptions.ReservedNodeQuotaExceeded,
        "InvalidClusterState": exceptions.InvalidClusterState,
        "HsmClientCertificateQuotaExceeded": exceptions.HsmClientCertificateQuotaExceeded,
        "SubscriptionCategoryNotFound": exceptions.SubscriptionCategoryNotFound,
        "HsmClientCertificateNotFound": exceptions.HsmClientCertificateNotFound,
        "SubscriptionEventIdNotFound": exceptions.SubscriptionEventIdNotFound,
        "ClusterSecurityGroupAlreadyExists": exceptions.ClusterSecurityGroupAlreadyExists,
        "HsmConfigurationAlreadyExists": exceptions.HsmConfigurationAlreadyExists,
        "NumberOfNodesQuotaExceeded": exceptions.NumberOfNodesQuotaExceeded,
        "ReservedNodeOfferingNotFound": exceptions.ReservedNodeOfferingNotFound,
        "BucketNotFound": exceptions.BucketNotFound,
        "InsufficientClusterCapacity": exceptions.InsufficientClusterCapacity,
        "InvalidRestore": exceptions.InvalidRestore,
        "UnauthorizedOperation": exceptions.UnauthorizedOperation,
        "ClusterQuotaExceeded": exceptions.ClusterQuotaExceeded,
        "InvalidVPCNetworkState": exceptions.InvalidVPCNetworkState,
        "ClusterSnapshotNotFound": exceptions.ClusterSnapshotNotFound,
        "AuthorizationQuotaExceeded": exceptions.AuthorizationQuotaExceeded,
        "InvalidHsmClientCertificateState": exceptions.InvalidHsmClientCertificateState,
        "SNSTopicArnNotFound": exceptions.SNSTopicArnNotFound,
        "ResizeNotFound": exceptions.ResizeNotFound,
        "ClusterSubnetGroupNotFound": exceptions.ClusterSubnetGroupNotFound,
        "SNSNoAuthorization": exceptions.SNSNoAuthorization,
        "ClusterSnapshotQuotaExceeded": exceptions.ClusterSnapshotQuotaExceeded,
        "AccessToSnapshotDenied": exceptions.AccessToSnapshotDenied,
        "InvalidClusterSecurityGroupState": exceptions.InvalidClusterSecurityGroupState,
        "NumberOfNodesPerClusterLimitExceeded": exceptions.NumberOfNodesPerClusterLimitExceeded,
        "ClusterSubnetQuotaExceeded": exceptions.ClusterSubnetQuotaExceeded,
        "SNSInvalidTopic": exceptions.SNSInvalidTopic,
        "ClusterSecurityGroupNotFound": exceptions.ClusterSecurityGroupNotFound,
        "InvalidElasticIp": exceptions.InvalidElasticIp,
        "InvalidClusterParameterGroupState": exceptions.InvalidClusterParameterGroupState,
        "InvalidHsmConfigurationState": exceptions.InvalidHsmConfigurationState,
        "ClusterAlreadyExists": exceptions.ClusterAlreadyExists,
        "HsmConfigurationQuotaExceeded": exceptions.HsmConfigurationQuotaExceeded,
        "ClusterSnapshotAlreadyExists": exceptions.ClusterSnapshotAlreadyExists,
        "SubscriptionSeverityNotFound": exceptions.SubscriptionSeverityNotFound,
        "SourceNotFound": exceptions.SourceNotFound,
        "ReservedNodeAlreadyExists": exceptions.ReservedNodeAlreadyExists,
        "ClusterSubnetGroupQuotaExceeded": exceptions.ClusterSubnetGroupQuotaExceeded,
        "ClusterParameterGroupNotFound": exceptions.ClusterParameterGroupNotFound,
        "InvalidS3BucketName": exceptions.InvalidS3BucketName,
        "InvalidS3KeyPrefix": exceptions.InvalidS3KeyPrefix,
        "SubscriptionAlreadyExist": exceptions.SubscriptionAlreadyExist,
        "HsmConfigurationNotFound": exceptions.HsmConfigurationNotFound,
        "InvalidSubscriptionState": exceptions.InvalidSubscriptionState,
        "AuthorizationNotFound": exceptions.AuthorizationNotFound,
        "ClusterSecurityGroupQuotaExceeded": exceptions.ClusterSecurityGroupQuotaExceeded,
        "SubnetAlreadyInUse": exceptions.SubnetAlreadyInUse,
        "EventSubscriptionQuotaExceeded": exceptions.EventSubscriptionQuotaExceeded,
        "AuthorizationAlreadyExists": exceptions.AuthorizationAlreadyExists,
        "InvalidClusterSnapshotState": exceptions.InvalidClusterSnapshotState,
        "ClusterParameterGroupQuotaExceeded": exceptions.ClusterParameterGroupQuotaExceeded,
        "SnapshotCopyDisabled": exceptions.SnapshotCopyDisabled,
        "ClusterSubnetGroupAlreadyExists": exceptions.ClusterSubnetGroupAlreadyExists,
        "ReservedNodeNotFound": exceptions.ReservedNodeNotFound,
        "HsmClientCertificateAlreadyExists": exceptions.HsmClientCertificateAlreadyExists,
        "InvalidClusterSubnetGroupState": exceptions.InvalidClusterSubnetGroupState,
        "SubscriptionNotFound": exceptions.SubscriptionNotFound,
        "InsufficientS3BucketPolicy": exceptions.InsufficientS3BucketPolicy,
        "ClusterParameterGroupAlreadyExists": exceptions.ClusterParameterGroupAlreadyExists,
        "UnsupportedOption": exceptions.UnsupportedOption,
        "CopyToRegionDisabled": exceptions.CopyToRegionDisabled,
        "SnapshotCopyAlreadyEnabled": exceptions.SnapshotCopyAlreadyEnabled,
        "IncompatibleOrderableOptions": exceptions.IncompatibleOrderableOptions,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(RedshiftConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def authorize_cluster_security_group_ingress(self,
                                                 cluster_security_group_name,
                                                 cidrip=None,
                                                 ec2_security_group_name=None,
                                                 ec2_security_group_owner_id=None):
        """
        Adds an inbound (ingress) rule to an Amazon Redshift security
        group. Depending on whether the application accessing your
        cluster is running on the Internet or an EC2 instance, you can
        authorize inbound access to either a Classless Interdomain
        Routing (CIDR) IP address range or an EC2 security group. You
        can add as many as 20 ingress rules to an Amazon Redshift
        security group.

        For an overview of CIDR blocks, see the Wikipedia article on
        `Classless Inter-Domain Routing`_.

        You must also associate the security group with a cluster so
        that clients running on these IP addresses or the EC2 instance
        are authorized to connect to the cluster. For information
        about managing security groups, go to `Working with Security
        Groups`_ in the Amazon Redshift Management Guide .

        :type cluster_security_group_name: string
        :param cluster_security_group_name: The name of the security group to
            which the ingress rule is added.

        :type cidrip: string
        :param cidrip: The IP range to be added the Amazon Redshift security
            group.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The EC2 security group to be added the
            Amazon Redshift security group.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The AWS account number of the owner
            of the security group specified by the EC2SecurityGroupName
            parameter. The AWS Access Key ID is not an acceptable value.
        Example: `111122223333`

        """
        params = {
            'ClusterSecurityGroupName': cluster_security_group_name,
        }
        if cidrip is not None:
            params['CIDRIP'] = cidrip
        if ec2_security_group_name is not None:
            params['EC2SecurityGroupName'] = ec2_security_group_name
        if ec2_security_group_owner_id is not None:
            params['EC2SecurityGroupOwnerId'] = ec2_security_group_owner_id
        return self._make_request(
            action='AuthorizeClusterSecurityGroupIngress',
            verb='POST',
            path='/', params=params)

    def authorize_snapshot_access(self, snapshot_identifier,
                                  account_with_restore_access,
                                  snapshot_cluster_identifier=None):
        """
        Authorizes the specified AWS customer account to restore the
        specified snapshot.

        For more information about working with snapshots, go to
        `Amazon Redshift Snapshots`_ in the Amazon Redshift Management
        Guide .

        :type snapshot_identifier: string
        :param snapshot_identifier: The identifier of the snapshot the account
            is authorized to restore.

        :type snapshot_cluster_identifier: string
        :param snapshot_cluster_identifier: The identifier of the cluster the
            snapshot was created from. This parameter is required if your IAM
            user has a policy containing a snapshot resource element that
            specifies anything other than * for the cluster name.

        :type account_with_restore_access: string
        :param account_with_restore_access: The identifier of the AWS customer
            account authorized to restore the specified snapshot.

        """
        params = {
            'SnapshotIdentifier': snapshot_identifier,
            'AccountWithRestoreAccess': account_with_restore_access,
        }
        if snapshot_cluster_identifier is not None:
            params['SnapshotClusterIdentifier'] = snapshot_cluster_identifier
        return self._make_request(
            action='AuthorizeSnapshotAccess',
            verb='POST',
            path='/', params=params)

    def copy_cluster_snapshot(self, source_snapshot_identifier,
                              target_snapshot_identifier,
                              source_snapshot_cluster_identifier=None):
        """
        Copies the specified automated cluster snapshot to a new
        manual cluster snapshot. The source must be an automated
        snapshot and it must be in the available state.

        When you delete a cluster, Amazon Redshift deletes any
        automated snapshots of the cluster. Also, when the retention
        period of the snapshot expires, Amazon Redshift automatically
        deletes it. If you want to keep an automated snapshot for a
        longer period, you can make a manual copy of the snapshot.
        Manual snapshots are retained until you delete them.

        For more information about working with snapshots, go to
        `Amazon Redshift Snapshots`_ in the Amazon Redshift Management
        Guide .

        :type source_snapshot_identifier: string
        :param source_snapshot_identifier:
        The identifier for the source snapshot.

        Constraints:


        + Must be the identifier for a valid automated snapshot whose state is
              `available`.

        :type source_snapshot_cluster_identifier: string
        :param source_snapshot_cluster_identifier:
        The identifier of the cluster the source snapshot was created from.
            This parameter is required if your IAM user has a policy containing
            a snapshot resource element that specifies anything other than *
            for the cluster name.

        Constraints:


        + Must be the identifier for a valid cluster.

        :type target_snapshot_identifier: string
        :param target_snapshot_identifier:
        The identifier given to the new manual snapshot.

        Constraints:


        + Cannot be null, empty, or blank.
        + Must contain from 1 to 255 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.
        + Must be unique for the AWS account that is making the request.

        """
        params = {
            'SourceSnapshotIdentifier': source_snapshot_identifier,
            'TargetSnapshotIdentifier': target_snapshot_identifier,
        }
        if source_snapshot_cluster_identifier is not None:
            params['SourceSnapshotClusterIdentifier'] = source_snapshot_cluster_identifier
        return self._make_request(
            action='CopyClusterSnapshot',
            verb='POST',
            path='/', params=params)

    def create_cluster(self, cluster_identifier, node_type, master_username,
                       master_user_password, db_name=None, cluster_type=None,
                       cluster_security_groups=None,
                       vpc_security_group_ids=None,
                       cluster_subnet_group_name=None,
                       availability_zone=None,
                       preferred_maintenance_window=None,
                       cluster_parameter_group_name=None,
                       automated_snapshot_retention_period=None, port=None,
                       cluster_version=None, allow_version_upgrade=None,
                       number_of_nodes=None, publicly_accessible=None,
                       encrypted=None,
                       hsm_client_certificate_identifier=None,
                       hsm_configuration_identifier=None, elastic_ip=None):
        """
        Creates a new cluster. To create the cluster in virtual
        private cloud (VPC), you must provide cluster subnet group
        name. If you don't provide a cluster subnet group name or the
        cluster security group parameter, Amazon Redshift creates a
        non-VPC cluster, it associates the default cluster security
        group with the cluster. For more information about managing
        clusters, go to `Amazon Redshift Clusters`_ in the Amazon
        Redshift Management Guide .

        :type db_name: string
        :param db_name:
        The name of the first database to be created when the cluster is
            created.

        To create additional databases after the cluster is created, connect to
            the cluster with a SQL client and use SQL commands to create a
            database. For more information, go to `Create a Database`_ in the
            Amazon Redshift Database Developer Guide.

        Default: `dev`

        Constraints:


        + Must contain 1 to 64 alphanumeric characters.
        + Must contain only lowercase letters.
        + Cannot be a word that is reserved by the service. A list of reserved
              words can be found in `Reserved Words`_ in the Amazon Redshift
              Database Developer Guide.

        :type cluster_identifier: string
        :param cluster_identifier: A unique identifier for the cluster. You use
            this identifier to refer to the cluster for any subsequent cluster
            operations such as deleting or modifying. The identifier also
            appears in the Amazon Redshift console.
        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens.
        + Alphabetic characters must be lowercase.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.
        + Must be unique for all clusters within an AWS account.


        Example: `myexamplecluster`

        :type cluster_type: string
        :param cluster_type: The type of the cluster. When cluster type is
            specified as

        + `single-node`, the **NumberOfNodes** parameter is not required.
        + `multi-node`, the **NumberOfNodes** parameter is required.


        Valid Values: `multi-node` | `single-node`

        Default: `multi-node`

        :type node_type: string
        :param node_type: The node type to be provisioned for the cluster. For
            information about node types, go to ` Working with Clusters`_ in
            the Amazon Redshift Management Guide .
        Valid Values: `dw1.xlarge` | `dw1.8xlarge` | `dw2.large` |
            `dw2.8xlarge`.

        :type master_username: string
        :param master_username:
        The user name associated with the master user account for the cluster
            that is being created.

        Constraints:


        + Must be 1 - 128 alphanumeric characters.
        + First character must be a letter.
        + Cannot be a reserved word. A list of reserved words can be found in
              `Reserved Words`_ in the Amazon Redshift Database Developer Guide.

        :type master_user_password: string
        :param master_user_password:
        The password associated with the master user account for the cluster
            that is being created.

        Constraints:


        + Must be between 8 and 64 characters in length.
        + Must contain at least one uppercase letter.
        + Must contain at least one lowercase letter.
        + Must contain one number.
        + Can be any printable ASCII character (ASCII code 33 to 126) except '
              (single quote), " (double quote), \, /, @, or space.

        :type cluster_security_groups: list
        :param cluster_security_groups: A list of security groups to be
            associated with this cluster.
        Default: The default cluster security group for Amazon Redshift.

        :type vpc_security_group_ids: list
        :param vpc_security_group_ids: A list of Virtual Private Cloud (VPC)
            security groups to be associated with the cluster.
        Default: The default VPC security group is associated with the cluster.

        :type cluster_subnet_group_name: string
        :param cluster_subnet_group_name: The name of a cluster subnet group to
            be associated with this cluster.
        If this parameter is not provided the resulting cluster will be
            deployed outside virtual private cloud (VPC).

        :type availability_zone: string
        :param availability_zone: The EC2 Availability Zone (AZ) in which you
            want Amazon Redshift to provision the cluster. For example, if you
            have several EC2 instances running in a specific Availability Zone,
            then you might want the cluster to be provisioned in the same zone
            in order to decrease network latency.
        Default: A random, system-chosen Availability Zone in the region that
            is specified by the endpoint.

        Example: `us-east-1d`

        Constraint: The specified Availability Zone must be in the same region
            as the current endpoint.

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which automated cluster maintenance can occur.
        Format: `ddd:hh24:mi-ddd:hh24:mi`

        Default: A 30-minute window selected at random from an 8-hour block of
            time per region, occurring on a random day of the week. The
            following list shows the time blocks for each region from which the
            default maintenance windows are assigned.


        + **US-East (Northern Virginia) Region:** 03:00-11:00 UTC
        + **US-West (Oregon) Region** 06:00-14:00 UTC
        + **EU (Ireland) Region** 22:00-06:00 UTC
        + **Asia Pacific (Singapore) Region** 14:00-22:00 UTC
        + **Asia Pacific (Sydney) Region** 12:00-20:00 UTC
        + **Asia Pacific (Tokyo) Region** 17:00-03:00 UTC


        Valid Days: Mon | Tue | Wed | Thu | Fri | Sat | Sun

        Constraints: Minimum 30-minute window.

        :type cluster_parameter_group_name: string
        :param cluster_parameter_group_name:
        The name of the parameter group to be associated with this cluster.

        Default: The default Amazon Redshift cluster parameter group. For
            information about the default parameter group, go to `Working with
            Amazon Redshift Parameter Groups`_

        Constraints:


        + Must be 1 to 255 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type automated_snapshot_retention_period: integer
        :param automated_snapshot_retention_period: The number of days that
            automated snapshots are retained. If the value is 0, automated
            snapshots are disabled. Even if automated snapshots are disabled,
            you can still create manual snapshots when you want with
            CreateClusterSnapshot.
        Default: `1`

        Constraints: Must be a value from 0 to 35.

        :type port: integer
        :param port: The port number on which the cluster accepts incoming
            connections.
        The cluster is accessible only via the JDBC and ODBC connection
            strings. Part of the connection string requires the port on which
            the cluster will listen for incoming connections.

        Default: `5439`

        Valid Values: `1150-65535`

        :type cluster_version: string
        :param cluster_version: The version of the Amazon Redshift engine
            software that you want to deploy on the cluster.
        The version selected runs on all the nodes in the cluster.

        Constraints: Only version 1.0 is currently available.

        Example: `1.0`

        :type allow_version_upgrade: boolean
        :param allow_version_upgrade: If `True`, upgrades can be applied during
            the maintenance window to the Amazon Redshift engine that is
            running on the cluster.
        When a new version of the Amazon Redshift engine is released, you can
            request that the service automatically apply upgrades during the
            maintenance window to the Amazon Redshift engine that is running on
            your cluster.

        Default: `True`

        :type number_of_nodes: integer
        :param number_of_nodes: The number of compute nodes in the cluster.
            This parameter is required when the **ClusterType** parameter is
            specified as `multi-node`.
        For information about determining how many nodes you need, go to `
            Working with Clusters`_ in the Amazon Redshift Management Guide .

        If you don't specify this parameter, you get a single-node cluster.
            When requesting a multi-node cluster, you must specify the number
            of nodes that you want in the cluster.

        Default: `1`

        Constraints: Value must be at least 1 and no more than 100.

        :type publicly_accessible: boolean
        :param publicly_accessible: If `True`, the cluster can be accessed from
            a public network.

        :type encrypted: boolean
        :param encrypted: If `True`, the data in the cluster is encrypted at
            rest.
        Default: false

        :type hsm_client_certificate_identifier: string
        :param hsm_client_certificate_identifier: Specifies the name of the HSM
            client certificate the Amazon Redshift cluster uses to retrieve the
            data encryption keys stored in an HSM.

        :type hsm_configuration_identifier: string
        :param hsm_configuration_identifier: Specifies the name of the HSM
            configuration that contains the information the Amazon Redshift
            cluster can use to retrieve and store keys in an HSM.

        :type elastic_ip: string
        :param elastic_ip: The Elastic IP (EIP) address for the cluster.
        Constraints: The cluster must be provisioned in EC2-VPC and publicly-
            accessible through an Internet gateway. For more information about
            provisioning clusters in EC2-VPC, go to `Supported Platforms to
            Launch Your Cluster`_ in the Amazon Redshift Management Guide.

        """
        params = {
            'ClusterIdentifier': cluster_identifier,
            'NodeType': node_type,
            'MasterUsername': master_username,
            'MasterUserPassword': master_user_password,
        }
        if db_name is not None:
            params['DBName'] = db_name
        if cluster_type is not None:
            params['ClusterType'] = cluster_type
        if cluster_security_groups is not None:
            self.build_list_params(params,
                                   cluster_security_groups,
                                   'ClusterSecurityGroups.member')
        if vpc_security_group_ids is not None:
            self.build_list_params(params,
                                   vpc_security_group_ids,
                                   'VpcSecurityGroupIds.member')
        if cluster_subnet_group_name is not None:
            params['ClusterSubnetGroupName'] = cluster_subnet_group_name
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if cluster_parameter_group_name is not None:
            params['ClusterParameterGroupName'] = cluster_parameter_group_name
        if automated_snapshot_retention_period is not None:
            params['AutomatedSnapshotRetentionPeriod'] = automated_snapshot_retention_period
        if port is not None:
            params['Port'] = port
        if cluster_version is not None:
            params['ClusterVersion'] = cluster_version
        if allow_version_upgrade is not None:
            params['AllowVersionUpgrade'] = str(
                allow_version_upgrade).lower()
        if number_of_nodes is not None:
            params['NumberOfNodes'] = number_of_nodes
        if publicly_accessible is not None:
            params['PubliclyAccessible'] = str(
                publicly_accessible).lower()
        if encrypted is not None:
            params['Encrypted'] = str(
                encrypted).lower()
        if hsm_client_certificate_identifier is not None:
            params['HsmClientCertificateIdentifier'] = hsm_client_certificate_identifier
        if hsm_configuration_identifier is not None:
            params['HsmConfigurationIdentifier'] = hsm_configuration_identifier
        if elastic_ip is not None:
            params['ElasticIp'] = elastic_ip
        return self._make_request(
            action='CreateCluster',
            verb='POST',
            path='/', params=params)

    def create_cluster_parameter_group(self, parameter_group_name,
                                       parameter_group_family, description):
        """
        Creates an Amazon Redshift parameter group.

        Creating parameter groups is independent of creating clusters.
        You can associate a cluster with a parameter group when you
        create the cluster. You can also associate an existing cluster
        with a parameter group after the cluster is created by using
        ModifyCluster.

        Parameters in the parameter group define specific behavior
        that applies to the databases you create on the cluster. For
        more information about managing parameter groups, go to
        `Amazon Redshift Parameter Groups`_ in the Amazon Redshift
        Management Guide .

        :type parameter_group_name: string
        :param parameter_group_name:
        The name of the cluster parameter group.

        Constraints:


        + Must be 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.
        + Must be unique within your AWS account.

        This value is stored as a lower-case string.

        :type parameter_group_family: string
        :param parameter_group_family: The Amazon Redshift engine version to
            which the cluster parameter group applies. The cluster engine
            version determines the set of parameters.
        To get a list of valid parameter group family names, you can call
            DescribeClusterParameterGroups. By default, Amazon Redshift returns
            a list of all the parameter groups that are owned by your AWS
            account, including the default parameter groups for each Amazon
            Redshift engine version. The parameter group family names
            associated with the default parameter groups provide you the valid
            values. For example, a valid family name is "redshift-1.0".

        :type description: string
        :param description: A description of the parameter group.

        """
        params = {
            'ParameterGroupName': parameter_group_name,
            'ParameterGroupFamily': parameter_group_family,
            'Description': description,
        }
        return self._make_request(
            action='CreateClusterParameterGroup',
            verb='POST',
            path='/', params=params)

    def create_cluster_security_group(self, cluster_security_group_name,
                                      description):
        """
        Creates a new Amazon Redshift security group. You use security
        groups to control access to non-VPC clusters.

        For information about managing security groups, go to `Amazon
        Redshift Cluster Security Groups`_ in the Amazon Redshift
        Management Guide .

        :type cluster_security_group_name: string
        :param cluster_security_group_name: The name for the security group.
            Amazon Redshift stores the value as a lowercase string.
        Constraints:


        + Must contain no more than 255 alphanumeric characters or hyphens.
        + Must not be "Default".
        + Must be unique for all security groups that are created by your AWS
              account.


        Example: `examplesecuritygroup`

        :type description: string
        :param description: A description for the security group.

        """
        params = {
            'ClusterSecurityGroupName': cluster_security_group_name,
            'Description': description,
        }
        return self._make_request(
            action='CreateClusterSecurityGroup',
            verb='POST',
            path='/', params=params)

    def create_cluster_snapshot(self, snapshot_identifier,
                                cluster_identifier):
        """
        Creates a manual snapshot of the specified cluster. The
        cluster must be in the `available` state.

        For more information about working with snapshots, go to
        `Amazon Redshift Snapshots`_ in the Amazon Redshift Management
        Guide .

        :type snapshot_identifier: string
        :param snapshot_identifier: A unique identifier for the snapshot that
            you are requesting. This identifier must be unique for all
            snapshots within the AWS account.
        Constraints:


        + Cannot be null, empty, or blank
        + Must contain from 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        Example: `my-snapshot-id`

        :type cluster_identifier: string
        :param cluster_identifier: The cluster identifier for which you want a
            snapshot.

        """
        params = {
            'SnapshotIdentifier': snapshot_identifier,
            'ClusterIdentifier': cluster_identifier,
        }
        return self._make_request(
            action='CreateClusterSnapshot',
            verb='POST',
            path='/', params=params)

    def create_cluster_subnet_group(self, cluster_subnet_group_name,
                                    description, subnet_ids):
        """
        Creates a new Amazon Redshift subnet group. You must provide a
        list of one or more subnets in your existing Amazon Virtual
        Private Cloud (Amazon VPC) when creating Amazon Redshift
        subnet group.

        For information about subnet groups, go to `Amazon Redshift
        Cluster Subnet Groups`_ in the Amazon Redshift Management
        Guide .

        :type cluster_subnet_group_name: string
        :param cluster_subnet_group_name: The name for the subnet group. Amazon
            Redshift stores the value as a lowercase string.
        Constraints:


        + Must contain no more than 255 alphanumeric characters or hyphens.
        + Must not be "Default".
        + Must be unique for all subnet groups that are created by your AWS
              account.


        Example: `examplesubnetgroup`

        :type description: string
        :param description: A description for the subnet group.

        :type subnet_ids: list
        :param subnet_ids: An array of VPC subnet IDs. A maximum of 20 subnets
            can be modified in a single request.

        """
        params = {
            'ClusterSubnetGroupName': cluster_subnet_group_name,
            'Description': description,
        }
        self.build_list_params(params,
                               subnet_ids,
                               'SubnetIds.member')
        return self._make_request(
            action='CreateClusterSubnetGroup',
            verb='POST',
            path='/', params=params)

    def create_event_subscription(self, subscription_name, sns_topic_arn,
                                  source_type=None, source_ids=None,
                                  event_categories=None, severity=None,
                                  enabled=None):
        """
        Creates an Amazon Redshift event notification subscription.
        This action requires an ARN (Amazon Resource Name) of an
        Amazon SNS topic created by either the Amazon Redshift
        console, the Amazon SNS console, or the Amazon SNS API. To
        obtain an ARN with Amazon SNS, you must create a topic in
        Amazon SNS and subscribe to the topic. The ARN is displayed in
        the SNS console.

        You can specify the source type, and lists of Amazon Redshift
        source IDs, event categories, and event severities.
        Notifications will be sent for all events you want that match
        those criteria. For example, you can specify source type =
        cluster, source ID = my-cluster-1 and mycluster2, event
        categories = Availability, Backup, and severity = ERROR. The
        subscription will only send notifications for those ERROR
        events in the Availability and Backup categories for the
        specified clusters.

        If you specify both the source type and source IDs, such as
        source type = cluster and source identifier = my-cluster-1,
        notifications will be sent for all the cluster events for my-
        cluster-1. If you specify a source type but do not specify a
        source identifier, you will receive notice of the events for
        the objects of that type in your AWS account. If you do not
        specify either the SourceType nor the SourceIdentifier, you
        will be notified of events generated from all Amazon Redshift
        sources belonging to your AWS account. You must specify a
        source type if you specify a source ID.

        :type subscription_name: string
        :param subscription_name:
        The name of the event subscription to be created.

        Constraints:


        + Cannot be null, empty, or blank.
        + Must contain from 1 to 255 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type sns_topic_arn: string
        :param sns_topic_arn: The Amazon Resource Name (ARN) of the Amazon SNS
            topic used to transmit the event notifications. The ARN is created
            by Amazon SNS when you create a topic and subscribe to it.

        :type source_type: string
        :param source_type: The type of source that will be generating the
            events. For example, if you want to be notified of events generated
            by a cluster, you would set this parameter to cluster. If this
            value is not specified, events are returned for all Amazon Redshift
            objects in your AWS account. You must specify a source type in
            order to specify source IDs.
        Valid values: cluster, cluster-parameter-group, cluster-security-group,
            and cluster-snapshot.

        :type source_ids: list
        :param source_ids: A list of one or more identifiers of Amazon Redshift
            source objects. All of the objects must be of the same type as was
            specified in the source type parameter. The event subscription will
            return only events generated by the specified objects. If not
            specified, then events are returned for all objects within the
            source type specified.
        Example: my-cluster-1, my-cluster-2

        Example: my-snapshot-20131010

        :type event_categories: list
        :param event_categories: Specifies the Amazon Redshift event categories
            to be published by the event notification subscription.
        Values: Configuration, Management, Monitoring, Security

        :type severity: string
        :param severity: Specifies the Amazon Redshift event severity to be
            published by the event notification subscription.
        Values: ERROR, INFO

        :type enabled: boolean
        :param enabled: A Boolean value; set to `True` to activate the
            subscription, set to `False` to create the subscription but not
            active it.

        """
        params = {
            'SubscriptionName': subscription_name,
            'SnsTopicArn': sns_topic_arn,
        }
        if source_type is not None:
            params['SourceType'] = source_type
        if source_ids is not None:
            self.build_list_params(params,
                                   source_ids,
                                   'SourceIds.member')
        if event_categories is not None:
            self.build_list_params(params,
                                   event_categories,
                                   'EventCategories.member')
        if severity is not None:
            params['Severity'] = severity
        if enabled is not None:
            params['Enabled'] = str(
                enabled).lower()
        return self._make_request(
            action='CreateEventSubscription',
            verb='POST',
            path='/', params=params)

    def create_hsm_client_certificate(self,
                                      hsm_client_certificate_identifier):
        """
        Creates an HSM client certificate that an Amazon Redshift
        cluster will use to connect to the client's HSM in order to
        store and retrieve the keys used to encrypt the cluster
        databases.

        The command returns a public key, which you must store in the
        HSM. In addition to creating the HSM certificate, you must
        create an Amazon Redshift HSM configuration that provides a
        cluster the information needed to store and use encryption
        keys in the HSM. For more information, go to `Hardware
        Security Modules`_ in the Amazon Redshift Management Guide.

        :type hsm_client_certificate_identifier: string
        :param hsm_client_certificate_identifier: The identifier to be assigned
            to the new HSM client certificate that the cluster will use to
            connect to the HSM to use the database encryption keys.

        """
        params = {
            'HsmClientCertificateIdentifier': hsm_client_certificate_identifier,
        }
        return self._make_request(
            action='CreateHsmClientCertificate',
            verb='POST',
            path='/', params=params)

    def create_hsm_configuration(self, hsm_configuration_identifier,
                                 description, hsm_ip_address,
                                 hsm_partition_name, hsm_partition_password,
                                 hsm_server_public_certificate):
        """
        Creates an HSM configuration that contains the information
        required by an Amazon Redshift cluster to store and use
        database encryption keys in a Hardware Security Module (HSM).
        After creating the HSM configuration, you can specify it as a
        parameter when creating a cluster. The cluster will then store
        its encryption keys in the HSM.

        In addition to creating an HSM configuration, you must also
        create an HSM client certificate. For more information, go to
        `Hardware Security Modules`_ in the Amazon Redshift Management
        Guide.

        :type hsm_configuration_identifier: string
        :param hsm_configuration_identifier: The identifier to be assigned to
            the new Amazon Redshift HSM configuration.

        :type description: string
        :param description: A text description of the HSM configuration to be
            created.

        :type hsm_ip_address: string
        :param hsm_ip_address: The IP address that the Amazon Redshift cluster
            must use to access the HSM.

        :type hsm_partition_name: string
        :param hsm_partition_name: The name of the partition in the HSM where
            the Amazon Redshift clusters will store their database encryption
            keys.

        :type hsm_partition_password: string
        :param hsm_partition_password: The password required to access the HSM
            partition.

        :type hsm_server_public_certificate: string
        :param hsm_server_public_certificate: The HSMs public certificate file.
            When using Cloud HSM, the file name is server.pem.

        """
        params = {
            'HsmConfigurationIdentifier': hsm_configuration_identifier,
            'Description': description,
            'HsmIpAddress': hsm_ip_address,
            'HsmPartitionName': hsm_partition_name,
            'HsmPartitionPassword': hsm_partition_password,
            'HsmServerPublicCertificate': hsm_server_public_certificate,
        }
        return self._make_request(
            action='CreateHsmConfiguration',
            verb='POST',
            path='/', params=params)

    def delete_cluster(self, cluster_identifier,
                       skip_final_cluster_snapshot=None,
                       final_cluster_snapshot_identifier=None):
        """
        Deletes a previously provisioned cluster. A successful
        response from the web service indicates that the request was
        received correctly. If a final cluster snapshot is requested
        the status of the cluster will be "final-snapshot" while the
        snapshot is being taken, then it's "deleting" once Amazon
        Redshift begins deleting the cluster. Use DescribeClusters to
        monitor the status of the deletion. The delete operation
        cannot be canceled or reverted once submitted. For more
        information about managing clusters, go to `Amazon Redshift
        Clusters`_ in the Amazon Redshift Management Guide .

        :type cluster_identifier: string
        :param cluster_identifier:
        The identifier of the cluster to be deleted.

        Constraints:


        + Must contain lowercase characters.
        + Must contain from 1 to 63 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type skip_final_cluster_snapshot: boolean
        :param skip_final_cluster_snapshot: Determines whether a final snapshot
            of the cluster is created before Amazon Redshift deletes the
            cluster. If `True`, a final cluster snapshot is not created. If
            `False`, a final cluster snapshot is created before the cluster is
            deleted.
        Default: `False`

        :type final_cluster_snapshot_identifier: string
        :param final_cluster_snapshot_identifier:
        The identifier of the final snapshot that is to be created immediately
            before deleting the cluster. If this parameter is provided,
            SkipFinalClusterSnapshot must be `False`.

        Constraints:


        + Must be 1 to 255 alphanumeric characters.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        if skip_final_cluster_snapshot is not None:
            params['SkipFinalClusterSnapshot'] = str(
                skip_final_cluster_snapshot).lower()
        if final_cluster_snapshot_identifier is not None:
            params['FinalClusterSnapshotIdentifier'] = final_cluster_snapshot_identifier
        return self._make_request(
            action='DeleteCluster',
            verb='POST',
            path='/', params=params)

    def delete_cluster_parameter_group(self, parameter_group_name):
        """
        Deletes a specified Amazon Redshift parameter group.

        :type parameter_group_name: string
        :param parameter_group_name:
        The name of the parameter group to be deleted.

        Constraints:


        + Must be the name of an existing cluster parameter group.
        + Cannot delete a default cluster parameter group.

        """
        params = {'ParameterGroupName': parameter_group_name, }
        return self._make_request(
            action='DeleteClusterParameterGroup',
            verb='POST',
            path='/', params=params)

    def delete_cluster_security_group(self, cluster_security_group_name):
        """
        Deletes an Amazon Redshift security group.

        For information about managing security groups, go to `Amazon
        Redshift Cluster Security Groups`_ in the Amazon Redshift
        Management Guide .

        :type cluster_security_group_name: string
        :param cluster_security_group_name: The name of the cluster security
            group to be deleted.

        """
        params = {
            'ClusterSecurityGroupName': cluster_security_group_name,
        }
        return self._make_request(
            action='DeleteClusterSecurityGroup',
            verb='POST',
            path='/', params=params)

    def delete_cluster_snapshot(self, snapshot_identifier,
                                snapshot_cluster_identifier=None):
        """
        Deletes the specified manual snapshot. The snapshot must be in
        the `available` state, with no other users authorized to
        access the snapshot.

        Unlike automated snapshots, manual snapshots are retained even
        after you delete your cluster. Amazon Redshift does not delete
        your manual snapshots. You must delete manual snapshot
        explicitly to avoid getting charged. If other accounts are
        authorized to access the snapshot, you must revoke all of the
        authorizations before you can delete the snapshot.

        :type snapshot_identifier: string
        :param snapshot_identifier: The unique identifier of the manual
            snapshot to be deleted.
        Constraints: Must be the name of an existing snapshot that is in the
            `available` state.

        :type snapshot_cluster_identifier: string
        :param snapshot_cluster_identifier: The unique identifier of the
            cluster the snapshot was created from. This parameter is required
            if your IAM user has a policy containing a snapshot resource
            element that specifies anything other than * for the cluster name.
        Constraints: Must be the name of valid cluster.

        """
        params = {'SnapshotIdentifier': snapshot_identifier, }
        if snapshot_cluster_identifier is not None:
            params['SnapshotClusterIdentifier'] = snapshot_cluster_identifier
        return self._make_request(
            action='DeleteClusterSnapshot',
            verb='POST',
            path='/', params=params)

    def delete_cluster_subnet_group(self, cluster_subnet_group_name):
        """
        Deletes the specified cluster subnet group.

        :type cluster_subnet_group_name: string
        :param cluster_subnet_group_name: The name of the cluster subnet group
            name to be deleted.

        """
        params = {
            'ClusterSubnetGroupName': cluster_subnet_group_name,
        }
        return self._make_request(
            action='DeleteClusterSubnetGroup',
            verb='POST',
            path='/', params=params)

    def delete_event_subscription(self, subscription_name):
        """
        Deletes an Amazon Redshift event notification subscription.

        :type subscription_name: string
        :param subscription_name: The name of the Amazon Redshift event
            notification subscription to be deleted.

        """
        params = {'SubscriptionName': subscription_name, }
        return self._make_request(
            action='DeleteEventSubscription',
            verb='POST',
            path='/', params=params)

    def delete_hsm_client_certificate(self,
                                      hsm_client_certificate_identifier):
        """
        Deletes the specified HSM client certificate.

        :type hsm_client_certificate_identifier: string
        :param hsm_client_certificate_identifier: The identifier of the HSM
            client certificate to be deleted.

        """
        params = {
            'HsmClientCertificateIdentifier': hsm_client_certificate_identifier,
        }
        return self._make_request(
            action='DeleteHsmClientCertificate',
            verb='POST',
            path='/', params=params)

    def delete_hsm_configuration(self, hsm_configuration_identifier):
        """
        Deletes the specified Amazon Redshift HSM configuration.

        :type hsm_configuration_identifier: string
        :param hsm_configuration_identifier: The identifier of the Amazon
            Redshift HSM configuration to be deleted.

        """
        params = {
            'HsmConfigurationIdentifier': hsm_configuration_identifier,
        }
        return self._make_request(
            action='DeleteHsmConfiguration',
            verb='POST',
            path='/', params=params)

    def describe_cluster_parameter_groups(self, parameter_group_name=None,
                                          max_records=None, marker=None):
        """
        Returns a list of Amazon Redshift parameter groups, including
        parameter groups you created and the default parameter group.
        For each parameter group, the response includes the parameter
        group name, description, and parameter group family name. You
        can optionally specify a name to retrieve the description of a
        specific parameter group.

        For more information about managing parameter groups, go to
        `Amazon Redshift Parameter Groups`_ in the Amazon Redshift
        Management Guide .

        :type parameter_group_name: string
        :param parameter_group_name: The name of a specific parameter group for
            which to return details. By default, details about all parameter
            groups and the default parameter group are returned.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusterParameterGroups request exceed the value specified
            in `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if parameter_group_name is not None:
            params['ParameterGroupName'] = parameter_group_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeClusterParameterGroups',
            verb='POST',
            path='/', params=params)

    def describe_cluster_parameters(self, parameter_group_name, source=None,
                                    max_records=None, marker=None):
        """
        Returns a detailed list of parameters contained within the
        specified Amazon Redshift parameter group. For each parameter
        the response includes information such as parameter name,
        description, data type, value, whether the parameter value is
        modifiable, and so on.

        You can specify source filter to retrieve parameters of only
        specific type. For example, to retrieve parameters that were
        modified by a user action such as from
        ModifyClusterParameterGroup, you can specify source equal to
        user .

        For more information about managing parameter groups, go to
        `Amazon Redshift Parameter Groups`_ in the Amazon Redshift
        Management Guide .

        :type parameter_group_name: string
        :param parameter_group_name: The name of a cluster parameter group for
            which to return details.

        :type source: string
        :param source: The parameter types to return. Specify `user` to show
            parameters that are different form the default. Similarly, specify
            `engine-default` to show parameters that are the same as the
            default parameter group.
        Default: All parameter types returned.

        Valid Values: `user` | `engine-default`

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusterParameters request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {'ParameterGroupName': parameter_group_name, }
        if source is not None:
            params['Source'] = source
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeClusterParameters',
            verb='POST',
            path='/', params=params)

    def describe_cluster_security_groups(self,
                                         cluster_security_group_name=None,
                                         max_records=None, marker=None):
        """
        Returns information about Amazon Redshift security groups. If
        the name of a security group is specified, the response will
        contain only information about only that security group.

        For information about managing security groups, go to `Amazon
        Redshift Cluster Security Groups`_ in the Amazon Redshift
        Management Guide .

        :type cluster_security_group_name: string
        :param cluster_security_group_name: The name of a cluster security
            group for which you are requesting details. You can specify either
            the **Marker** parameter or a **ClusterSecurityGroupName**
            parameter, but not both.
        Example: `securitygroup1`

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusterSecurityGroups request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.
        Constraints: You can specify either the **ClusterSecurityGroupName**
            parameter or the **Marker** parameter, but not both.

        """
        params = {}
        if cluster_security_group_name is not None:
            params['ClusterSecurityGroupName'] = cluster_security_group_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeClusterSecurityGroups',
            verb='POST',
            path='/', params=params)

    def describe_cluster_snapshots(self, cluster_identifier=None,
                                   snapshot_identifier=None,
                                   snapshot_type=None, start_time=None,
                                   end_time=None, max_records=None,
                                   marker=None, owner_account=None):
        """
        Returns one or more snapshot objects, which contain metadata
        about your cluster snapshots. By default, this operation
        returns information about all snapshots of all clusters that
        are owned by you AWS customer account. No information is
        returned for snapshots owned by inactive AWS customer
        accounts.

        :type cluster_identifier: string
        :param cluster_identifier: The identifier of the cluster for which
            information about snapshots is requested.

        :type snapshot_identifier: string
        :param snapshot_identifier: The snapshot identifier of the snapshot
            about which to return information.

        :type snapshot_type: string
        :param snapshot_type: The type of snapshots for which you are
            requesting information. By default, snapshots of all types are
            returned.
        Valid Values: `automated` | `manual`

        :type start_time: timestamp
        :param start_time: A value that requests only snapshots created at or
            after the specified time. The time value is specified in ISO 8601
            format. For more information about ISO 8601, go to the `ISO8601
            Wikipedia page.`_
        Example: `2012-07-16T18:00:00Z`

        :type end_time: timestamp
        :param end_time: A time value that requests only snapshots created at
            or before the specified time. The time value is specified in ISO
            8601 format. For more information about ISO 8601, go to the
            `ISO8601 Wikipedia page.`_
        Example: `2012-07-16T18:00:00Z`

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusterSnapshots request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        :type owner_account: string
        :param owner_account: The AWS customer account used to create or copy
            the snapshot. Use this field to filter the results to snapshots
            owned by a particular account. To describe snapshots you own,
            either specify your AWS customer account, or do not specify the
            parameter.

        """
        params = {}
        if cluster_identifier is not None:
            params['ClusterIdentifier'] = cluster_identifier
        if snapshot_identifier is not None:
            params['SnapshotIdentifier'] = snapshot_identifier
        if snapshot_type is not None:
            params['SnapshotType'] = snapshot_type
        if start_time is not None:
            params['StartTime'] = start_time
        if end_time is not None:
            params['EndTime'] = end_time
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        if owner_account is not None:
            params['OwnerAccount'] = owner_account
        return self._make_request(
            action='DescribeClusterSnapshots',
            verb='POST',
            path='/', params=params)

    def describe_cluster_subnet_groups(self, cluster_subnet_group_name=None,
                                       max_records=None, marker=None):
        """
        Returns one or more cluster subnet group objects, which
        contain metadata about your cluster subnet groups. By default,
        this operation returns information about all cluster subnet
        groups that are defined in you AWS account.

        :type cluster_subnet_group_name: string
        :param cluster_subnet_group_name: The name of the cluster subnet group
            for which information is requested.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusterSubnetGroups request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if cluster_subnet_group_name is not None:
            params['ClusterSubnetGroupName'] = cluster_subnet_group_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeClusterSubnetGroups',
            verb='POST',
            path='/', params=params)

    def describe_cluster_versions(self, cluster_version=None,
                                  cluster_parameter_group_family=None,
                                  max_records=None, marker=None):
        """
        Returns descriptions of the available Amazon Redshift cluster
        versions. You can call this operation even before creating any
        clusters to learn more about the Amazon Redshift versions. For
        more information about managing clusters, go to `Amazon
        Redshift Clusters`_ in the Amazon Redshift Management Guide

        :type cluster_version: string
        :param cluster_version: The specific cluster version to return.
        Example: `1.0`

        :type cluster_parameter_group_family: string
        :param cluster_parameter_group_family:
        The name of a specific cluster parameter group family to return details
            for.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusterVersions request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if cluster_version is not None:
            params['ClusterVersion'] = cluster_version
        if cluster_parameter_group_family is not None:
            params['ClusterParameterGroupFamily'] = cluster_parameter_group_family
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeClusterVersions',
            verb='POST',
            path='/', params=params)

    def describe_clusters(self, cluster_identifier=None, max_records=None,
                          marker=None):
        """
        Returns properties of provisioned clusters including general
        cluster properties, cluster database properties, maintenance
        and backup properties, and security and access properties.
        This operation supports pagination. For more information about
        managing clusters, go to `Amazon Redshift Clusters`_ in the
        Amazon Redshift Management Guide .

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of a cluster whose
            properties you are requesting. This parameter is case sensitive.
        The default is that all clusters defined for an account are returned.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeClusters request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.
        Constraints: You can specify either the **ClusterIdentifier** parameter
            or the **Marker** parameter, but not both.

        """
        params = {}
        if cluster_identifier is not None:
            params['ClusterIdentifier'] = cluster_identifier
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeClusters',
            verb='POST',
            path='/', params=params)

    def describe_default_cluster_parameters(self, parameter_group_family,
                                            max_records=None, marker=None):
        """
        Returns a list of parameter settings for the specified
        parameter group family.

        For more information about managing parameter groups, go to
        `Amazon Redshift Parameter Groups`_ in the Amazon Redshift
        Management Guide .

        :type parameter_group_family: string
        :param parameter_group_family: The name of the cluster parameter group
            family.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeDefaultClusterParameters request exceed the value specified
            in `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {'ParameterGroupFamily': parameter_group_family, }
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDefaultClusterParameters',
            verb='POST',
            path='/', params=params)

    def describe_event_categories(self, source_type=None):
        """
        Displays a list of event categories for all event source
        types, or for a specified source type. For a list of the event
        categories and source types, go to `Amazon Redshift Event
        Notifications`_.

        :type source_type: string
        :param source_type: The source type, such as cluster or parameter
            group, to which the described event categories apply.
        Valid values: cluster, snapshot, parameter group, and security group.

        """
        params = {}
        if source_type is not None:
            params['SourceType'] = source_type
        return self._make_request(
            action='DescribeEventCategories',
            verb='POST',
            path='/', params=params)

    def describe_event_subscriptions(self, subscription_name=None,
                                     max_records=None, marker=None):
        """
        Lists descriptions of all the Amazon Redshift event
        notifications subscription for a customer account. If you
        specify a subscription name, lists the description for that
        subscription.

        :type subscription_name: string
        :param subscription_name: The name of the Amazon Redshift event
            notification subscription to be described.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeEventSubscriptions request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if subscription_name is not None:
            params['SubscriptionName'] = subscription_name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeEventSubscriptions',
            verb='POST',
            path='/', params=params)

    def describe_events(self, source_identifier=None, source_type=None,
                        start_time=None, end_time=None, duration=None,
                        max_records=None, marker=None):
        """
        Returns events related to clusters, security groups,
        snapshots, and parameter groups for the past 14 days. Events
        specific to a particular cluster, security group, snapshot or
        parameter group can be obtained by providing the name as a
        parameter. By default, the past hour of events are returned.

        :type source_identifier: string
        :param source_identifier:
        The identifier of the event source for which events will be returned.
            If this parameter is not specified, then all sources are included
            in the response.

        Constraints:

        If SourceIdentifier is supplied, SourceType must also be provided.


        + Specify a cluster identifier when SourceType is `cluster`.
        + Specify a cluster security group name when SourceType is `cluster-
              security-group`.
        + Specify a cluster parameter group name when SourceType is `cluster-
              parameter-group`.
        + Specify a cluster snapshot identifier when SourceType is `cluster-
              snapshot`.

        :type source_type: string
        :param source_type:
        The event source to retrieve events for. If no value is specified, all
            events are returned.

        Constraints:

        If SourceType is supplied, SourceIdentifier must also be provided.


        + Specify `cluster` when SourceIdentifier is a cluster identifier.
        + Specify `cluster-security-group` when SourceIdentifier is a cluster
              security group name.
        + Specify `cluster-parameter-group` when SourceIdentifier is a cluster
              parameter group name.
        + Specify `cluster-snapshot` when SourceIdentifier is a cluster
              snapshot identifier.

        :type start_time: timestamp
        :param start_time: The beginning of the time interval to retrieve
            events for, specified in ISO 8601 format. For more information
            about ISO 8601, go to the `ISO8601 Wikipedia page.`_
        Example: `2009-07-08T18:00Z`

        :type end_time: timestamp
        :param end_time: The end of the time interval for which to retrieve
            events, specified in ISO 8601 format. For more information about
            ISO 8601, go to the `ISO8601 Wikipedia page.`_
        Example: `2009-07-08T18:00Z`

        :type duration: integer
        :param duration: The number of minutes prior to the time of the request
            for which to retrieve events. For example, if the request is sent
            at 18:00 and you specify a duration of 60, then only events which
            have occurred after 17:00 will be returned.
        Default: `60`

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeEvents request exceed the value specified in `MaxRecords`,
            AWS returns a value in the `Marker` field of the response. You can
            retrieve the next set of response records by providing the returned
            marker value in the `Marker` parameter and retrying the request.

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

    def describe_hsm_client_certificates(self,
                                         hsm_client_certificate_identifier=None,
                                         max_records=None, marker=None):
        """
        Returns information about the specified HSM client
        certificate. If no certificate ID is specified, returns
        information about all the HSM certificates owned by your AWS
        customer account.

        :type hsm_client_certificate_identifier: string
        :param hsm_client_certificate_identifier: The identifier of a specific
            HSM client certificate for which you want information. If no
            identifier is specified, information is returned for all HSM client
            certificates owned by your AWS customer account.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeHsmClientCertificates request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if hsm_client_certificate_identifier is not None:
            params['HsmClientCertificateIdentifier'] = hsm_client_certificate_identifier
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeHsmClientCertificates',
            verb='POST',
            path='/', params=params)

    def describe_hsm_configurations(self, hsm_configuration_identifier=None,
                                    max_records=None, marker=None):
        """
        Returns information about the specified Amazon Redshift HSM
        configuration. If no configuration ID is specified, returns
        information about all the HSM configurations owned by your AWS
        customer account.

        :type hsm_configuration_identifier: string
        :param hsm_configuration_identifier: The identifier of a specific
            Amazon Redshift HSM configuration to be described. If no identifier
            is specified, information is returned for all HSM configurations
            owned by your AWS customer account.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeHsmConfigurations request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if hsm_configuration_identifier is not None:
            params['HsmConfigurationIdentifier'] = hsm_configuration_identifier
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeHsmConfigurations',
            verb='POST',
            path='/', params=params)

    def describe_logging_status(self, cluster_identifier):
        """
        Describes whether information, such as queries and connection
        attempts, is being logged for the specified Amazon Redshift
        cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The identifier of the cluster to get the
            logging status from.
        Example: `examplecluster`

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        return self._make_request(
            action='DescribeLoggingStatus',
            verb='POST',
            path='/', params=params)

    def describe_orderable_cluster_options(self, cluster_version=None,
                                           node_type=None, max_records=None,
                                           marker=None):
        """
        Returns a list of orderable cluster options. Before you create
        a new cluster you can use this operation to find what options
        are available, such as the EC2 Availability Zones (AZ) in the
        specific AWS region that you can specify, and the node types
        you can request. The node types differ by available storage,
        memory, CPU and price. With the cost involved you might want
        to obtain a list of cluster options in the specific region and
        specify values when creating a cluster. For more information
        about managing clusters, go to `Amazon Redshift Clusters`_ in
        the Amazon Redshift Management Guide

        :type cluster_version: string
        :param cluster_version: The version filter value. Specify this
            parameter to show only the available offerings matching the
            specified version.
        Default: All versions.

        Constraints: Must be one of the version returned from
            DescribeClusterVersions.

        :type node_type: string
        :param node_type: The node type filter value. Specify this parameter to
            show only the available offerings matching the specified node type.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeOrderableClusterOptions request exceed the value specified
            in `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if cluster_version is not None:
            params['ClusterVersion'] = cluster_version
        if node_type is not None:
            params['NodeType'] = node_type
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeOrderableClusterOptions',
            verb='POST',
            path='/', params=params)

    def describe_reserved_node_offerings(self,
                                         reserved_node_offering_id=None,
                                         max_records=None, marker=None):
        """
        Returns a list of the available reserved node offerings by
        Amazon Redshift with their descriptions including the node
        type, the fixed and recurring costs of reserving the node and
        duration the node will be reserved for you. These descriptions
        help you determine which reserve node offering you want to
        purchase. You then use the unique offering ID in you call to
        PurchaseReservedNodeOffering to reserve one or more nodes for
        your Amazon Redshift cluster.

        For more information about managing parameter groups, go to
        `Purchasing Reserved Nodes`_ in the Amazon Redshift Management
        Guide .

        :type reserved_node_offering_id: string
        :param reserved_node_offering_id: The unique identifier for the
            offering.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeReservedNodeOfferings request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if reserved_node_offering_id is not None:
            params['ReservedNodeOfferingId'] = reserved_node_offering_id
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReservedNodeOfferings',
            verb='POST',
            path='/', params=params)

    def describe_reserved_nodes(self, reserved_node_id=None,
                                max_records=None, marker=None):
        """
        Returns the descriptions of the reserved nodes.

        :type reserved_node_id: string
        :param reserved_node_id: Identifier for the node reservation.

        :type max_records: integer
        :param max_records: The maximum number of response records to return in
            each call. If the number of remaining response records exceeds the
            specified `MaxRecords` value, a value is returned in a `marker`
            field of the response. You can retrieve the next set of records by
            retrying the command with the returned marker value.
        Default: `100`

        Constraints: minimum 20, maximum 100.

        :type marker: string
        :param marker: An optional parameter that specifies the starting point
            to return a set of response records. When the results of a
            DescribeReservedNodes request exceed the value specified in
            `MaxRecords`, AWS returns a value in the `Marker` field of the
            response. You can retrieve the next set of response records by
            providing the returned marker value in the `Marker` parameter and
            retrying the request.

        """
        params = {}
        if reserved_node_id is not None:
            params['ReservedNodeId'] = reserved_node_id
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReservedNodes',
            verb='POST',
            path='/', params=params)

    def describe_resize(self, cluster_identifier):
        """
        Returns information about the last resize operation for the
        specified cluster. If no resize operation has ever been
        initiated for the specified cluster, a `HTTP 404` error is
        returned. If a resize operation was initiated and completed,
        the status of the resize remains as `SUCCEEDED` until the next
        resize.

        A resize operation can be requested using ModifyCluster and
        specifying a different number or type of nodes for the
        cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of a cluster whose
            resize progress you are requesting. This parameter isn't case-
            sensitive.
        By default, resize operations for all clusters defined for an AWS
            account are returned.

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        return self._make_request(
            action='DescribeResize',
            verb='POST',
            path='/', params=params)

    def disable_logging(self, cluster_identifier):
        """
        Stops logging information, such as queries and connection
        attempts, for the specified Amazon Redshift cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The identifier of the cluster on which
            logging is to be stopped.
        Example: `examplecluster`

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        return self._make_request(
            action='DisableLogging',
            verb='POST',
            path='/', params=params)

    def disable_snapshot_copy(self, cluster_identifier):
        """
        Disables the automatic copying of snapshots from one region to
        another region for a specified cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of the source cluster
            that you want to disable copying of snapshots to a destination
            region.
        Constraints: Must be the valid name of an existing cluster that has
            cross-region snapshot copy enabled.

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        return self._make_request(
            action='DisableSnapshotCopy',
            verb='POST',
            path='/', params=params)

    def enable_logging(self, cluster_identifier, bucket_name,
                       s3_key_prefix=None):
        """
        Starts logging information, such as queries and connection
        attempts, for the specified Amazon Redshift cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The identifier of the cluster on which
            logging is to be started.
        Example: `examplecluster`

        :type bucket_name: string
        :param bucket_name:
        The name of an existing S3 bucket where the log files are to be stored.

        Constraints:


        + Must be in the same region as the cluster
        + The cluster must have read bucket and put object permissions

        :type s3_key_prefix: string
        :param s3_key_prefix:
        The prefix applied to the log file names.

        Constraints:


        + Cannot exceed 512 characters
        + Cannot contain spaces( ), double quotes ("), single quotes ('), a
              backslash (\), or control characters. The hexadecimal codes for
              invalid characters are:

            + x00 to x20
            + x22
            + x27
            + x5c
            + x7f or larger

        """
        params = {
            'ClusterIdentifier': cluster_identifier,
            'BucketName': bucket_name,
        }
        if s3_key_prefix is not None:
            params['S3KeyPrefix'] = s3_key_prefix
        return self._make_request(
            action='EnableLogging',
            verb='POST',
            path='/', params=params)

    def enable_snapshot_copy(self, cluster_identifier, destination_region,
                             retention_period=None):
        """
        Enables the automatic copy of snapshots from one region to
        another region for a specified cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of the source cluster
            to copy snapshots from.
        Constraints: Must be the valid name of an existing cluster that does
            not already have cross-region snapshot copy enabled.

        :type destination_region: string
        :param destination_region: The destination region that you want to copy
            snapshots to.
        Constraints: Must be the name of a valid region. For more information,
            see `Regions and Endpoints`_ in the Amazon Web Services General
            Reference.

        :type retention_period: integer
        :param retention_period: The number of days to retain automated
            snapshots in the destination region after they are copied from the
            source region.
        Default: 7.

        Constraints: Must be at least 1 and no more than 35.

        """
        params = {
            'ClusterIdentifier': cluster_identifier,
            'DestinationRegion': destination_region,
        }
        if retention_period is not None:
            params['RetentionPeriod'] = retention_period
        return self._make_request(
            action='EnableSnapshotCopy',
            verb='POST',
            path='/', params=params)

    def modify_cluster(self, cluster_identifier, cluster_type=None,
                       node_type=None, number_of_nodes=None,
                       cluster_security_groups=None,
                       vpc_security_group_ids=None,
                       master_user_password=None,
                       cluster_parameter_group_name=None,
                       automated_snapshot_retention_period=None,
                       preferred_maintenance_window=None,
                       cluster_version=None, allow_version_upgrade=None,
                       hsm_client_certificate_identifier=None,
                       hsm_configuration_identifier=None,
                       new_cluster_identifier=None):
        """
        Modifies the settings for a cluster. For example, you can add
        another security or parameter group, update the preferred
        maintenance window, or change the master user password.
        Resetting a cluster password or modifying the security groups
        associated with a cluster do not need a reboot. However,
        modifying a parameter group requires a reboot for parameters
        to take effect. For more information about managing clusters,
        go to `Amazon Redshift Clusters`_ in the Amazon Redshift
        Management Guide

        You can also change node type and the number of nodes to scale
        up or down the cluster. When resizing a cluster, you must
        specify both the number of nodes and the node type even if one
        of the parameters does not change. If you specify the same
        number of nodes and node type that are already configured for
        the cluster, an error is returned.

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of the cluster to be
            modified.
        Example: `examplecluster`

        :type cluster_type: string
        :param cluster_type: The new cluster type.
        When you submit your cluster resize request, your existing cluster goes
            into a read-only mode. After Amazon Redshift provisions a new
            cluster based on your resize requirements, there will be outage for
            a period while the old cluster is deleted and your connection is
            switched to the new cluster. You can use DescribeResize to track
            the progress of the resize request.

        Valid Values: ` multi-node | single-node `

        :type node_type: string
        :param node_type: The new node type of the cluster. If you specify a
            new node type, you must also specify the number of nodes parameter
            also.
        When you submit your request to resize a cluster, Amazon Redshift sets
            access permissions for the cluster to read-only. After Amazon
            Redshift provisions a new cluster according to your resize
            requirements, there will be a temporary outage while the old
            cluster is deleted and your connection is switched to the new
            cluster. When the new connection is complete, the original access
            permissions for the cluster are restored. You can use the
            DescribeResize to track the progress of the resize request.

        Valid Values: ` dw1.xlarge` | `dw1.8xlarge` | `dw2.large` |
            `dw2.8xlarge`.

        :type number_of_nodes: integer
        :param number_of_nodes: The new number of nodes of the cluster. If you
            specify a new number of nodes, you must also specify the node type
            parameter also.
        When you submit your request to resize a cluster, Amazon Redshift sets
            access permissions for the cluster to read-only. After Amazon
            Redshift provisions a new cluster according to your resize
            requirements, there will be a temporary outage while the old
            cluster is deleted and your connection is switched to the new
            cluster. When the new connection is complete, the original access
            permissions for the cluster are restored. You can use
            DescribeResize to track the progress of the resize request.

        Valid Values: Integer greater than `0`.

        :type cluster_security_groups: list
        :param cluster_security_groups:
        A list of cluster security groups to be authorized on this cluster.
            This change is asynchronously applied as soon as possible.

        Security groups currently associated with the cluster, and not in the
            list of groups to apply, will be revoked from the cluster.

        Constraints:


        + Must be 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type vpc_security_group_ids: list
        :param vpc_security_group_ids: A list of virtual private cloud (VPC)
            security groups to be associated with the cluster.

        :type master_user_password: string
        :param master_user_password:
        The new password for the cluster master user. This change is
            asynchronously applied as soon as possible. Between the time of the
            request and the completion of the request, the `MasterUserPassword`
            element exists in the `PendingModifiedValues` element of the
            operation response.

        Default: Uses existing setting.

        Constraints:


        + Must be between 8 and 64 characters in length.
        + Must contain at least one uppercase letter.
        + Must contain at least one lowercase letter.
        + Must contain one number.
        + Can be any printable ASCII character (ASCII code 33 to 126) except '
              (single quote), " (double quote), \, /, @, or space.

        :type cluster_parameter_group_name: string
        :param cluster_parameter_group_name: The name of the cluster parameter
            group to apply to this cluster. This change is applied only after
            the cluster is rebooted. To reboot a cluster use RebootCluster.
        Default: Uses existing setting.

        Constraints: The cluster parameter group must be in the same parameter
            group family that matches the cluster version.

        :type automated_snapshot_retention_period: integer
        :param automated_snapshot_retention_period: The number of days that
            automated snapshots are retained. If the value is 0, automated
            snapshots are disabled. Even if automated snapshots are disabled,
            you can still create manual snapshots when you want with
            CreateClusterSnapshot.
        If you decrease the automated snapshot retention period from its
            current value, existing automated snapshots that fall outside of
            the new retention period will be immediately deleted.

        Default: Uses existing setting.

        Constraints: Must be a value from 0 to 35.

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which system maintenance can occur, if necessary. If system
            maintenance is necessary during the window, it may result in an
            outage.
        This maintenance window change is made immediately. If the new
            maintenance window indicates the current time, there must be at
            least 120 minutes between the current time and end of the window in
            order to ensure that pending changes are applied.

        Default: Uses existing setting.

        Format: ddd:hh24:mi-ddd:hh24:mi, for example `wed:07:30-wed:08:00`.

        Valid Days: Mon | Tue | Wed | Thu | Fri | Sat | Sun

        Constraints: Must be at least 30 minutes.

        :type cluster_version: string
        :param cluster_version: The new version number of the Amazon Redshift
            engine to upgrade to.
        For major version upgrades, if a non-default cluster parameter group is
            currently in use, a new cluster parameter group in the cluster
            parameter group family for the new version must be specified. The
            new cluster parameter group can be the default for that cluster
            parameter group family. For more information about managing
            parameter groups, go to `Amazon Redshift Parameter Groups`_ in the
            Amazon Redshift Management Guide .

        Example: `1.0`

        :type allow_version_upgrade: boolean
        :param allow_version_upgrade: If `True`, upgrades will be applied
            automatically to the cluster during the maintenance window.
        Default: `False`

        :type hsm_client_certificate_identifier: string
        :param hsm_client_certificate_identifier: Specifies the name of the HSM
            client certificate the Amazon Redshift cluster uses to retrieve the
            data encryption keys stored in an HSM.

        :type hsm_configuration_identifier: string
        :param hsm_configuration_identifier: Specifies the name of the HSM
            configuration that contains the information the Amazon Redshift
            cluster can use to retrieve and store keys in an HSM.

        :type new_cluster_identifier: string
        :param new_cluster_identifier: The new identifier for the cluster.
        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens.
        + Alphabetic characters must be lowercase.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.
        + Must be unique for all clusters within an AWS account.


        Example: `examplecluster`

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        if cluster_type is not None:
            params['ClusterType'] = cluster_type
        if node_type is not None:
            params['NodeType'] = node_type
        if number_of_nodes is not None:
            params['NumberOfNodes'] = number_of_nodes
        if cluster_security_groups is not None:
            self.build_list_params(params,
                                   cluster_security_groups,
                                   'ClusterSecurityGroups.member')
        if vpc_security_group_ids is not None:
            self.build_list_params(params,
                                   vpc_security_group_ids,
                                   'VpcSecurityGroupIds.member')
        if master_user_password is not None:
            params['MasterUserPassword'] = master_user_password
        if cluster_parameter_group_name is not None:
            params['ClusterParameterGroupName'] = cluster_parameter_group_name
        if automated_snapshot_retention_period is not None:
            params['AutomatedSnapshotRetentionPeriod'] = automated_snapshot_retention_period
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if cluster_version is not None:
            params['ClusterVersion'] = cluster_version
        if allow_version_upgrade is not None:
            params['AllowVersionUpgrade'] = str(
                allow_version_upgrade).lower()
        if hsm_client_certificate_identifier is not None:
            params['HsmClientCertificateIdentifier'] = hsm_client_certificate_identifier
        if hsm_configuration_identifier is not None:
            params['HsmConfigurationIdentifier'] = hsm_configuration_identifier
        if new_cluster_identifier is not None:
            params['NewClusterIdentifier'] = new_cluster_identifier
        return self._make_request(
            action='ModifyCluster',
            verb='POST',
            path='/', params=params)

    def modify_cluster_parameter_group(self, parameter_group_name,
                                       parameters):
        """
        Modifies the parameters of a parameter group.

        For more information about managing parameter groups, go to
        `Amazon Redshift Parameter Groups`_ in the Amazon Redshift
        Management Guide .

        :type parameter_group_name: string
        :param parameter_group_name: The name of the parameter group to be
            modified.

        :type parameters: list
        :param parameters: An array of parameters to be modified. A maximum of
            20 parameters can be modified in a single request.
        For each parameter to be modified, you must supply at least the
            parameter name and parameter value; other name-value pairs of the
            parameter are optional.

        For the workload management (WLM) configuration, you must supply all
            the name-value pairs in the wlm_json_configuration parameter.

        """
        params = {'ParameterGroupName': parameter_group_name, }
        self.build_complex_list_params(
            params, parameters,
            'Parameters.member',
            ('ParameterName', 'ParameterValue', 'Description', 'Source', 'DataType', 'AllowedValues', 'IsModifiable', 'MinimumEngineVersion'))
        return self._make_request(
            action='ModifyClusterParameterGroup',
            verb='POST',
            path='/', params=params)

    def modify_cluster_subnet_group(self, cluster_subnet_group_name,
                                    subnet_ids, description=None):
        """
        Modifies a cluster subnet group to include the specified list
        of VPC subnets. The operation replaces the existing list of
        subnets with the new list of subnets.

        :type cluster_subnet_group_name: string
        :param cluster_subnet_group_name: The name of the subnet group to be
            modified.

        :type description: string
        :param description: A text description of the subnet group to be
            modified.

        :type subnet_ids: list
        :param subnet_ids: An array of VPC subnet IDs. A maximum of 20 subnets
            can be modified in a single request.

        """
        params = {
            'ClusterSubnetGroupName': cluster_subnet_group_name,
        }
        self.build_list_params(params,
                               subnet_ids,
                               'SubnetIds.member')
        if description is not None:
            params['Description'] = description
        return self._make_request(
            action='ModifyClusterSubnetGroup',
            verb='POST',
            path='/', params=params)

    def modify_event_subscription(self, subscription_name,
                                  sns_topic_arn=None, source_type=None,
                                  source_ids=None, event_categories=None,
                                  severity=None, enabled=None):
        """
        Modifies an existing Amazon Redshift event notification
        subscription.

        :type subscription_name: string
        :param subscription_name: The name of the modified Amazon Redshift
            event notification subscription.

        :type sns_topic_arn: string
        :param sns_topic_arn: The Amazon Resource Name (ARN) of the SNS topic
            to be used by the event notification subscription.

        :type source_type: string
        :param source_type: The type of source that will be generating the
            events. For example, if you want to be notified of events generated
            by a cluster, you would set this parameter to cluster. If this
            value is not specified, events are returned for all Amazon Redshift
            objects in your AWS account. You must specify a source type in
            order to specify source IDs.
        Valid values: cluster, cluster-parameter-group, cluster-security-group,
            and cluster-snapshot.

        :type source_ids: list
        :param source_ids: A list of one or more identifiers of Amazon Redshift
            source objects. All of the objects must be of the same type as was
            specified in the source type parameter. The event subscription will
            return only events generated by the specified objects. If not
            specified, then events are returned for all objects within the
            source type specified.
        Example: my-cluster-1, my-cluster-2

        Example: my-snapshot-20131010

        :type event_categories: list
        :param event_categories: Specifies the Amazon Redshift event categories
            to be published by the event notification subscription.
        Values: Configuration, Management, Monitoring, Security

        :type severity: string
        :param severity: Specifies the Amazon Redshift event severity to be
            published by the event notification subscription.
        Values: ERROR, INFO

        :type enabled: boolean
        :param enabled: A Boolean value indicating if the subscription is
            enabled. `True` indicates the subscription is enabled

        """
        params = {'SubscriptionName': subscription_name, }
        if sns_topic_arn is not None:
            params['SnsTopicArn'] = sns_topic_arn
        if source_type is not None:
            params['SourceType'] = source_type
        if source_ids is not None:
            self.build_list_params(params,
                                   source_ids,
                                   'SourceIds.member')
        if event_categories is not None:
            self.build_list_params(params,
                                   event_categories,
                                   'EventCategories.member')
        if severity is not None:
            params['Severity'] = severity
        if enabled is not None:
            params['Enabled'] = str(
                enabled).lower()
        return self._make_request(
            action='ModifyEventSubscription',
            verb='POST',
            path='/', params=params)

    def modify_snapshot_copy_retention_period(self, cluster_identifier,
                                              retention_period):
        """
        Modifies the number of days to retain automated snapshots in
        the destination region after they are copied from the source
        region.

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of the cluster for
            which you want to change the retention period for automated
            snapshots that are copied to a destination region.
        Constraints: Must be the valid name of an existing cluster that has
            cross-region snapshot copy enabled.

        :type retention_period: integer
        :param retention_period: The number of days to retain automated
            snapshots in the destination region after they are copied from the
            source region.
        If you decrease the retention period for automated snapshots that are
            copied to a destination region, Amazon Redshift will delete any
            existing automated snapshots that were copied to the destination
            region and that fall outside of the new retention period.

        Constraints: Must be at least 1 and no more than 35.

        """
        params = {
            'ClusterIdentifier': cluster_identifier,
            'RetentionPeriod': retention_period,
        }
        return self._make_request(
            action='ModifySnapshotCopyRetentionPeriod',
            verb='POST',
            path='/', params=params)

    def purchase_reserved_node_offering(self, reserved_node_offering_id,
                                        node_count=None):
        """
        Allows you to purchase reserved nodes. Amazon Redshift offers
        a predefined set of reserved node offerings. You can purchase
        one of the offerings. You can call the
        DescribeReservedNodeOfferings API to obtain the available
        reserved node offerings. You can call this API by providing a
        specific reserved node offering and the number of nodes you
        want to reserve.

        For more information about managing parameter groups, go to
        `Purchasing Reserved Nodes`_ in the Amazon Redshift Management
        Guide .

        :type reserved_node_offering_id: string
        :param reserved_node_offering_id: The unique identifier of the reserved
            node offering you want to purchase.

        :type node_count: integer
        :param node_count: The number of reserved nodes you want to purchase.
        Default: `1`

        """
        params = {
            'ReservedNodeOfferingId': reserved_node_offering_id,
        }
        if node_count is not None:
            params['NodeCount'] = node_count
        return self._make_request(
            action='PurchaseReservedNodeOffering',
            verb='POST',
            path='/', params=params)

    def reboot_cluster(self, cluster_identifier):
        """
        Reboots a cluster. This action is taken as soon as possible.
        It results in a momentary outage to the cluster, during which
        the cluster status is set to `rebooting`. A cluster event is
        created when the reboot is completed. Any pending cluster
        modifications (see ModifyCluster) are applied at this reboot.
        For more information about managing clusters, go to `Amazon
        Redshift Clusters`_ in the Amazon Redshift Management Guide

        :type cluster_identifier: string
        :param cluster_identifier: The cluster identifier.

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        return self._make_request(
            action='RebootCluster',
            verb='POST',
            path='/', params=params)

    def reset_cluster_parameter_group(self, parameter_group_name,
                                      reset_all_parameters=None,
                                      parameters=None):
        """
        Sets one or more parameters of the specified parameter group
        to their default values and sets the source values of the
        parameters to "engine-default". To reset the entire parameter
        group specify the ResetAllParameters parameter. For parameter
        changes to take effect you must reboot any associated
        clusters.

        :type parameter_group_name: string
        :param parameter_group_name: The name of the cluster parameter group to
            be reset.

        :type reset_all_parameters: boolean
        :param reset_all_parameters: If `True`, all parameters in the specified
            parameter group will be reset to their default values.
        Default: `True`

        :type parameters: list
        :param parameters: An array of names of parameters to be reset. If
            ResetAllParameters option is not used, then at least one parameter
            name must be supplied.
        Constraints: A maximum of 20 parameters can be reset in a single
            request.

        """
        params = {'ParameterGroupName': parameter_group_name, }
        if reset_all_parameters is not None:
            params['ResetAllParameters'] = str(
                reset_all_parameters).lower()
        if parameters is not None:
            self.build_complex_list_params(
                params, parameters,
                'Parameters.member',
                ('ParameterName', 'ParameterValue', 'Description', 'Source', 'DataType', 'AllowedValues', 'IsModifiable', 'MinimumEngineVersion'))
        return self._make_request(
            action='ResetClusterParameterGroup',
            verb='POST',
            path='/', params=params)

    def restore_from_cluster_snapshot(self, cluster_identifier,
                                      snapshot_identifier,
                                      snapshot_cluster_identifier=None,
                                      port=None, availability_zone=None,
                                      allow_version_upgrade=None,
                                      cluster_subnet_group_name=None,
                                      publicly_accessible=None,
                                      owner_account=None,
                                      hsm_client_certificate_identifier=None,
                                      hsm_configuration_identifier=None,
                                      elastic_ip=None,
                                      cluster_parameter_group_name=None,
                                      cluster_security_groups=None,
                                      vpc_security_group_ids=None,
                                      preferred_maintenance_window=None,
                                      automated_snapshot_retention_period=None):
        """
        Creates a new cluster from a snapshot. Amazon Redshift creates
        the resulting cluster with the same configuration as the
        original cluster from which the snapshot was created, except
        that the new cluster is created with the default cluster
        security and parameter group. After Amazon Redshift creates
        the cluster you can use the ModifyCluster API to associate a
        different security group and different parameter group with
        the restored cluster.

        If you restore a cluster into a VPC, you must provide a
        cluster subnet group where you want the cluster restored.

        For more information about working with snapshots, go to
        `Amazon Redshift Snapshots`_ in the Amazon Redshift Management
        Guide .

        :type cluster_identifier: string
        :param cluster_identifier: The identifier of the cluster that will be
            created from restoring the snapshot.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens.
        + Alphabetic characters must be lowercase.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.
        + Must be unique for all clusters within an AWS account.

        :type snapshot_identifier: string
        :param snapshot_identifier: The name of the snapshot from which to
            create the new cluster. This parameter isn't case sensitive.
        Example: `my-snapshot-id`

        :type snapshot_cluster_identifier: string
        :param snapshot_cluster_identifier: The name of the cluster the source
            snapshot was created from. This parameter is required if your IAM
            user has a policy containing a snapshot resource element that
            specifies anything other than * for the cluster name.

        :type port: integer
        :param port: The port number on which the cluster accepts connections.
        Default: The same port as the original cluster.

        Constraints: Must be between `1115` and `65535`.

        :type availability_zone: string
        :param availability_zone: The Amazon EC2 Availability Zone in which to
            restore the cluster.
        Default: A random, system-chosen Availability Zone.

        Example: `us-east-1a`

        :type allow_version_upgrade: boolean
        :param allow_version_upgrade: If `True`, upgrades can be applied during
            the maintenance window to the Amazon Redshift engine that is
            running on the cluster.
        Default: `True`

        :type cluster_subnet_group_name: string
        :param cluster_subnet_group_name: The name of the subnet group where
            you want to cluster restored.
        A snapshot of cluster in VPC can be restored only in VPC. Therefore,
            you must provide subnet group name where you want the cluster
            restored.

        :type publicly_accessible: boolean
        :param publicly_accessible: If `True`, the cluster can be accessed from
            a public network.

        :type owner_account: string
        :param owner_account: The AWS customer account used to create or copy
            the snapshot. Required if you are restoring a snapshot you do not
            own, optional if you own the snapshot.

        :type hsm_client_certificate_identifier: string
        :param hsm_client_certificate_identifier: Specifies the name of the HSM
            client certificate the Amazon Redshift cluster uses to retrieve the
            data encryption keys stored in an HSM.

        :type hsm_configuration_identifier: string
        :param hsm_configuration_identifier: Specifies the name of the HSM
            configuration that contains the information the Amazon Redshift
            cluster can use to retrieve and store keys in an HSM.

        :type elastic_ip: string
        :param elastic_ip: The elastic IP (EIP) address for the cluster.

        :type cluster_parameter_group_name: string
        :param cluster_parameter_group_name:
        The name of the parameter group to be associated with this cluster.

        Default: The default Amazon Redshift cluster parameter group. For
            information about the default parameter group, go to `Working with
            Amazon Redshift Parameter Groups`_.

        Constraints:


        + Must be 1 to 255 alphanumeric characters or hyphens.
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type cluster_security_groups: list
        :param cluster_security_groups: A list of security groups to be
            associated with this cluster.
        Default: The default cluster security group for Amazon Redshift.

        Cluster security groups only apply to clusters outside of VPCs.

        :type vpc_security_group_ids: list
        :param vpc_security_group_ids: A list of Virtual Private Cloud (VPC)
            security groups to be associated with the cluster.
        Default: The default VPC security group is associated with the cluster.

        VPC security groups only apply to clusters in VPCs.

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which automated cluster maintenance can occur.
        Format: `ddd:hh24:mi-ddd:hh24:mi`

        Default: The value selected for the cluster from which the snapshot was
            taken. The following list shows the time blocks for each region
            from which the default maintenance windows are assigned.


        + **US-East (Northern Virginia) Region:** 03:00-11:00 UTC
        + **US-West (Oregon) Region** 06:00-14:00 UTC
        + **EU (Ireland) Region** 22:00-06:00 UTC
        + **Asia Pacific (Singapore) Region** 14:00-22:00 UTC
        + **Asia Pacific (Sydney) Region** 12:00-20:00 UTC
        + **Asia Pacific (Tokyo) Region** 17:00-03:00 UTC


        Valid Days: Mon | Tue | Wed | Thu | Fri | Sat | Sun

        Constraints: Minimum 30-minute window.

        :type automated_snapshot_retention_period: integer
        :param automated_snapshot_retention_period: The number of days that
            automated snapshots are retained. If the value is 0, automated
            snapshots are disabled. Even if automated snapshots are disabled,
            you can still create manual snapshots when you want with
            CreateClusterSnapshot.
        Default: The value selected for the cluster from which the snapshot was
            taken.

        Constraints: Must be a value from 0 to 35.

        """
        params = {
            'ClusterIdentifier': cluster_identifier,
            'SnapshotIdentifier': snapshot_identifier,
        }
        if snapshot_cluster_identifier is not None:
            params['SnapshotClusterIdentifier'] = snapshot_cluster_identifier
        if port is not None:
            params['Port'] = port
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if allow_version_upgrade is not None:
            params['AllowVersionUpgrade'] = str(
                allow_version_upgrade).lower()
        if cluster_subnet_group_name is not None:
            params['ClusterSubnetGroupName'] = cluster_subnet_group_name
        if publicly_accessible is not None:
            params['PubliclyAccessible'] = str(
                publicly_accessible).lower()
        if owner_account is not None:
            params['OwnerAccount'] = owner_account
        if hsm_client_certificate_identifier is not None:
            params['HsmClientCertificateIdentifier'] = hsm_client_certificate_identifier
        if hsm_configuration_identifier is not None:
            params['HsmConfigurationIdentifier'] = hsm_configuration_identifier
        if elastic_ip is not None:
            params['ElasticIp'] = elastic_ip
        if cluster_parameter_group_name is not None:
            params['ClusterParameterGroupName'] = cluster_parameter_group_name
        if cluster_security_groups is not None:
            self.build_list_params(params,
                                   cluster_security_groups,
                                   'ClusterSecurityGroups.member')
        if vpc_security_group_ids is not None:
            self.build_list_params(params,
                                   vpc_security_group_ids,
                                   'VpcSecurityGroupIds.member')
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if automated_snapshot_retention_period is not None:
            params['AutomatedSnapshotRetentionPeriod'] = automated_snapshot_retention_period
        return self._make_request(
            action='RestoreFromClusterSnapshot',
            verb='POST',
            path='/', params=params)

    def revoke_cluster_security_group_ingress(self,
                                              cluster_security_group_name,
                                              cidrip=None,
                                              ec2_security_group_name=None,
                                              ec2_security_group_owner_id=None):
        """
        Revokes an ingress rule in an Amazon Redshift security group
        for a previously authorized IP range or Amazon EC2 security
        group. To add an ingress rule, see
        AuthorizeClusterSecurityGroupIngress. For information about
        managing security groups, go to `Amazon Redshift Cluster
        Security Groups`_ in the Amazon Redshift Management Guide .

        :type cluster_security_group_name: string
        :param cluster_security_group_name: The name of the security Group from
            which to revoke the ingress rule.

        :type cidrip: string
        :param cidrip: The IP range for which to revoke access. This range must
            be a valid Classless Inter-Domain Routing (CIDR) block of IP
            addresses. If `CIDRIP` is specified, `EC2SecurityGroupName` and
            `EC2SecurityGroupOwnerId` cannot be provided.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The name of the EC2 Security Group
            whose access is to be revoked. If `EC2SecurityGroupName` is
            specified, `EC2SecurityGroupOwnerId` must also be provided and
            `CIDRIP` cannot be provided.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The AWS account number of the owner
            of the security group specified in the `EC2SecurityGroupName`
            parameter. The AWS access key ID is not an acceptable value. If
            `EC2SecurityGroupOwnerId` is specified, `EC2SecurityGroupName` must
            also be provided. and `CIDRIP` cannot be provided.
        Example: `111122223333`

        """
        params = {
            'ClusterSecurityGroupName': cluster_security_group_name,
        }
        if cidrip is not None:
            params['CIDRIP'] = cidrip
        if ec2_security_group_name is not None:
            params['EC2SecurityGroupName'] = ec2_security_group_name
        if ec2_security_group_owner_id is not None:
            params['EC2SecurityGroupOwnerId'] = ec2_security_group_owner_id
        return self._make_request(
            action='RevokeClusterSecurityGroupIngress',
            verb='POST',
            path='/', params=params)

    def revoke_snapshot_access(self, snapshot_identifier,
                               account_with_restore_access,
                               snapshot_cluster_identifier=None):
        """
        Removes the ability of the specified AWS customer account to
        restore the specified snapshot. If the account is currently
        restoring the snapshot, the restore will run to completion.

        For more information about working with snapshots, go to
        `Amazon Redshift Snapshots`_ in the Amazon Redshift Management
        Guide .

        :type snapshot_identifier: string
        :param snapshot_identifier: The identifier of the snapshot that the
            account can no longer access.

        :type snapshot_cluster_identifier: string
        :param snapshot_cluster_identifier: The identifier of the cluster the
            snapshot was created from. This parameter is required if your IAM
            user has a policy containing a snapshot resource element that
            specifies anything other than * for the cluster name.

        :type account_with_restore_access: string
        :param account_with_restore_access: The identifier of the AWS customer
            account that can no longer restore the specified snapshot.

        """
        params = {
            'SnapshotIdentifier': snapshot_identifier,
            'AccountWithRestoreAccess': account_with_restore_access,
        }
        if snapshot_cluster_identifier is not None:
            params['SnapshotClusterIdentifier'] = snapshot_cluster_identifier
        return self._make_request(
            action='RevokeSnapshotAccess',
            verb='POST',
            path='/', params=params)

    def rotate_encryption_key(self, cluster_identifier):
        """
        Rotates the encryption keys for a cluster.

        :type cluster_identifier: string
        :param cluster_identifier: The unique identifier of the cluster that
            you want to rotate the encryption keys for.
        Constraints: Must be the name of valid cluster that has encryption
            enabled.

        """
        params = {'ClusterIdentifier': cluster_identifier, }
        return self._make_request(
            action='RotateEncryptionKey',
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
            json_body = json.loads(body)
            fault_name = json_body.get('Error', {}).get('Code', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)
