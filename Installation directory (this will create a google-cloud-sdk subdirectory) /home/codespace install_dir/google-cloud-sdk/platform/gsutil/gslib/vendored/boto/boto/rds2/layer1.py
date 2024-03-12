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
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.rds2 import exceptions
from boto.compat import json


class RDSConnection(AWSQueryConnection):
    """
    Amazon Relational Database Service
    Amazon Relational Database Service (Amazon RDS) is a web service
    that makes it easier to set up, operate, and scale a relational
    database in the cloud. It provides cost-efficient, resizable
    capacity for an industry-standard relational database and manages
    common database administration tasks, freeing up developers to
    focus on what makes their applications and businesses unique.

    Amazon RDS gives you access to the capabilities of a familiar
    MySQL or Oracle database server. This means the code,
    applications, and tools you already use today with your existing
    MySQL or Oracle databases work with Amazon RDS without
    modification. Amazon RDS automatically backs up your database and
    maintains the database software that powers your DB instance.
    Amazon RDS is flexible: you can scale your database instance's
    compute resources and storage capacity to meet your application's
    demand. As with all Amazon Web Services, there are no up-front
    investments, and you pay only for the resources you use.

    This is the Amazon RDS API Reference . It contains a comprehensive
    description of all Amazon RDS Query APIs and data types. Note that
    this API is asynchronous and some actions may require polling to
    determine when an action has been applied. See the parameter
    description to determine if a change is applied immediately or on
    the next instance reboot or during the maintenance window. For
    more information on Amazon RDS concepts and usage scenarios, go to
    the `Amazon RDS User Guide`_.
    """
    APIVersion = "2013-09-09"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "rds.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidSubnet": exceptions.InvalidSubnet,
        "DBParameterGroupQuotaExceeded": exceptions.DBParameterGroupQuotaExceeded,
        "DBSubnetGroupAlreadyExists": exceptions.DBSubnetGroupAlreadyExists,
        "DBSubnetGroupQuotaExceeded": exceptions.DBSubnetGroupQuotaExceeded,
        "InstanceQuotaExceeded": exceptions.InstanceQuotaExceeded,
        "InvalidRestore": exceptions.InvalidRestore,
        "InvalidDBParameterGroupState": exceptions.InvalidDBParameterGroupState,
        "AuthorizationQuotaExceeded": exceptions.AuthorizationQuotaExceeded,
        "DBSecurityGroupAlreadyExists": exceptions.DBSecurityGroupAlreadyExists,
        "InsufficientDBInstanceCapacity": exceptions.InsufficientDBInstanceCapacity,
        "ReservedDBInstanceQuotaExceeded": exceptions.ReservedDBInstanceQuotaExceeded,
        "DBSecurityGroupNotFound": exceptions.DBSecurityGroupNotFound,
        "DBInstanceAlreadyExists": exceptions.DBInstanceAlreadyExists,
        "ReservedDBInstanceNotFound": exceptions.ReservedDBInstanceNotFound,
        "DBSubnetGroupDoesNotCoverEnoughAZs": exceptions.DBSubnetGroupDoesNotCoverEnoughAZs,
        "InvalidDBSecurityGroupState": exceptions.InvalidDBSecurityGroupState,
        "InvalidVPCNetworkState": exceptions.InvalidVPCNetworkState,
        "ReservedDBInstancesOfferingNotFound": exceptions.ReservedDBInstancesOfferingNotFound,
        "SNSTopicArnNotFound": exceptions.SNSTopicArnNotFound,
        "SNSNoAuthorization": exceptions.SNSNoAuthorization,
        "SnapshotQuotaExceeded": exceptions.SnapshotQuotaExceeded,
        "OptionGroupQuotaExceeded": exceptions.OptionGroupQuotaExceeded,
        "DBParameterGroupNotFound": exceptions.DBParameterGroupNotFound,
        "SNSInvalidTopic": exceptions.SNSInvalidTopic,
        "InvalidDBSubnetGroupState": exceptions.InvalidDBSubnetGroupState,
        "DBSubnetGroupNotFound": exceptions.DBSubnetGroupNotFound,
        "InvalidOptionGroupState": exceptions.InvalidOptionGroupState,
        "SourceNotFound": exceptions.SourceNotFound,
        "SubscriptionCategoryNotFound": exceptions.SubscriptionCategoryNotFound,
        "EventSubscriptionQuotaExceeded": exceptions.EventSubscriptionQuotaExceeded,
        "DBSecurityGroupNotSupported": exceptions.DBSecurityGroupNotSupported,
        "InvalidEventSubscriptionState": exceptions.InvalidEventSubscriptionState,
        "InvalidDBSubnetState": exceptions.InvalidDBSubnetState,
        "InvalidDBSnapshotState": exceptions.InvalidDBSnapshotState,
        "SubscriptionAlreadyExist": exceptions.SubscriptionAlreadyExist,
        "DBSecurityGroupQuotaExceeded": exceptions.DBSecurityGroupQuotaExceeded,
        "ProvisionedIopsNotAvailableInAZ": exceptions.ProvisionedIopsNotAvailableInAZ,
        "AuthorizationNotFound": exceptions.AuthorizationNotFound,
        "OptionGroupAlreadyExists": exceptions.OptionGroupAlreadyExists,
        "SubscriptionNotFound": exceptions.SubscriptionNotFound,
        "DBUpgradeDependencyFailure": exceptions.DBUpgradeDependencyFailure,
        "PointInTimeRestoreNotEnabled": exceptions.PointInTimeRestoreNotEnabled,
        "AuthorizationAlreadyExists": exceptions.AuthorizationAlreadyExists,
        "DBSubnetQuotaExceeded": exceptions.DBSubnetQuotaExceeded,
        "OptionGroupNotFound": exceptions.OptionGroupNotFound,
        "DBParameterGroupAlreadyExists": exceptions.DBParameterGroupAlreadyExists,
        "DBInstanceNotFound": exceptions.DBInstanceNotFound,
        "ReservedDBInstanceAlreadyExists": exceptions.ReservedDBInstanceAlreadyExists,
        "InvalidDBInstanceState": exceptions.InvalidDBInstanceState,
        "DBSnapshotNotFound": exceptions.DBSnapshotNotFound,
        "DBSnapshotAlreadyExists": exceptions.DBSnapshotAlreadyExists,
        "StorageQuotaExceeded": exceptions.StorageQuotaExceeded,
        "SubnetAlreadyInUse": exceptions.SubnetAlreadyInUse,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint

        super(RDSConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def add_source_identifier_to_subscription(self, subscription_name,
                                              source_identifier):
        """
        Adds a source identifier to an existing RDS event notification
        subscription.

        :type subscription_name: string
        :param subscription_name: The name of the RDS event notification
            subscription you want to add a source identifier to.

        :type source_identifier: string
        :param source_identifier:
        The identifier of the event source to be added. An identifier must
            begin with a letter and must contain only ASCII letters, digits,
            and hyphens; it cannot end with a hyphen or contain two consecutive
            hyphens.

        Constraints:


        + If the source type is a DB instance, then a `DBInstanceIdentifier`
              must be supplied.
        + If the source type is a DB security group, a `DBSecurityGroupName`
              must be supplied.
        + If the source type is a DB parameter group, a `DBParameterGroupName`
              must be supplied.
        + If the source type is a DB snapshot, a `DBSnapshotIdentifier` must be
              supplied.

        """
        params = {
            'SubscriptionName': subscription_name,
            'SourceIdentifier': source_identifier,
        }
        return self._make_request(
            action='AddSourceIdentifierToSubscription',
            verb='POST',
            path='/', params=params)

    def add_tags_to_resource(self, resource_name, tags):
        """
        Adds metadata tags to an Amazon RDS resource. These tags can
        also be used with cost allocation reporting to track cost
        associated with Amazon RDS resources, or used in Condition
        statement in IAM policy for Amazon RDS.

        For an overview on tagging Amazon RDS resources, see `Tagging
        Amazon RDS Resources`_.

        :type resource_name: string
        :param resource_name: The Amazon RDS resource the tags will be added
            to. This value is an Amazon Resource Name (ARN). For information
            about creating an ARN, see ` Constructing an RDS Amazon Resource
            Name (ARN)`_.

        :type tags: list
        :param tags: The tags to be assigned to the Amazon RDS resource.
            Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {'ResourceName': resource_name, }
        self.build_complex_list_params(
            params, tags,
            'Tags.member',
            ('Key', 'Value'))
        return self._make_request(
            action='AddTagsToResource',
            verb='POST',
            path='/', params=params)

    def authorize_db_security_group_ingress(self, db_security_group_name,
                                            cidrip=None,
                                            ec2_security_group_name=None,
                                            ec2_security_group_id=None,
                                            ec2_security_group_owner_id=None):
        """
        Enables ingress to a DBSecurityGroup using one of two forms of
        authorization. First, EC2 or VPC security groups can be added
        to the DBSecurityGroup if the application using the database
        is running on EC2 or VPC instances. Second, IP ranges are
        available if the application accessing your database is
        running on the Internet. Required parameters for this API are
        one of CIDR range, EC2SecurityGroupId for VPC, or
        (EC2SecurityGroupOwnerId and either EC2SecurityGroupName or
        EC2SecurityGroupId for non-VPC).
        You cannot authorize ingress from an EC2 security group in one
        Region to an Amazon RDS DB instance in another. You cannot
        authorize ingress from a VPC security group in one VPC to an
        Amazon RDS DB instance in another.
        For an overview of CIDR ranges, go to the `Wikipedia
        Tutorial`_.

        :type db_security_group_name: string
        :param db_security_group_name: The name of the DB security group to add
            authorization to.

        :type cidrip: string
        :param cidrip: The IP range to authorize.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: Name of the EC2 security group to
            authorize. For VPC DB security groups, `EC2SecurityGroupId` must be
            provided. Otherwise, EC2SecurityGroupOwnerId and either
            `EC2SecurityGroupName` or `EC2SecurityGroupId` must be provided.

        :type ec2_security_group_id: string
        :param ec2_security_group_id: Id of the EC2 security group to
            authorize. For VPC DB security groups, `EC2SecurityGroupId` must be
            provided. Otherwise, EC2SecurityGroupOwnerId and either
            `EC2SecurityGroupName` or `EC2SecurityGroupId` must be provided.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: AWS Account Number of the owner of
            the EC2 security group specified in the EC2SecurityGroupName
            parameter. The AWS Access Key ID is not an acceptable value. For
            VPC DB security groups, `EC2SecurityGroupId` must be provided.
            Otherwise, EC2SecurityGroupOwnerId and either
            `EC2SecurityGroupName` or `EC2SecurityGroupId` must be provided.

        """
        params = {'DBSecurityGroupName': db_security_group_name, }
        if cidrip is not None:
            params['CIDRIP'] = cidrip
        if ec2_security_group_name is not None:
            params['EC2SecurityGroupName'] = ec2_security_group_name
        if ec2_security_group_id is not None:
            params['EC2SecurityGroupId'] = ec2_security_group_id
        if ec2_security_group_owner_id is not None:
            params['EC2SecurityGroupOwnerId'] = ec2_security_group_owner_id
        return self._make_request(
            action='AuthorizeDBSecurityGroupIngress',
            verb='POST',
            path='/', params=params)

    def copy_db_snapshot(self, source_db_snapshot_identifier,
                         target_db_snapshot_identifier, tags=None):
        """
        Copies the specified DBSnapshot. The source DBSnapshot must be
        in the "available" state.

        :type source_db_snapshot_identifier: string
        :param source_db_snapshot_identifier: The identifier for the source DB
            snapshot.
        Constraints:


        + Must be the identifier for a valid system snapshot in the "available"
              state.


        Example: `rds:mydb-2012-04-02-00-01`

        :type target_db_snapshot_identifier: string
        :param target_db_snapshot_identifier: The identifier for the copied
            snapshot.
        Constraints:


        + Cannot be null, empty, or blank
        + Must contain from 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        Example: `my-db-snapshot`

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]
        """
        params = {
            'SourceDBSnapshotIdentifier': source_db_snapshot_identifier,
            'TargetDBSnapshotIdentifier': target_db_snapshot_identifier,
        }
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CopyDBSnapshot',
            verb='POST',
            path='/', params=params)

    def create_db_instance(self, db_instance_identifier, allocated_storage,
                           db_instance_class, engine, master_username,
                           master_user_password, db_name=None,
                           db_security_groups=None,
                           vpc_security_group_ids=None,
                           availability_zone=None, db_subnet_group_name=None,
                           preferred_maintenance_window=None,
                           db_parameter_group_name=None,
                           backup_retention_period=None,
                           preferred_backup_window=None, port=None,
                           multi_az=None, engine_version=None,
                           auto_minor_version_upgrade=None,
                           license_model=None, iops=None,
                           option_group_name=None, character_set_name=None,
                           publicly_accessible=None, tags=None):
        """
        Creates a new DB instance.

        :type db_name: string
        :param db_name: The meaning of this parameter differs according to the
            database engine you use.
        **MySQL**

        The name of the database to create when the DB instance is created. If
            this parameter is not specified, no database is created in the DB
            instance.

        Constraints:


        + Must contain 1 to 64 alphanumeric characters
        + Cannot be a word reserved by the specified database engine


        Type: String

        **Oracle**

        The Oracle System ID (SID) of the created DB instance.

        Default: `ORCL`

        Constraints:


        + Cannot be longer than 8 characters


        **SQL Server**

        Not applicable. Must be null.

        :type db_instance_identifier: string
        :param db_instance_identifier: The DB instance identifier. This
            parameter is stored as a lowercase string.
        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens (1 to 15
              for SQL Server).
        + First character must be a letter.
        + Cannot end with a hyphen or contain two consecutive hyphens.


        Example: `mydbinstance`

        :type allocated_storage: integer
        :param allocated_storage: The amount of storage (in gigabytes) to be
            initially allocated for the database instance.
        **MySQL**

        Constraints: Must be an integer from 5 to 1024.

        Type: Integer

        **Oracle**

        Constraints: Must be an integer from 10 to 1024.

        **SQL Server**

        Constraints: Must be an integer from 200 to 1024 (Standard Edition and
            Enterprise Edition) or from 30 to 1024 (Express Edition and Web
            Edition)

        :type db_instance_class: string
        :param db_instance_class: The compute and memory capacity of the DB
            instance.
        Valid Values: `db.t1.micro | db.m1.small | db.m1.medium | db.m1.large |
            db.m1.xlarge | db.m2.xlarge |db.m2.2xlarge | db.m2.4xlarge`

        :type engine: string
        :param engine: The name of the database engine to be used for this
            instance.
        Valid Values: `MySQL` | `oracle-se1` | `oracle-se` | `oracle-ee` |
            `sqlserver-ee` | `sqlserver-se` | `sqlserver-ex` | `sqlserver-web`

        :type master_username: string
        :param master_username:
        The name of master user for the client DB instance.

        **MySQL**

        Constraints:


        + Must be 1 to 16 alphanumeric characters.
        + First character must be a letter.
        + Cannot be a reserved word for the chosen database engine.


        Type: String

        **Oracle**

        Constraints:


        + Must be 1 to 30 alphanumeric characters.
        + First character must be a letter.
        + Cannot be a reserved word for the chosen database engine.


        **SQL Server**

        Constraints:


        + Must be 1 to 128 alphanumeric characters.
        + First character must be a letter.
        + Cannot be a reserved word for the chosen database engine.

        :type master_user_password: string
        :param master_user_password: The password for the master database user.
            Can be any printable ASCII character except "/", '"', or "@".
        Type: String

        **MySQL**

        Constraints: Must contain from 8 to 41 characters.

        **Oracle**

        Constraints: Must contain from 8 to 30 characters.

        **SQL Server**

        Constraints: Must contain from 8 to 128 characters.

        :type db_security_groups: list
        :param db_security_groups: A list of DB security groups to associate
            with this DB instance.
        Default: The default DB security group for the database engine.

        :type vpc_security_group_ids: list
        :param vpc_security_group_ids: A list of EC2 VPC security groups to
            associate with this DB instance.
        Default: The default EC2 VPC security group for the DB subnet group's
            VPC.

        :type availability_zone: string
        :param availability_zone: The EC2 Availability Zone that the database
            instance will be created in.
        Default: A random, system-chosen Availability Zone in the endpoint's
            region.

        Example: `us-east-1d`

        Constraint: The AvailabilityZone parameter cannot be specified if the
            MultiAZ parameter is set to `True`. The specified Availability Zone
            must be in the same region as the current endpoint.

        :type db_subnet_group_name: string
        :param db_subnet_group_name: A DB subnet group to associate with this
            DB instance.
        If there is no DB subnet group, then it is a non-VPC DB instance.

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which system maintenance can occur.
        Format: `ddd:hh24:mi-ddd:hh24:mi`

        Default: A 30-minute window selected at random from an 8-hour block of
            time per region, occurring on a random day of the week. To see the
            time blocks available, see ` Adjusting the Preferred Maintenance
            Window`_ in the Amazon RDS User Guide.

        Valid Days: Mon, Tue, Wed, Thu, Fri, Sat, Sun

        Constraints: Minimum 30-minute window.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of the DB parameter group to associate with this DB instance.
            If this argument is omitted, the default DBParameterGroup for the
            specified engine will be used.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type backup_retention_period: integer
        :param backup_retention_period:
        The number of days for which automated backups are retained. Setting
            this parameter to a positive number enables backups. Setting this
            parameter to 0 disables automated backups.

        Default: 1

        Constraints:


        + Must be a value from 0 to 8
        + Cannot be set to 0 if the DB instance is a master instance with read
              replicas

        :type preferred_backup_window: string
        :param preferred_backup_window: The daily time range during which
            automated backups are created if automated backups are enabled,
            using the `BackupRetentionPeriod` parameter.
        Default: A 30-minute window selected at random from an 8-hour block of
            time per region. See the Amazon RDS User Guide for the time blocks
            for each region from which the default backup windows are assigned.

        Constraints: Must be in the format `hh24:mi-hh24:mi`. Times should be
            Universal Time Coordinated (UTC). Must not conflict with the
            preferred maintenance window. Must be at least 30 minutes.

        :type port: integer
        :param port: The port number on which the database accepts connections.
        **MySQL**

        Default: `3306`

        Valid Values: `1150-65535`

        Type: Integer

        **Oracle**

        Default: `1521`

        Valid Values: `1150-65535`

        **SQL Server**

        Default: `1433`

        Valid Values: `1150-65535` except for `1434` and `3389`.

        :type multi_az: boolean
        :param multi_az: Specifies if the DB instance is a Multi-AZ deployment.
            You cannot set the AvailabilityZone parameter if the MultiAZ
            parameter is set to true.

        :type engine_version: string
        :param engine_version: The version number of the database engine to
            use.
        **MySQL**

        Example: `5.1.42`

        Type: String

        **Oracle**

        Example: `11.2.0.2.v2`

        Type: String

        **SQL Server**

        Example: `10.50.2789.0.v1`

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Indicates that minor engine upgrades
            will be applied automatically to the DB instance during the
            maintenance window.
        Default: `True`

        :type license_model: string
        :param license_model: License model information for this DB instance.
        Valid values: `license-included` | `bring-your-own-license` | `general-
            public-license`

        :type iops: integer
        :param iops: The amount of Provisioned IOPS (input/output operations
            per second) to be initially allocated for the DB instance.
        Constraints: Must be an integer greater than 1000.

        :type option_group_name: string
        :param option_group_name: Indicates that the DB instance should be
            associated with the specified option group.
        Permanent options, such as the TDE option for Oracle Advanced Security
            TDE, cannot be removed from an option group, and that option group
            cannot be removed from a DB instance once it is associated with a
            DB instance

        :type character_set_name: string
        :param character_set_name: For supported engines, indicates that the DB
            instance should be associated with the specified CharacterSet.

        :type publicly_accessible: boolean
        :param publicly_accessible: Specifies the accessibility options for the
            DB instance. A value of true specifies an Internet-facing instance
            with a publicly resolvable DNS name, which resolves to a public IP
            address. A value of false specifies an internal instance with a DNS
            name that resolves to a private IP address.
        Default: The default behavior varies depending on whether a VPC has
            been requested or not. The following list shows the default
            behavior in each case.


        + **Default VPC:**true
        + **VPC:**false


        If no DB subnet group has been specified as part of the request and the
            PubliclyAccessible value has not been set, the DB instance will be
            publicly accessible. If a specific DB subnet group has been
            specified as part of the request and the PubliclyAccessible value
            has not been set, the DB instance will be private.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBInstanceIdentifier': db_instance_identifier,
            'AllocatedStorage': allocated_storage,
            'DBInstanceClass': db_instance_class,
            'Engine': engine,
            'MasterUsername': master_username,
            'MasterUserPassword': master_user_password,
        }
        if db_name is not None:
            params['DBName'] = db_name
        if db_security_groups is not None:
            self.build_list_params(params,
                                   db_security_groups,
                                   'DBSecurityGroups.member')
        if vpc_security_group_ids is not None:
            self.build_list_params(params,
                                   vpc_security_group_ids,
                                   'VpcSecurityGroupIds.member')
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if db_subnet_group_name is not None:
            params['DBSubnetGroupName'] = db_subnet_group_name
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if db_parameter_group_name is not None:
            params['DBParameterGroupName'] = db_parameter_group_name
        if backup_retention_period is not None:
            params['BackupRetentionPeriod'] = backup_retention_period
        if preferred_backup_window is not None:
            params['PreferredBackupWindow'] = preferred_backup_window
        if port is not None:
            params['Port'] = port
        if multi_az is not None:
            params['MultiAZ'] = str(
                multi_az).lower()
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        if license_model is not None:
            params['LicenseModel'] = license_model
        if iops is not None:
            params['Iops'] = iops
        if option_group_name is not None:
            params['OptionGroupName'] = option_group_name
        if character_set_name is not None:
            params['CharacterSetName'] = character_set_name
        if publicly_accessible is not None:
            params['PubliclyAccessible'] = str(
                publicly_accessible).lower()
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateDBInstance',
            verb='POST',
            path='/', params=params)

    def create_db_instance_read_replica(self, db_instance_identifier,
                                        source_db_instance_identifier,
                                        db_instance_class=None,
                                        availability_zone=None, port=None,
                                        auto_minor_version_upgrade=None,
                                        iops=None, option_group_name=None,
                                        publicly_accessible=None, tags=None):
        """
        Creates a DB instance that acts as a read replica of a source
        DB instance.

        All read replica DB instances are created as Single-AZ
        deployments with backups disabled. All other DB instance
        attributes (including DB security groups and DB parameter
        groups) are inherited from the source DB instance, except as
        specified below.

        The source DB instance must have backup retention enabled.

        :type db_instance_identifier: string
        :param db_instance_identifier: The DB instance identifier of the read
            replica. This is the unique key that identifies a DB instance. This
            parameter is stored as a lowercase string.

        :type source_db_instance_identifier: string
        :param source_db_instance_identifier: The identifier of the DB instance
            that will act as the source for the read replica. Each DB instance
            can have up to five read replicas.
        Constraints: Must be the identifier of an existing DB instance that is
            not already a read replica DB instance.

        :type db_instance_class: string
        :param db_instance_class: The compute and memory capacity of the read
            replica.
        Valid Values: `db.m1.small | db.m1.medium | db.m1.large | db.m1.xlarge
            | db.m2.xlarge |db.m2.2xlarge | db.m2.4xlarge`

        Default: Inherits from the source DB instance.

        :type availability_zone: string
        :param availability_zone: The Amazon EC2 Availability Zone that the
            read replica will be created in.
        Default: A random, system-chosen Availability Zone in the endpoint's
            region.

        Example: `us-east-1d`

        :type port: integer
        :param port: The port number that the DB instance uses for connections.
        Default: Inherits from the source DB instance

        Valid Values: `1150-65535`

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Indicates that minor engine upgrades
            will be applied automatically to the read replica during the
            maintenance window.
        Default: Inherits from the source DB instance

        :type iops: integer
        :param iops: The amount of Provisioned IOPS (input/output operations
            per second) to be initially allocated for the DB instance.

        :type option_group_name: string
        :param option_group_name: The option group the DB instance will be
            associated with. If omitted, the default option group for the
            engine specified will be used.

        :type publicly_accessible: boolean
        :param publicly_accessible: Specifies the accessibility options for the
            DB instance. A value of true specifies an Internet-facing instance
            with a publicly resolvable DNS name, which resolves to a public IP
            address. A value of false specifies an internal instance with a DNS
            name that resolves to a private IP address.
        Default: The default behavior varies depending on whether a VPC has
            been requested or not. The following list shows the default
            behavior in each case.


        + **Default VPC:**true
        + **VPC:**false


        If no DB subnet group has been specified as part of the request and the
            PubliclyAccessible value has not been set, the DB instance will be
            publicly accessible. If a specific DB subnet group has been
            specified as part of the request and the PubliclyAccessible value
            has not been set, the DB instance will be private.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBInstanceIdentifier': db_instance_identifier,
            'SourceDBInstanceIdentifier': source_db_instance_identifier,
        }
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if port is not None:
            params['Port'] = port
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        if iops is not None:
            params['Iops'] = iops
        if option_group_name is not None:
            params['OptionGroupName'] = option_group_name
        if publicly_accessible is not None:
            params['PubliclyAccessible'] = str(
                publicly_accessible).lower()
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateDBInstanceReadReplica',
            verb='POST',
            path='/', params=params)

    def create_db_parameter_group(self, db_parameter_group_name,
                                  db_parameter_group_family, description,
                                  tags=None):
        """
        Creates a new DB parameter group.

        A DB parameter group is initially created with the default
        parameters for the database engine used by the DB instance. To
        provide custom values for any of the parameters, you must
        modify the group after creating it using
        ModifyDBParameterGroup . Once you've created a DB parameter
        group, you need to associate it with your DB instance using
        ModifyDBInstance . When you associate a new DB parameter group
        with a running DB instance, you need to reboot the DB Instance
        for the new DB parameter group and associated settings to take
        effect.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of the DB parameter group.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        This value is stored as a lower-case string.

        :type db_parameter_group_family: string
        :param db_parameter_group_family: The DB parameter group family name. A
            DB parameter group can be associated with one and only one DB
            parameter group family, and can be applied only to a DB instance
            running a database engine and engine version compatible with that
            DB parameter group family.

        :type description: string
        :param description: The description for the DB parameter group.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBParameterGroupName': db_parameter_group_name,
            'DBParameterGroupFamily': db_parameter_group_family,
            'Description': description,
        }
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateDBParameterGroup',
            verb='POST',
            path='/', params=params)

    def create_db_security_group(self, db_security_group_name,
                                 db_security_group_description, tags=None):
        """
        Creates a new DB security group. DB security groups control
        access to a DB instance.

        :type db_security_group_name: string
        :param db_security_group_name: The name for the DB security group. This
            value is stored as a lowercase string.
        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens
        + Must not be "Default"
        + May not contain spaces


        Example: `mysecuritygroup`

        :type db_security_group_description: string
        :param db_security_group_description: The description for the DB
            security group.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBSecurityGroupName': db_security_group_name,
            'DBSecurityGroupDescription': db_security_group_description,
        }
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateDBSecurityGroup',
            verb='POST',
            path='/', params=params)

    def create_db_snapshot(self, db_snapshot_identifier,
                           db_instance_identifier, tags=None):
        """
        Creates a DBSnapshot. The source DBInstance must be in
        "available" state.

        :type db_snapshot_identifier: string
        :param db_snapshot_identifier: The identifier for the DB snapshot.
        Constraints:


        + Cannot be null, empty, or blank
        + Must contain from 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        Example: `my-snapshot-id`

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The DB instance identifier. This is the unique key that identifies a DB
            instance. This parameter isn't case sensitive.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBSnapshotIdentifier': db_snapshot_identifier,
            'DBInstanceIdentifier': db_instance_identifier,
        }
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateDBSnapshot',
            verb='POST',
            path='/', params=params)

    def create_db_subnet_group(self, db_subnet_group_name,
                               db_subnet_group_description, subnet_ids,
                               tags=None):
        """
        Creates a new DB subnet group. DB subnet groups must contain
        at least one subnet in at least two AZs in the region.

        :type db_subnet_group_name: string
        :param db_subnet_group_name: The name for the DB subnet group. This
            value is stored as a lowercase string.
        Constraints: Must contain no more than 255 alphanumeric characters or
            hyphens. Must not be "Default".

        Example: `mySubnetgroup`

        :type db_subnet_group_description: string
        :param db_subnet_group_description: The description for the DB subnet
            group.

        :type subnet_ids: list
        :param subnet_ids: The EC2 Subnet IDs for the DB subnet group.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBSubnetGroupName': db_subnet_group_name,
            'DBSubnetGroupDescription': db_subnet_group_description,
        }
        self.build_list_params(params,
                               subnet_ids,
                               'SubnetIds.member')
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateDBSubnetGroup',
            verb='POST',
            path='/', params=params)

    def create_event_subscription(self, subscription_name, sns_topic_arn,
                                  source_type=None, event_categories=None,
                                  source_ids=None, enabled=None, tags=None):
        """
        Creates an RDS event notification subscription. This action
        requires a topic ARN (Amazon Resource Name) created by either
        the RDS console, the SNS console, or the SNS API. To obtain an
        ARN with SNS, you must create a topic in Amazon SNS and
        subscribe to the topic. The ARN is displayed in the SNS
        console.

        You can specify the type of source (SourceType) you want to be
        notified of, provide a list of RDS sources (SourceIds) that
        triggers the events, and provide a list of event categories
        (EventCategories) for events you want to be notified of. For
        example, you can specify SourceType = db-instance, SourceIds =
        mydbinstance1, mydbinstance2 and EventCategories =
        Availability, Backup.

        If you specify both the SourceType and SourceIds, such as
        SourceType = db-instance and SourceIdentifier = myDBInstance1,
        you will be notified of all the db-instance events for the
        specified source. If you specify a SourceType but do not
        specify a SourceIdentifier, you will receive notice of the
        events for that source type for all your RDS sources. If you
        do not specify either the SourceType nor the SourceIdentifier,
        you will be notified of events generated from all RDS sources
        belonging to your customer account.

        :type subscription_name: string
        :param subscription_name: The name of the subscription.
        Constraints: The name must be less than 255 characters.

        :type sns_topic_arn: string
        :param sns_topic_arn: The Amazon Resource Name (ARN) of the SNS topic
            created for event notification. The ARN is created by Amazon SNS
            when you create a topic and subscribe to it.

        :type source_type: string
        :param source_type: The type of source that will be generating the
            events. For example, if you want to be notified of events generated
            by a DB instance, you would set this parameter to db-instance. if
            this value is not specified, all events are returned.
        Valid values: db-instance | db-parameter-group | db-security-group |
            db-snapshot

        :type event_categories: list
        :param event_categories: A list of event categories for a SourceType
            that you want to subscribe to. You can see a list of the categories
            for a given SourceType in the `Events`_ topic in the Amazon RDS
            User Guide or by using the **DescribeEventCategories** action.

        :type source_ids: list
        :param source_ids:
        The list of identifiers of the event sources for which events will be
            returned. If not specified, then all sources are included in the
            response. An identifier must begin with a letter and must contain
            only ASCII letters, digits, and hyphens; it cannot end with a
            hyphen or contain two consecutive hyphens.

        Constraints:


        + If SourceIds are supplied, SourceType must also be provided.
        + If the source type is a DB instance, then a `DBInstanceIdentifier`
              must be supplied.
        + If the source type is a DB security group, a `DBSecurityGroupName`
              must be supplied.
        + If the source type is a DB parameter group, a `DBParameterGroupName`
              must be supplied.
        + If the source type is a DB snapshot, a `DBSnapshotIdentifier` must be
              supplied.

        :type enabled: boolean
        :param enabled: A Boolean value; set to **true** to activate the
            subscription, set to **false** to create the subscription but not
            active it.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'SubscriptionName': subscription_name,
            'SnsTopicArn': sns_topic_arn,
        }
        if source_type is not None:
            params['SourceType'] = source_type
        if event_categories is not None:
            self.build_list_params(params,
                                   event_categories,
                                   'EventCategories.member')
        if source_ids is not None:
            self.build_list_params(params,
                                   source_ids,
                                   'SourceIds.member')
        if enabled is not None:
            params['Enabled'] = str(
                enabled).lower()
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateEventSubscription',
            verb='POST',
            path='/', params=params)

    def create_option_group(self, option_group_name, engine_name,
                            major_engine_version, option_group_description,
                            tags=None):
        """
        Creates a new option group. You can create up to 20 option
        groups.

        :type option_group_name: string
        :param option_group_name: Specifies the name of the option group to be
            created.
        Constraints:


        + Must be 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        Example: `myoptiongroup`

        :type engine_name: string
        :param engine_name: Specifies the name of the engine that this option
            group should be associated with.

        :type major_engine_version: string
        :param major_engine_version: Specifies the major version of the engine
            that this option group should be associated with.

        :type option_group_description: string
        :param option_group_description: The description of the option group.

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'OptionGroupName': option_group_name,
            'EngineName': engine_name,
            'MajorEngineVersion': major_engine_version,
            'OptionGroupDescription': option_group_description,
        }
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateOptionGroup',
            verb='POST',
            path='/', params=params)

    def delete_db_instance(self, db_instance_identifier,
                           skip_final_snapshot=None,
                           final_db_snapshot_identifier=None):
        """
        The DeleteDBInstance action deletes a previously provisioned
        DB instance. A successful response from the web service
        indicates the request was received correctly. When you delete
        a DB instance, all automated backups for that instance are
        deleted and cannot be recovered. Manual DB snapshots of the DB
        instance to be deleted are not deleted.

        If a final DB snapshot is requested the status of the RDS
        instance will be "deleting" until the DB snapshot is created.
        The API action `DescribeDBInstance` is used to monitor the
        status of this operation. The action cannot be canceled or
        reverted once submitted.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The DB instance identifier for the DB instance to be deleted. This
            parameter isn't case sensitive.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type skip_final_snapshot: boolean
        :param skip_final_snapshot: Determines whether a final DB snapshot is
            created before the DB instance is deleted. If `True` is specified,
            no DBSnapshot is created. If false is specified, a DB snapshot is
            created before the DB instance is deleted.
        The FinalDBSnapshotIdentifier parameter must be specified if
            SkipFinalSnapshot is `False`.

        Default: `False`

        :type final_db_snapshot_identifier: string
        :param final_db_snapshot_identifier:
        The DBSnapshotIdentifier of the new DBSnapshot created when
            SkipFinalSnapshot is set to `False`.

        Specifying this parameter and also setting the SkipFinalShapshot
            parameter to true results in an error.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        """
        params = {'DBInstanceIdentifier': db_instance_identifier, }
        if skip_final_snapshot is not None:
            params['SkipFinalSnapshot'] = str(
                skip_final_snapshot).lower()
        if final_db_snapshot_identifier is not None:
            params['FinalDBSnapshotIdentifier'] = final_db_snapshot_identifier
        return self._make_request(
            action='DeleteDBInstance',
            verb='POST',
            path='/', params=params)

    def delete_db_parameter_group(self, db_parameter_group_name):
        """
        Deletes a specified DBParameterGroup. The DBParameterGroup
        cannot be associated with any RDS instances to be deleted.
        The specified DB parameter group cannot be associated with any
        DB instances.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of the DB parameter group.

        Constraints:


        + Must be the name of an existing DB parameter group
        + You cannot delete a default DB parameter group
        + Cannot be associated with any DB instances

        """
        params = {'DBParameterGroupName': db_parameter_group_name, }
        return self._make_request(
            action='DeleteDBParameterGroup',
            verb='POST',
            path='/', params=params)

    def delete_db_security_group(self, db_security_group_name):
        """
        Deletes a DB security group.
        The specified DB security group must not be associated with
        any DB instances.

        :type db_security_group_name: string
        :param db_security_group_name:
        The name of the DB security group to delete.

        You cannot delete the default DB security group.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens
        + Must not be "Default"
        + May not contain spaces

        """
        params = {'DBSecurityGroupName': db_security_group_name, }
        return self._make_request(
            action='DeleteDBSecurityGroup',
            verb='POST',
            path='/', params=params)

    def delete_db_snapshot(self, db_snapshot_identifier):
        """
        Deletes a DBSnapshot.
        The DBSnapshot must be in the `available` state to be deleted.

        :type db_snapshot_identifier: string
        :param db_snapshot_identifier: The DBSnapshot identifier.
        Constraints: Must be the name of an existing DB snapshot in the
            `available` state.

        """
        params = {'DBSnapshotIdentifier': db_snapshot_identifier, }
        return self._make_request(
            action='DeleteDBSnapshot',
            verb='POST',
            path='/', params=params)

    def delete_db_subnet_group(self, db_subnet_group_name):
        """
        Deletes a DB subnet group.
        The specified database subnet group must not be associated
        with any DB instances.

        :type db_subnet_group_name: string
        :param db_subnet_group_name:
        The name of the database subnet group to delete.

        You cannot delete the default subnet group.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        """
        params = {'DBSubnetGroupName': db_subnet_group_name, }
        return self._make_request(
            action='DeleteDBSubnetGroup',
            verb='POST',
            path='/', params=params)

    def delete_event_subscription(self, subscription_name):
        """
        Deletes an RDS event notification subscription.

        :type subscription_name: string
        :param subscription_name: The name of the RDS event notification
            subscription you want to delete.

        """
        params = {'SubscriptionName': subscription_name, }
        return self._make_request(
            action='DeleteEventSubscription',
            verb='POST',
            path='/', params=params)

    def delete_option_group(self, option_group_name):
        """
        Deletes an existing option group.

        :type option_group_name: string
        :param option_group_name:
        The name of the option group to be deleted.

        You cannot delete default option groups.

        """
        params = {'OptionGroupName': option_group_name, }
        return self._make_request(
            action='DeleteOptionGroup',
            verb='POST',
            path='/', params=params)

    def describe_db_engine_versions(self, engine=None, engine_version=None,
                                    db_parameter_group_family=None,
                                    max_records=None, marker=None,
                                    default_only=None,
                                    list_supported_character_sets=None):
        """
        Returns a list of the available DB engines.

        :type engine: string
        :param engine: The database engine to return.

        :type engine_version: string
        :param engine_version: The database engine version to return.
        Example: `5.1.49`

        :type db_parameter_group_family: string
        :param db_parameter_group_family:
        The name of a specific DB parameter group family to return details for.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more than the `MaxRecords` value is available, a
            pagination token called a marker is included in the response so
            that the following results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            request. If this parameter is specified, the response includes only
            records beyond the marker, up to the value specified by
            `MaxRecords`.

        :type default_only: boolean
        :param default_only: Indicates that only the default version of the
            specified engine or engine and major version combination is
            returned.

        :type list_supported_character_sets: boolean
        :param list_supported_character_sets: If this parameter is specified,
            and if the requested engine supports the CharacterSetName parameter
            for CreateDBInstance, the response includes a list of supported
            character sets for each engine version.

        """
        params = {}
        if engine is not None:
            params['Engine'] = engine
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if db_parameter_group_family is not None:
            params['DBParameterGroupFamily'] = db_parameter_group_family
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        if default_only is not None:
            params['DefaultOnly'] = str(
                default_only).lower()
        if list_supported_character_sets is not None:
            params['ListSupportedCharacterSets'] = str(
                list_supported_character_sets).lower()
        return self._make_request(
            action='DescribeDBEngineVersions',
            verb='POST',
            path='/', params=params)

    def describe_db_instances(self, db_instance_identifier=None,
                              filters=None, max_records=None, marker=None):
        """
        Returns information about provisioned RDS instances. This API
        supports pagination.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The user-supplied instance identifier. If this parameter is specified,
            information from only the specific DB instance is returned. This
            parameter isn't case sensitive.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeDBInstances request. If this parameter is specified, the
            response includes only records beyond the marker, up to the value
            specified by `MaxRecords` .

        """
        params = {}
        if db_instance_identifier is not None:
            params['DBInstanceIdentifier'] = db_instance_identifier
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBInstances',
            verb='POST',
            path='/', params=params)

    def describe_db_log_files(self, db_instance_identifier,
                              filename_contains=None, file_last_written=None,
                              file_size=None, max_records=None, marker=None):
        """
        Returns a list of DB log files for the DB instance.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The customer-assigned name of the DB instance that contains the log
            files you want to list.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type filename_contains: string
        :param filename_contains: Filters the available log files for log file
            names that contain the specified string.

        :type file_last_written: long
        :param file_last_written: Filters the available log files for files
            written since the specified date, in POSIX timestamp format.

        :type file_size: long
        :param file_size: Filters the available log files for files larger than
            the specified size.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified MaxRecords
            value, a pagination token called a marker is included in the
            response so that the remaining results can be retrieved.

        :type marker: string
        :param marker: The pagination token provided in the previous request.
            If this parameter is specified the response includes only records
            beyond the marker, up to MaxRecords.

        """
        params = {'DBInstanceIdentifier': db_instance_identifier, }
        if filename_contains is not None:
            params['FilenameContains'] = filename_contains
        if file_last_written is not None:
            params['FileLastWritten'] = file_last_written
        if file_size is not None:
            params['FileSize'] = file_size
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBLogFiles',
            verb='POST',
            path='/', params=params)

    def describe_db_parameter_groups(self, db_parameter_group_name=None,
                                     filters=None, max_records=None,
                                     marker=None):
        """
        Returns a list of `DBParameterGroup` descriptions. If a
        `DBParameterGroupName` is specified, the list will contain
        only the description of the specified DB parameter group.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of a specific DB parameter group to return details for.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            `DescribeDBParameterGroups` request. If this parameter is
            specified, the response includes only records beyond the marker, up
            to the value specified by `MaxRecords`.

        """
        params = {}
        if db_parameter_group_name is not None:
            params['DBParameterGroupName'] = db_parameter_group_name
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBParameterGroups',
            verb='POST',
            path='/', params=params)

    def describe_db_parameters(self, db_parameter_group_name, source=None,
                               max_records=None, marker=None):
        """
        Returns the detailed parameter list for a particular DB
        parameter group.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of a specific DB parameter group to return details for.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type source: string
        :param source: The parameter types to return.
        Default: All parameter types returned

        Valid Values: `user | system | engine-default`

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            `DescribeDBParameters` request. If this parameter is specified, the
            response includes only records beyond the marker, up to the value
            specified by `MaxRecords`.

        """
        params = {'DBParameterGroupName': db_parameter_group_name, }
        if source is not None:
            params['Source'] = source
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBParameters',
            verb='POST',
            path='/', params=params)

    def describe_db_security_groups(self, db_security_group_name=None,
                                    filters=None, max_records=None,
                                    marker=None):
        """
        Returns a list of `DBSecurityGroup` descriptions. If a
        `DBSecurityGroupName` is specified, the list will contain only
        the descriptions of the specified DB security group.

        :type db_security_group_name: string
        :param db_security_group_name: The name of the DB security group to
            return details for.

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeDBSecurityGroups request. If this parameter is specified,
            the response includes only records beyond the marker, up to the
            value specified by `MaxRecords`.

        """
        params = {}
        if db_security_group_name is not None:
            params['DBSecurityGroupName'] = db_security_group_name
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBSecurityGroups',
            verb='POST',
            path='/', params=params)

    def describe_db_snapshots(self, db_instance_identifier=None,
                              db_snapshot_identifier=None,
                              snapshot_type=None, filters=None,
                              max_records=None, marker=None):
        """
        Returns information about DB snapshots. This API supports
        pagination.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        A DB instance identifier to retrieve the list of DB snapshots for.
            Cannot be used in conjunction with `DBSnapshotIdentifier`. This
            parameter is not case sensitive.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type db_snapshot_identifier: string
        :param db_snapshot_identifier:
        A specific DB snapshot identifier to describe. Cannot be used in
            conjunction with `DBInstanceIdentifier`. This value is stored as a
            lowercase string.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens
        + If this is the identifier of an automated snapshot, the
              `SnapshotType` parameter must also be specified.

        :type snapshot_type: string
        :param snapshot_type: The type of snapshots that will be returned.
            Values can be "automated" or "manual." If not specified, the
            returned results will include all snapshots types.

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            `DescribeDBSnapshots` request. If this parameter is specified, the
            response includes only records beyond the marker, up to the value
            specified by `MaxRecords`.

        """
        params = {}
        if db_instance_identifier is not None:
            params['DBInstanceIdentifier'] = db_instance_identifier
        if db_snapshot_identifier is not None:
            params['DBSnapshotIdentifier'] = db_snapshot_identifier
        if snapshot_type is not None:
            params['SnapshotType'] = snapshot_type
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBSnapshots',
            verb='POST',
            path='/', params=params)

    def describe_db_subnet_groups(self, db_subnet_group_name=None,
                                  filters=None, max_records=None,
                                  marker=None):
        """
        Returns a list of DBSubnetGroup descriptions. If a
        DBSubnetGroupName is specified, the list will contain only the
        descriptions of the specified DBSubnetGroup.

        For an overview of CIDR ranges, go to the `Wikipedia
        Tutorial`_.

        :type db_subnet_group_name: string
        :param db_subnet_group_name: The name of the DB subnet group to return
            details for.

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeDBSubnetGroups request. If this parameter is specified, the
            response includes only records beyond the marker, up to the value
            specified by `MaxRecords`.

        """
        params = {}
        if db_subnet_group_name is not None:
            params['DBSubnetGroupName'] = db_subnet_group_name
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeDBSubnetGroups',
            verb='POST',
            path='/', params=params)

    def describe_engine_default_parameters(self, db_parameter_group_family,
                                           max_records=None, marker=None):
        """
        Returns the default engine and system parameter information
        for the specified database engine.

        :type db_parameter_group_family: string
        :param db_parameter_group_family: The name of the DB parameter group
            family.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            `DescribeEngineDefaultParameters` request. If this parameter is
            specified, the response includes only records beyond the marker, up
            to the value specified by `MaxRecords`.

        """
        params = {
            'DBParameterGroupFamily': db_parameter_group_family,
        }
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeEngineDefaultParameters',
            verb='POST',
            path='/', params=params)

    def describe_event_categories(self, source_type=None):
        """
        Displays a list of categories for all event source types, or,
        if specified, for a specified source type. You can see a list
        of the event categories and source types in the ` Events`_
        topic in the Amazon RDS User Guide.

        :type source_type: string
        :param source_type: The type of source that will be generating the
            events.
        Valid values: db-instance | db-parameter-group | db-security-group |
            db-snapshot

        """
        params = {}
        if source_type is not None:
            params['SourceType'] = source_type
        return self._make_request(
            action='DescribeEventCategories',
            verb='POST',
            path='/', params=params)

    def describe_event_subscriptions(self, subscription_name=None,
                                     filters=None, max_records=None,
                                     marker=None):
        """
        Lists all the subscription descriptions for a customer
        account. The description for a subscription includes
        SubscriptionName, SNSTopicARN, CustomerID, SourceType,
        SourceID, CreationTime, and Status.

        If you specify a SubscriptionName, lists the description for
        that subscription.

        :type subscription_name: string
        :param subscription_name: The name of the RDS event notification
            subscription you want to describe.

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeOrderableDBInstanceOptions request. If this parameter is
            specified, the response includes only records beyond the marker, up
            to the value specified by `MaxRecords` .

        """
        params = {}
        if subscription_name is not None:
            params['SubscriptionName'] = subscription_name
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
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
                        event_categories=None, max_records=None, marker=None):
        """
        Returns events related to DB instances, DB security groups, DB
        snapshots, and DB parameter groups for the past 14 days.
        Events specific to a particular DB instance, DB security
        group, database snapshot, or DB parameter group can be
        obtained by providing the name as a parameter. By default, the
        past hour of events are returned.

        :type source_identifier: string
        :param source_identifier:
        The identifier of the event source for which events will be returned.
            If not specified, then all sources are included in the response.

        Constraints:


        + If SourceIdentifier is supplied, SourceType must also be provided.
        + If the source type is `DBInstance`, then a `DBInstanceIdentifier`
              must be supplied.
        + If the source type is `DBSecurityGroup`, a `DBSecurityGroupName` must
              be supplied.
        + If the source type is `DBParameterGroup`, a `DBParameterGroupName`
              must be supplied.
        + If the source type is `DBSnapshot`, a `DBSnapshotIdentifier` must be
              supplied.
        + Cannot end with a hyphen or contain two consecutive hyphens.

        :type source_type: string
        :param source_type: The event source to retrieve events for. If no
            value is specified, all events are returned.

        :type start_time: timestamp
        :param start_time: The beginning of the time interval to retrieve
            events for, specified in ISO 8601 format. For more information
            about ISO 8601, go to the `ISO8601 Wikipedia page.`_
        Example: 2009-07-08T18:00Z

        :type end_time: timestamp
        :param end_time: The end of the time interval for which to retrieve
            events, specified in ISO 8601 format. For more information about
            ISO 8601, go to the `ISO8601 Wikipedia page.`_
        Example: 2009-07-08T18:00Z

        :type duration: integer
        :param duration: The number of minutes to retrieve events for.
        Default: 60

        :type event_categories: list
        :param event_categories: A list of event categories that trigger
            notifications for a event notification subscription.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results may be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeEvents request. If this parameter is specified, the
            response includes only records beyond the marker, up to the value
            specified by `MaxRecords`.

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
        if event_categories is not None:
            self.build_list_params(params,
                                   event_categories,
                                   'EventCategories.member')
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeEvents',
            verb='POST',
            path='/', params=params)

    def describe_option_group_options(self, engine_name,
                                      major_engine_version=None,
                                      max_records=None, marker=None):
        """
        Describes all available options.

        :type engine_name: string
        :param engine_name: A required parameter. Options available for the
            given Engine name will be described.

        :type major_engine_version: string
        :param major_engine_version: If specified, filters the results to
            include only options for the specified major engine version.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            request. If this parameter is specified, the response includes only
            records beyond the marker, up to the value specified by
            `MaxRecords`.

        """
        params = {'EngineName': engine_name, }
        if major_engine_version is not None:
            params['MajorEngineVersion'] = major_engine_version
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeOptionGroupOptions',
            verb='POST',
            path='/', params=params)

    def describe_option_groups(self, option_group_name=None, filters=None,
                               marker=None, max_records=None,
                               engine_name=None, major_engine_version=None):
        """
        Describes the available option groups.

        :type option_group_name: string
        :param option_group_name: The name of the option group to describe.
            Cannot be supplied together with EngineName or MajorEngineVersion.

        :type filters: list
        :param filters:

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeOptionGroups request. If this parameter is specified, the
            response includes only records beyond the marker, up to the value
            specified by `MaxRecords`.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type engine_name: string
        :param engine_name: Filters the list of option groups to only include
            groups associated with a specific database engine.

        :type major_engine_version: string
        :param major_engine_version: Filters the list of option groups to only
            include groups associated with a specific database engine version.
            If specified, then EngineName must also be specified.

        """
        params = {}
        if option_group_name is not None:
            params['OptionGroupName'] = option_group_name
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if marker is not None:
            params['Marker'] = marker
        if max_records is not None:
            params['MaxRecords'] = max_records
        if engine_name is not None:
            params['EngineName'] = engine_name
        if major_engine_version is not None:
            params['MajorEngineVersion'] = major_engine_version
        return self._make_request(
            action='DescribeOptionGroups',
            verb='POST',
            path='/', params=params)

    def describe_orderable_db_instance_options(self, engine,
                                               engine_version=None,
                                               db_instance_class=None,
                                               license_model=None, vpc=None,
                                               max_records=None, marker=None):
        """
        Returns a list of orderable DB instance options for the
        specified engine.

        :type engine: string
        :param engine: The name of the engine to retrieve DB instance options
            for.

        :type engine_version: string
        :param engine_version: The engine version filter value. Specify this
            parameter to show only the available offerings matching the
            specified engine version.

        :type db_instance_class: string
        :param db_instance_class: The DB instance class filter value. Specify
            this parameter to show only the available offerings matching the
            specified DB instance class.

        :type license_model: string
        :param license_model: The license model filter value. Specify this
            parameter to show only the available offerings matching the
            specified license model.

        :type vpc: boolean
        :param vpc: The VPC filter value. Specify this parameter to show only
            the available VPC or non-VPC offerings.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more records exist than the specified `MaxRecords`
            value, a pagination token called a marker is included in the
            response so that the remaining results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            DescribeOrderableDBInstanceOptions request. If this parameter is
            specified, the response includes only records beyond the marker, up
            to the value specified by `MaxRecords` .

        """
        params = {'Engine': engine, }
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if license_model is not None:
            params['LicenseModel'] = license_model
        if vpc is not None:
            params['Vpc'] = str(
                vpc).lower()
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeOrderableDBInstanceOptions',
            verb='POST',
            path='/', params=params)

    def describe_reserved_db_instances(self, reserved_db_instance_id=None,
                                       reserved_db_instances_offering_id=None,
                                       db_instance_class=None, duration=None,
                                       product_description=None,
                                       offering_type=None, multi_az=None,
                                       filters=None, max_records=None,
                                       marker=None):
        """
        Returns information about reserved DB instances for this
        account, or about a specified reserved DB instance.

        :type reserved_db_instance_id: string
        :param reserved_db_instance_id: The reserved DB instance identifier
            filter value. Specify this parameter to show only the reservation
            that matches the specified reservation ID.

        :type reserved_db_instances_offering_id: string
        :param reserved_db_instances_offering_id: The offering identifier
            filter value. Specify this parameter to show only purchased
            reservations matching the specified offering identifier.

        :type db_instance_class: string
        :param db_instance_class: The DB instance class filter value. Specify
            this parameter to show only those reservations matching the
            specified DB instances class.

        :type duration: string
        :param duration: The duration filter value, specified in years or
            seconds. Specify this parameter to show only reservations for this
            duration.
        Valid Values: `1 | 3 | 31536000 | 94608000`

        :type product_description: string
        :param product_description: The product description filter value.
            Specify this parameter to show only those reservations matching the
            specified product description.

        :type offering_type: string
        :param offering_type: The offering type filter value. Specify this
            parameter to show only the available offerings matching the
            specified offering type.
        Valid Values: `"Light Utilization" | "Medium Utilization" | "Heavy
            Utilization" `

        :type multi_az: boolean
        :param multi_az: The Multi-AZ filter value. Specify this parameter to
            show only those reservations matching the specified Multi-AZ
            parameter.

        :type filters: list
        :param filters:

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more than the `MaxRecords` value is available, a
            pagination token called a marker is included in the response so
            that the following results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            request. If this parameter is specified, the response includes only
            records beyond the marker, up to the value specified by
            `MaxRecords`.

        """
        params = {}
        if reserved_db_instance_id is not None:
            params['ReservedDBInstanceId'] = reserved_db_instance_id
        if reserved_db_instances_offering_id is not None:
            params['ReservedDBInstancesOfferingId'] = reserved_db_instances_offering_id
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if duration is not None:
            params['Duration'] = duration
        if product_description is not None:
            params['ProductDescription'] = product_description
        if offering_type is not None:
            params['OfferingType'] = offering_type
        if multi_az is not None:
            params['MultiAZ'] = str(
                multi_az).lower()
        if filters is not None:
            self.build_complex_list_params(
                params, filters,
                'Filters.member',
                ('FilterName', 'FilterValue'))
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReservedDBInstances',
            verb='POST',
            path='/', params=params)

    def describe_reserved_db_instances_offerings(self,
                                                 reserved_db_instances_offering_id=None,
                                                 db_instance_class=None,
                                                 duration=None,
                                                 product_description=None,
                                                 offering_type=None,
                                                 multi_az=None,
                                                 max_records=None,
                                                 marker=None):
        """
        Lists available reserved DB instance offerings.

        :type reserved_db_instances_offering_id: string
        :param reserved_db_instances_offering_id: The offering identifier
            filter value. Specify this parameter to show only the available
            offering that matches the specified reservation identifier.
        Example: `438012d3-4052-4cc7-b2e3-8d3372e0e706`

        :type db_instance_class: string
        :param db_instance_class: The DB instance class filter value. Specify
            this parameter to show only the available offerings matching the
            specified DB instance class.

        :type duration: string
        :param duration: Duration filter value, specified in years or seconds.
            Specify this parameter to show only reservations for this duration.
        Valid Values: `1 | 3 | 31536000 | 94608000`

        :type product_description: string
        :param product_description: Product description filter value. Specify
            this parameter to show only the available offerings matching the
            specified product description.

        :type offering_type: string
        :param offering_type: The offering type filter value. Specify this
            parameter to show only the available offerings matching the
            specified offering type.
        Valid Values: `"Light Utilization" | "Medium Utilization" | "Heavy
            Utilization" `

        :type multi_az: boolean
        :param multi_az: The Multi-AZ filter value. Specify this parameter to
            show only the available offerings matching the specified Multi-AZ
            parameter.

        :type max_records: integer
        :param max_records: The maximum number of records to include in the
            response. If more than the `MaxRecords` value is available, a
            pagination token called a marker is included in the response so
            that the following results can be retrieved.
        Default: 100

        Constraints: minimum 20, maximum 100

        :type marker: string
        :param marker: An optional pagination token provided by a previous
            request. If this parameter is specified, the response includes only
            records beyond the marker, up to the value specified by
            `MaxRecords`.

        """
        params = {}
        if reserved_db_instances_offering_id is not None:
            params['ReservedDBInstancesOfferingId'] = reserved_db_instances_offering_id
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if duration is not None:
            params['Duration'] = duration
        if product_description is not None:
            params['ProductDescription'] = product_description
        if offering_type is not None:
            params['OfferingType'] = offering_type
        if multi_az is not None:
            params['MultiAZ'] = str(
                multi_az).lower()
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker
        return self._make_request(
            action='DescribeReservedDBInstancesOfferings',
            verb='POST',
            path='/', params=params)

    def download_db_log_file_portion(self, db_instance_identifier,
                                     log_file_name, marker=None,
                                     number_of_lines=None):
        """
        Downloads the last line of the specified log file.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The customer-assigned name of the DB instance that contains the log
            files you want to list.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type log_file_name: string
        :param log_file_name: The name of the log file to be downloaded.

        :type marker: string
        :param marker: The pagination token provided in the previous request.
            If this parameter is specified the response includes only records
            beyond the marker, up to MaxRecords.

        :type number_of_lines: integer
        :param number_of_lines: The number of lines remaining to be downloaded.

        """
        params = {
            'DBInstanceIdentifier': db_instance_identifier,
            'LogFileName': log_file_name,
        }
        if marker is not None:
            params['Marker'] = marker
        if number_of_lines is not None:
            params['NumberOfLines'] = number_of_lines
        return self._make_request(
            action='DownloadDBLogFilePortion',
            verb='POST',
            path='/', params=params)

    def list_tags_for_resource(self, resource_name):
        """
        Lists all tags on an Amazon RDS resource.

        For an overview on tagging an Amazon RDS resource, see
        `Tagging Amazon RDS Resources`_.

        :type resource_name: string
        :param resource_name: The Amazon RDS resource with tags to be listed.
            This value is an Amazon Resource Name (ARN). For information about
            creating an ARN, see ` Constructing an RDS Amazon Resource Name
            (ARN)`_.

        """
        params = {'ResourceName': resource_name, }
        return self._make_request(
            action='ListTagsForResource',
            verb='POST',
            path='/', params=params)

    def modify_db_instance(self, db_instance_identifier,
                           allocated_storage=None, db_instance_class=None,
                           db_security_groups=None,
                           vpc_security_group_ids=None,
                           apply_immediately=None, master_user_password=None,
                           db_parameter_group_name=None,
                           backup_retention_period=None,
                           preferred_backup_window=None,
                           preferred_maintenance_window=None, multi_az=None,
                           engine_version=None,
                           allow_major_version_upgrade=None,
                           auto_minor_version_upgrade=None, iops=None,
                           option_group_name=None,
                           new_db_instance_identifier=None):
        """
        Modify settings for a DB instance. You can change one or more
        database configuration parameters by specifying these
        parameters and the new values in the request.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The DB instance identifier. This value is stored as a lowercase string.

        Constraints:


        + Must be the identifier for an existing DB instance
        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type allocated_storage: integer
        :param allocated_storage: The new storage capacity of the RDS instance.
            Changing this parameter does not result in an outage and the change
            is applied during the next maintenance window unless the
            `ApplyImmediately` parameter is set to `True` for this request.
        **MySQL**

        Default: Uses existing setting

        Valid Values: 5-1024

        Constraints: Value supplied must be at least 10% greater than the
            current value. Values that are not at least 10% greater than the
            existing value are rounded up so that they are 10% greater than the
            current value.

        Type: Integer

        **Oracle**

        Default: Uses existing setting

        Valid Values: 10-1024

        Constraints: Value supplied must be at least 10% greater than the
            current value. Values that are not at least 10% greater than the
            existing value are rounded up so that they are 10% greater than the
            current value.

        **SQL Server**

        Cannot be modified.

        If you choose to migrate your DB instance from using standard storage
            to using Provisioned IOPS, or from using Provisioned IOPS to using
            standard storage, the process can take time. The duration of the
            migration depends on several factors such as database load, storage
            size, storage type (standard or Provisioned IOPS), amount of IOPS
            provisioned (if any), and the number of prior scale storage
            operations. Typical migration times are under 24 hours, but the
            process can take up to several days in some cases. During the
            migration, the DB instance will be available for use, but may
            experience performance degradation. While the migration takes
            place, nightly backups for the instance will be suspended. No other
            Amazon RDS operations can take place for the instance, including
            modifying the instance, rebooting the instance, deleting the
            instance, creating a read replica for the instance, and creating a
            DB snapshot of the instance.

        :type db_instance_class: string
        :param db_instance_class: The new compute and memory capacity of the DB
            instance. To determine the instance classes that are available for
            a particular DB engine, use the DescribeOrderableDBInstanceOptions
            action.
        Passing a value for this parameter causes an outage during the change
            and is applied during the next maintenance window, unless the
            `ApplyImmediately` parameter is specified as `True` for this
            request.

        Default: Uses existing setting

        Valid Values: `db.t1.micro | db.m1.small | db.m1.medium | db.m1.large |
            db.m1.xlarge | db.m2.xlarge | db.m2.2xlarge | db.m2.4xlarge`

        :type db_security_groups: list
        :param db_security_groups:
        A list of DB security groups to authorize on this DB instance. Changing
            this parameter does not result in an outage and the change is
            asynchronously applied as soon as possible.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type vpc_security_group_ids: list
        :param vpc_security_group_ids:
        A list of EC2 VPC security groups to authorize on this DB instance.
            This change is asynchronously applied as soon as possible.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type apply_immediately: boolean
        :param apply_immediately: Specifies whether or not the modifications in
            this request and any pending modifications are asynchronously
            applied as soon as possible, regardless of the
            `PreferredMaintenanceWindow` setting for the DB instance.
        If this parameter is passed as `False`, changes to the DB instance are
            applied on the next call to RebootDBInstance, the next maintenance
            reboot, or the next failure reboot, whichever occurs first. See
            each parameter to determine when a change is applied.

        Default: `False`

        :type master_user_password: string
        :param master_user_password:
        The new password for the DB instance master user. Can be any printable
            ASCII character except "/", '"', or "@".

        Changing this parameter does not result in an outage and the change is
            asynchronously applied as soon as possible. Between the time of the
            request and the completion of the request, the `MasterUserPassword`
            element exists in the `PendingModifiedValues` element of the
            operation response.

        Default: Uses existing setting

        Constraints: Must be 8 to 41 alphanumeric characters (MySQL), 8 to 30
            alphanumeric characters (Oracle), or 8 to 128 alphanumeric
            characters (SQL Server).

        Amazon RDS API actions never return the password, so this action
            provides a way to regain access to a master instance user if the
            password is lost.

        :type db_parameter_group_name: string
        :param db_parameter_group_name: The name of the DB parameter group to
            apply to this DB instance. Changing this parameter does not result
            in an outage and the change is applied during the next maintenance
            window unless the `ApplyImmediately` parameter is set to `True` for
            this request.
        Default: Uses existing setting

        Constraints: The DB parameter group must be in the same DB parameter
            group family as this DB instance.

        :type backup_retention_period: integer
        :param backup_retention_period:
        The number of days to retain automated backups. Setting this parameter
            to a positive number enables backups. Setting this parameter to 0
            disables automated backups.

        Changing this parameter can result in an outage if you change from 0 to
            a non-zero value or from a non-zero value to 0. These changes are
            applied during the next maintenance window unless the
            `ApplyImmediately` parameter is set to `True` for this request. If
            you change the parameter from one non-zero value to another non-
            zero value, the change is asynchronously applied as soon as
            possible.

        Default: Uses existing setting

        Constraints:


        + Must be a value from 0 to 8
        + Cannot be set to 0 if the DB instance is a master instance with read
              replicas or if the DB instance is a read replica

        :type preferred_backup_window: string
        :param preferred_backup_window:
        The daily time range during which automated backups are created if
            automated backups are enabled, as determined by the
            `BackupRetentionPeriod`. Changing this parameter does not result in
            an outage and the change is asynchronously applied as soon as
            possible.

        Constraints:


        + Must be in the format hh24:mi-hh24:mi
        + Times should be Universal Time Coordinated (UTC)
        + Must not conflict with the preferred maintenance window
        + Must be at least 30 minutes

        :type preferred_maintenance_window: string
        :param preferred_maintenance_window: The weekly time range (in UTC)
            during which system maintenance can occur, which may result in an
            outage. Changing this parameter does not result in an outage,
            except in the following situation, and the change is asynchronously
            applied as soon as possible. If there are pending actions that
            cause a reboot, and the maintenance window is changed to include
            the current time, then changing this parameter will cause a reboot
            of the DB instance. If moving this window to the current time,
            there must be at least 30 minutes between the current time and end
            of the window to ensure pending changes are applied.
        Default: Uses existing setting

        Format: ddd:hh24:mi-ddd:hh24:mi

        Valid Days: Mon | Tue | Wed | Thu | Fri | Sat | Sun

        Constraints: Must be at least 30 minutes

        :type multi_az: boolean
        :param multi_az: Specifies if the DB instance is a Multi-AZ deployment.
            Changing this parameter does not result in an outage and the change
            is applied during the next maintenance window unless the
            `ApplyImmediately` parameter is set to `True` for this request.
        Constraints: Cannot be specified if the DB instance is a read replica.

        :type engine_version: string
        :param engine_version: The version number of the database engine to
            upgrade to. Changing this parameter results in an outage and the
            change is applied during the next maintenance window unless the
            `ApplyImmediately` parameter is set to `True` for this request.
        For major version upgrades, if a non-default DB parameter group is
            currently in use, a new DB parameter group in the DB parameter
            group family for the new engine version must be specified. The new
            DB parameter group can be the default for that DB parameter group
            family.

        Example: `5.1.42`

        :type allow_major_version_upgrade: boolean
        :param allow_major_version_upgrade: Indicates that major version
            upgrades are allowed. Changing this parameter does not result in an
            outage and the change is asynchronously applied as soon as
            possible.
        Constraints: This parameter must be set to true when specifying a value
            for the EngineVersion parameter that is a different major version
            than the DB instance's current version.

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Indicates that minor version
            upgrades will be applied automatically to the DB instance during
            the maintenance window. Changing this parameter does not result in
            an outage except in the following case and the change is
            asynchronously applied as soon as possible. An outage will result
            if this parameter is set to `True` during the maintenance window,
            and a newer minor version is available, and RDS has enabled auto
            patching for that engine version.

        :type iops: integer
        :param iops: The new Provisioned IOPS (I/O operations per second) value
            for the RDS instance. Changing this parameter does not result in an
            outage and the change is applied during the next maintenance window
            unless the `ApplyImmediately` parameter is set to `True` for this
            request.
        Default: Uses existing setting

        Constraints: Value supplied must be at least 10% greater than the
            current value. Values that are not at least 10% greater than the
            existing value are rounded up so that they are 10% greater than the
            current value.

        Type: Integer

        If you choose to migrate your DB instance from using standard storage
            to using Provisioned IOPS, or from using Provisioned IOPS to using
            standard storage, the process can take time. The duration of the
            migration depends on several factors such as database load, storage
            size, storage type (standard or Provisioned IOPS), amount of IOPS
            provisioned (if any), and the number of prior scale storage
            operations. Typical migration times are under 24 hours, but the
            process can take up to several days in some cases. During the
            migration, the DB instance will be available for use, but may
            experience performance degradation. While the migration takes
            place, nightly backups for the instance will be suspended. No other
            Amazon RDS operations can take place for the instance, including
            modifying the instance, rebooting the instance, deleting the
            instance, creating a read replica for the instance, and creating a
            DB snapshot of the instance.

        :type option_group_name: string
        :param option_group_name: Indicates that the DB instance should be
            associated with the specified option group. Changing this parameter
            does not result in an outage except in the following case and the
            change is applied during the next maintenance window unless the
            `ApplyImmediately` parameter is set to `True` for this request. If
            the parameter change results in an option group that enables OEM,
            this change can cause a brief (sub-second) period during which new
            connections are rejected but existing connections are not
            interrupted.
        Permanent options, such as the TDE option for Oracle Advanced Security
            TDE, cannot be removed from an option group, and that option group
            cannot be removed from a DB instance once it is associated with a
            DB instance

        :type new_db_instance_identifier: string
        :param new_db_instance_identifier:
        The new DB instance identifier for the DB instance when renaming a DB
            Instance. This value is stored as a lowercase string.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        """
        params = {'DBInstanceIdentifier': db_instance_identifier, }
        if allocated_storage is not None:
            params['AllocatedStorage'] = allocated_storage
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if db_security_groups is not None:
            self.build_list_params(params,
                                   db_security_groups,
                                   'DBSecurityGroups.member')
        if vpc_security_group_ids is not None:
            self.build_list_params(params,
                                   vpc_security_group_ids,
                                   'VpcSecurityGroupIds.member')
        if apply_immediately is not None:
            params['ApplyImmediately'] = str(
                apply_immediately).lower()
        if master_user_password is not None:
            params['MasterUserPassword'] = master_user_password
        if db_parameter_group_name is not None:
            params['DBParameterGroupName'] = db_parameter_group_name
        if backup_retention_period is not None:
            params['BackupRetentionPeriod'] = backup_retention_period
        if preferred_backup_window is not None:
            params['PreferredBackupWindow'] = preferred_backup_window
        if preferred_maintenance_window is not None:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if multi_az is not None:
            params['MultiAZ'] = str(
                multi_az).lower()
        if engine_version is not None:
            params['EngineVersion'] = engine_version
        if allow_major_version_upgrade is not None:
            params['AllowMajorVersionUpgrade'] = str(
                allow_major_version_upgrade).lower()
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        if iops is not None:
            params['Iops'] = iops
        if option_group_name is not None:
            params['OptionGroupName'] = option_group_name
        if new_db_instance_identifier is not None:
            params['NewDBInstanceIdentifier'] = new_db_instance_identifier
        return self._make_request(
            action='ModifyDBInstance',
            verb='POST',
            path='/', params=params)

    def modify_db_parameter_group(self, db_parameter_group_name, parameters):
        """
        Modifies the parameters of a DB parameter group. To modify
        more than one parameter, submit a list of the following:
        `ParameterName`, `ParameterValue`, and `ApplyMethod`. A
        maximum of 20 parameters can be modified in a single request.

        The `apply-immediate` method can be used only for dynamic
        parameters; the `pending-reboot` method can be used with MySQL
        and Oracle DB instances for either dynamic or static
        parameters. For Microsoft SQL Server DB instances, the
        `pending-reboot` method can be used only for static
        parameters.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of the DB parameter group.

        Constraints:


        + Must be the name of an existing DB parameter group
        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type parameters: list
        :param parameters:
        An array of parameter names, values, and the apply method for the
            parameter update. At least one parameter name, value, and apply
            method must be supplied; subsequent arguments are optional. A
            maximum of 20 parameters may be modified in a single request.

        Valid Values (for the application method): `immediate | pending-reboot`

        You can use the immediate value with dynamic parameters only. You can
            use the pending-reboot value for both dynamic and static
            parameters, and changes are applied when DB instance reboots.

        """
        params = {'DBParameterGroupName': db_parameter_group_name, }
        self.build_complex_list_params(
            params, parameters,
            'Parameters.member',
            ('ParameterName', 'ParameterValue', 'Description', 'Source', 'ApplyType', 'DataType', 'AllowedValues', 'IsModifiable', 'MinimumEngineVersion', 'ApplyMethod'))
        return self._make_request(
            action='ModifyDBParameterGroup',
            verb='POST',
            path='/', params=params)

    def modify_db_subnet_group(self, db_subnet_group_name, subnet_ids,
                               db_subnet_group_description=None):
        """
        Modifies an existing DB subnet group. DB subnet groups must
        contain at least one subnet in at least two AZs in the region.

        :type db_subnet_group_name: string
        :param db_subnet_group_name: The name for the DB subnet group. This
            value is stored as a lowercase string.
        Constraints: Must contain no more than 255 alphanumeric characters or
            hyphens. Must not be "Default".

        Example: `mySubnetgroup`

        :type db_subnet_group_description: string
        :param db_subnet_group_description: The description for the DB subnet
            group.

        :type subnet_ids: list
        :param subnet_ids: The EC2 subnet IDs for the DB subnet group.

        """
        params = {'DBSubnetGroupName': db_subnet_group_name, }
        self.build_list_params(params,
                               subnet_ids,
                               'SubnetIds.member')
        if db_subnet_group_description is not None:
            params['DBSubnetGroupDescription'] = db_subnet_group_description
        return self._make_request(
            action='ModifyDBSubnetGroup',
            verb='POST',
            path='/', params=params)

    def modify_event_subscription(self, subscription_name,
                                  sns_topic_arn=None, source_type=None,
                                  event_categories=None, enabled=None):
        """
        Modifies an existing RDS event notification subscription. Note
        that you cannot modify the source identifiers using this call;
        to change source identifiers for a subscription, use the
        AddSourceIdentifierToSubscription and
        RemoveSourceIdentifierFromSubscription calls.

        You can see a list of the event categories for a given
        SourceType in the `Events`_ topic in the Amazon RDS User Guide
        or by using the **DescribeEventCategories** action.

        :type subscription_name: string
        :param subscription_name: The name of the RDS event notification
            subscription.

        :type sns_topic_arn: string
        :param sns_topic_arn: The Amazon Resource Name (ARN) of the SNS topic
            created for event notification. The ARN is created by Amazon SNS
            when you create a topic and subscribe to it.

        :type source_type: string
        :param source_type: The type of source that will be generating the
            events. For example, if you want to be notified of events generated
            by a DB instance, you would set this parameter to db-instance. if
            this value is not specified, all events are returned.
        Valid values: db-instance | db-parameter-group | db-security-group |
            db-snapshot

        :type event_categories: list
        :param event_categories: A list of event categories for a SourceType
            that you want to subscribe to. You can see a list of the categories
            for a given SourceType in the `Events`_ topic in the Amazon RDS
            User Guide or by using the **DescribeEventCategories** action.

        :type enabled: boolean
        :param enabled: A Boolean value; set to **true** to activate the
            subscription.

        """
        params = {'SubscriptionName': subscription_name, }
        if sns_topic_arn is not None:
            params['SnsTopicArn'] = sns_topic_arn
        if source_type is not None:
            params['SourceType'] = source_type
        if event_categories is not None:
            self.build_list_params(params,
                                   event_categories,
                                   'EventCategories.member')
        if enabled is not None:
            params['Enabled'] = str(
                enabled).lower()
        return self._make_request(
            action='ModifyEventSubscription',
            verb='POST',
            path='/', params=params)

    def modify_option_group(self, option_group_name, options_to_include=None,
                            options_to_remove=None, apply_immediately=None):
        """
        Modifies an existing option group.

        :type option_group_name: string
        :param option_group_name: The name of the option group to be modified.
        Permanent options, such as the TDE option for Oracle Advanced Security
            TDE, cannot be removed from an option group, and that option group
            cannot be removed from a DB instance once it is associated with a
            DB instance

        :type options_to_include: list
        :param options_to_include: Options in this list are added to the option
            group or, if already present, the specified configuration is used
            to update the existing configuration.

        :type options_to_remove: list
        :param options_to_remove: Options in this list are removed from the
            option group.

        :type apply_immediately: boolean
        :param apply_immediately: Indicates whether the changes should be
            applied immediately, or during the next maintenance window for each
            instance associated with the option group.

        """
        params = {'OptionGroupName': option_group_name, }
        if options_to_include is not None:
            self.build_complex_list_params(
                params, options_to_include,
                'OptionsToInclude.member',
                ('OptionName', 'Port', 'DBSecurityGroupMemberships', 'VpcSecurityGroupMemberships', 'OptionSettings'))
        if options_to_remove is not None:
            self.build_list_params(params,
                                   options_to_remove,
                                   'OptionsToRemove.member')
        if apply_immediately is not None:
            params['ApplyImmediately'] = str(
                apply_immediately).lower()
        return self._make_request(
            action='ModifyOptionGroup',
            verb='POST',
            path='/', params=params)

    def promote_read_replica(self, db_instance_identifier,
                             backup_retention_period=None,
                             preferred_backup_window=None):
        """
        Promotes a read replica DB instance to a standalone DB
        instance.

        :type db_instance_identifier: string
        :param db_instance_identifier: The DB instance identifier. This value
            is stored as a lowercase string.
        Constraints:


        + Must be the identifier for an existing read replica DB instance
        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        Example: mydbinstance

        :type backup_retention_period: integer
        :param backup_retention_period:
        The number of days to retain automated backups. Setting this parameter
            to a positive number enables backups. Setting this parameter to 0
            disables automated backups.

        Default: 1

        Constraints:


        + Must be a value from 0 to 8

        :type preferred_backup_window: string
        :param preferred_backup_window: The daily time range during which
            automated backups are created if automated backups are enabled,
            using the `BackupRetentionPeriod` parameter.
        Default: A 30-minute window selected at random from an 8-hour block of
            time per region. See the Amazon RDS User Guide for the time blocks
            for each region from which the default backup windows are assigned.

        Constraints: Must be in the format `hh24:mi-hh24:mi`. Times should be
            Universal Time Coordinated (UTC). Must not conflict with the
            preferred maintenance window. Must be at least 30 minutes.

        """
        params = {'DBInstanceIdentifier': db_instance_identifier, }
        if backup_retention_period is not None:
            params['BackupRetentionPeriod'] = backup_retention_period
        if preferred_backup_window is not None:
            params['PreferredBackupWindow'] = preferred_backup_window
        return self._make_request(
            action='PromoteReadReplica',
            verb='POST',
            path='/', params=params)

    def purchase_reserved_db_instances_offering(self,
                                                reserved_db_instances_offering_id,
                                                reserved_db_instance_id=None,
                                                db_instance_count=None,
                                                tags=None):
        """
        Purchases a reserved DB instance offering.

        :type reserved_db_instances_offering_id: string
        :param reserved_db_instances_offering_id: The ID of the Reserved DB
            instance offering to purchase.
        Example: 438012d3-4052-4cc7-b2e3-8d3372e0e706

        :type reserved_db_instance_id: string
        :param reserved_db_instance_id: Customer-specified identifier to track
            this reservation.
        Example: myreservationID

        :type db_instance_count: integer
        :param db_instance_count: The number of instances to reserve.
        Default: `1`

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'ReservedDBInstancesOfferingId': reserved_db_instances_offering_id,
        }
        if reserved_db_instance_id is not None:
            params['ReservedDBInstanceId'] = reserved_db_instance_id
        if db_instance_count is not None:
            params['DBInstanceCount'] = db_instance_count
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='PurchaseReservedDBInstancesOffering',
            verb='POST',
            path='/', params=params)

    def reboot_db_instance(self, db_instance_identifier, force_failover=None):
        """
        Rebooting a DB instance restarts the database engine service.
        A reboot also applies to the DB instance any modifications to
        the associated DB parameter group that were pending. Rebooting
        a DB instance results in a momentary outage of the instance,
        during which the DB instance status is set to rebooting. If
        the RDS instance is configured for MultiAZ, it is possible
        that the reboot will be conducted through a failover. An
        Amazon RDS event is created when the reboot is completed.

        If your DB instance is deployed in multiple Availability
        Zones, you can force a failover from one AZ to the other
        during the reboot. You might force a failover to test the
        availability of your DB instance deployment or to restore
        operations to the original AZ after a failover occurs.

        The time required to reboot is a function of the specific
        database engine's crash recovery process. To improve the
        reboot time, we recommend that you reduce database activities
        as much as possible during the reboot process to reduce
        rollback activity for in-transit transactions.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The DB instance identifier. This parameter is stored as a lowercase
            string.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type force_failover: boolean
        :param force_failover: When `True`, the reboot will be conducted
            through a MultiAZ failover.
        Constraint: You cannot specify `True` if the instance is not configured
            for MultiAZ.

        """
        params = {'DBInstanceIdentifier': db_instance_identifier, }
        if force_failover is not None:
            params['ForceFailover'] = str(
                force_failover).lower()
        return self._make_request(
            action='RebootDBInstance',
            verb='POST',
            path='/', params=params)

    def remove_source_identifier_from_subscription(self, subscription_name,
                                                   source_identifier):
        """
        Removes a source identifier from an existing RDS event
        notification subscription.

        :type subscription_name: string
        :param subscription_name: The name of the RDS event notification
            subscription you want to remove a source identifier from.

        :type source_identifier: string
        :param source_identifier: The source identifier to be removed from the
            subscription, such as the **DB instance identifier** for a DB
            instance or the name of a security group.

        """
        params = {
            'SubscriptionName': subscription_name,
            'SourceIdentifier': source_identifier,
        }
        return self._make_request(
            action='RemoveSourceIdentifierFromSubscription',
            verb='POST',
            path='/', params=params)

    def remove_tags_from_resource(self, resource_name, tag_keys):
        """
        Removes metadata tags from an Amazon RDS resource.

        For an overview on tagging an Amazon RDS resource, see
        `Tagging Amazon RDS Resources`_.

        :type resource_name: string
        :param resource_name: The Amazon RDS resource the tags will be removed
            from. This value is an Amazon Resource Name (ARN). For information
            about creating an ARN, see ` Constructing an RDS Amazon Resource
            Name (ARN)`_.

        :type tag_keys: list
        :param tag_keys: The tag key (name) of the tag to be removed.

        """
        params = {'ResourceName': resource_name, }
        self.build_list_params(params,
                               tag_keys,
                               'TagKeys.member')
        return self._make_request(
            action='RemoveTagsFromResource',
            verb='POST',
            path='/', params=params)

    def reset_db_parameter_group(self, db_parameter_group_name,
                                 reset_all_parameters=None, parameters=None):
        """
        Modifies the parameters of a DB parameter group to the
        engine/system default value. To reset specific parameters
        submit a list of the following: `ParameterName` and
        `ApplyMethod`. To reset the entire DB parameter group, specify
        the `DBParameterGroup` name and `ResetAllParameters`
        parameters. When resetting the entire group, dynamic
        parameters are updated immediately and static parameters are
        set to `pending-reboot` to take effect on the next DB instance
        restart or `RebootDBInstance` request.

        :type db_parameter_group_name: string
        :param db_parameter_group_name:
        The name of the DB parameter group.

        Constraints:


        + Must be 1 to 255 alphanumeric characters
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type reset_all_parameters: boolean
        :param reset_all_parameters: Specifies whether ( `True`) or not (
            `False`) to reset all parameters in the DB parameter group to
            default values.
        Default: `True`

        :type parameters: list
        :param parameters: An array of parameter names, values, and the apply
            method for the parameter update. At least one parameter name,
            value, and apply method must be supplied; subsequent arguments are
            optional. A maximum of 20 parameters may be modified in a single
            request.
        **MySQL**

        Valid Values (for Apply method): `immediate` | `pending-reboot`

        You can use the immediate value with dynamic parameters only. You can
            use the `pending-reboot` value for both dynamic and static
            parameters, and changes are applied when DB instance reboots.

        **Oracle**

        Valid Values (for Apply method): `pending-reboot`

        """
        params = {'DBParameterGroupName': db_parameter_group_name, }
        if reset_all_parameters is not None:
            params['ResetAllParameters'] = str(
                reset_all_parameters).lower()
        if parameters is not None:
            self.build_complex_list_params(
                params, parameters,
                'Parameters.member',
                ('ParameterName', 'ParameterValue', 'Description', 'Source', 'ApplyType', 'DataType', 'AllowedValues', 'IsModifiable', 'MinimumEngineVersion', 'ApplyMethod'))
        return self._make_request(
            action='ResetDBParameterGroup',
            verb='POST',
            path='/', params=params)

    def restore_db_instance_from_db_snapshot(self, db_instance_identifier,
                                             db_snapshot_identifier,
                                             db_instance_class=None,
                                             port=None,
                                             availability_zone=None,
                                             db_subnet_group_name=None,
                                             multi_az=None,
                                             publicly_accessible=None,
                                             auto_minor_version_upgrade=None,
                                             license_model=None,
                                             db_name=None, engine=None,
                                             iops=None,
                                             option_group_name=None,
                                             tags=None):
        """
        Creates a new DB instance from a DB snapshot. The target
        database is created from the source database restore point
        with the same configuration as the original source database,
        except that the new RDS instance is created with the default
        security group.

        :type db_instance_identifier: string
        :param db_instance_identifier:
        The identifier for the DB snapshot to restore from.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type db_snapshot_identifier: string
        :param db_snapshot_identifier: Name of the DB instance to create from
            the DB snapshot. This parameter isn't case sensitive.
        Constraints:


        + Must contain from 1 to 255 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens


        Example: `my-snapshot-id`

        :type db_instance_class: string
        :param db_instance_class: The compute and memory capacity of the Amazon
            RDS DB instance.
        Valid Values: `db.t1.micro | db.m1.small | db.m1.medium | db.m1.large |
            db.m1.xlarge | db.m2.2xlarge | db.m2.4xlarge`

        :type port: integer
        :param port: The port number on which the database accepts connections.
        Default: The same port as the original DB instance

        Constraints: Value must be `1150-65535`

        :type availability_zone: string
        :param availability_zone: The EC2 Availability Zone that the database
            instance will be created in.
        Default: A random, system-chosen Availability Zone.

        Constraint: You cannot specify the AvailabilityZone parameter if the
            MultiAZ parameter is set to `True`.

        Example: `us-east-1a`

        :type db_subnet_group_name: string
        :param db_subnet_group_name: The DB subnet group name to use for the
            new instance.

        :type multi_az: boolean
        :param multi_az: Specifies if the DB instance is a Multi-AZ deployment.
        Constraint: You cannot specify the AvailabilityZone parameter if the
            MultiAZ parameter is set to `True`.

        :type publicly_accessible: boolean
        :param publicly_accessible: Specifies the accessibility options for the
            DB instance. A value of true specifies an Internet-facing instance
            with a publicly resolvable DNS name, which resolves to a public IP
            address. A value of false specifies an internal instance with a DNS
            name that resolves to a private IP address.
        Default: The default behavior varies depending on whether a VPC has
            been requested or not. The following list shows the default
            behavior in each case.


        + **Default VPC:**true
        + **VPC:**false


        If no DB subnet group has been specified as part of the request and the
            PubliclyAccessible value has not been set, the DB instance will be
            publicly accessible. If a specific DB subnet group has been
            specified as part of the request and the PubliclyAccessible value
            has not been set, the DB instance will be private.

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Indicates that minor version
            upgrades will be applied automatically to the DB instance during
            the maintenance window.

        :type license_model: string
        :param license_model: License model information for the restored DB
            instance.
        Default: Same as source.

        Valid values: `license-included` | `bring-your-own-license` | `general-
            public-license`

        :type db_name: string
        :param db_name:
        The database name for the restored DB instance.


        This parameter doesn't apply to the MySQL engine.

        :type engine: string
        :param engine: The database engine to use for the new instance.
        Default: The same as source

        Constraint: Must be compatible with the engine of the source

        Example: `oracle-ee`

        :type iops: integer
        :param iops: Specifies the amount of provisioned IOPS for the DB
            instance, expressed in I/O operations per second. If this parameter
            is not specified, the IOPS value will be taken from the backup. If
            this parameter is set to 0, the new instance will be converted to a
            non-PIOPS instance, which will take additional time, though your DB
            instance will be available for connections before the conversion
            starts.
        Constraints: Must be an integer greater than 1000.

        :type option_group_name: string
        :param option_group_name: The name of the option group to be used for
            the restored DB instance.
        Permanent options, such as the TDE option for Oracle Advanced Security
            TDE, cannot be removed from an option group, and that option group
            cannot be removed from a DB instance once it is associated with a
            DB instance

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'DBInstanceIdentifier': db_instance_identifier,
            'DBSnapshotIdentifier': db_snapshot_identifier,
        }
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if port is not None:
            params['Port'] = port
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if db_subnet_group_name is not None:
            params['DBSubnetGroupName'] = db_subnet_group_name
        if multi_az is not None:
            params['MultiAZ'] = str(
                multi_az).lower()
        if publicly_accessible is not None:
            params['PubliclyAccessible'] = str(
                publicly_accessible).lower()
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        if license_model is not None:
            params['LicenseModel'] = license_model
        if db_name is not None:
            params['DBName'] = db_name
        if engine is not None:
            params['Engine'] = engine
        if iops is not None:
            params['Iops'] = iops
        if option_group_name is not None:
            params['OptionGroupName'] = option_group_name
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='RestoreDBInstanceFromDBSnapshot',
            verb='POST',
            path='/', params=params)

    def restore_db_instance_to_point_in_time(self,
                                             source_db_instance_identifier,
                                             target_db_instance_identifier,
                                             restore_time=None,
                                             use_latest_restorable_time=None,
                                             db_instance_class=None,
                                             port=None,
                                             availability_zone=None,
                                             db_subnet_group_name=None,
                                             multi_az=None,
                                             publicly_accessible=None,
                                             auto_minor_version_upgrade=None,
                                             license_model=None,
                                             db_name=None, engine=None,
                                             iops=None,
                                             option_group_name=None,
                                             tags=None):
        """
        Restores a DB instance to an arbitrary point-in-time. Users
        can restore to any point in time before the
        latestRestorableTime for up to backupRetentionPeriod days. The
        target database is created from the source database with the
        same configuration as the original database except that the DB
        instance is created with the default DB security group.

        :type source_db_instance_identifier: string
        :param source_db_instance_identifier:
        The identifier of the source DB instance from which to restore.

        Constraints:


        + Must be the identifier of an existing database instance
        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type target_db_instance_identifier: string
        :param target_db_instance_identifier:
        The name of the new database instance to be created.

        Constraints:


        + Must contain from 1 to 63 alphanumeric characters or hyphens
        + First character must be a letter
        + Cannot end with a hyphen or contain two consecutive hyphens

        :type restore_time: timestamp
        :param restore_time: The date and time to restore from.
        Valid Values: Value must be a UTC time

        Constraints:


        + Must be before the latest restorable time for the DB instance
        + Cannot be specified if UseLatestRestorableTime parameter is true


        Example: `2009-09-07T23:45:00Z`

        :type use_latest_restorable_time: boolean
        :param use_latest_restorable_time: Specifies whether ( `True`) or not (
            `False`) the DB instance is restored from the latest backup time.
        Default: `False`

        Constraints: Cannot be specified if RestoreTime parameter is provided.

        :type db_instance_class: string
        :param db_instance_class: The compute and memory capacity of the Amazon
            RDS DB instance.
        Valid Values: `db.t1.micro | db.m1.small | db.m1.medium | db.m1.large |
            db.m1.xlarge | db.m2.2xlarge | db.m2.4xlarge`

        Default: The same DBInstanceClass as the original DB instance.

        :type port: integer
        :param port: The port number on which the database accepts connections.
        Constraints: Value must be `1150-65535`

        Default: The same port as the original DB instance.

        :type availability_zone: string
        :param availability_zone: The EC2 Availability Zone that the database
            instance will be created in.
        Default: A random, system-chosen Availability Zone.

        Constraint: You cannot specify the AvailabilityZone parameter if the
            MultiAZ parameter is set to true.

        Example: `us-east-1a`

        :type db_subnet_group_name: string
        :param db_subnet_group_name: The DB subnet group name to use for the
            new instance.

        :type multi_az: boolean
        :param multi_az: Specifies if the DB instance is a Multi-AZ deployment.
        Constraint: You cannot specify the AvailabilityZone parameter if the
            MultiAZ parameter is set to `True`.

        :type publicly_accessible: boolean
        :param publicly_accessible: Specifies the accessibility options for the
            DB instance. A value of true specifies an Internet-facing instance
            with a publicly resolvable DNS name, which resolves to a public IP
            address. A value of false specifies an internal instance with a DNS
            name that resolves to a private IP address.
        Default: The default behavior varies depending on whether a VPC has
            been requested or not. The following list shows the default
            behavior in each case.


        + **Default VPC:**true
        + **VPC:**false


        If no DB subnet group has been specified as part of the request and the
            PubliclyAccessible value has not been set, the DB instance will be
            publicly accessible. If a specific DB subnet group has been
            specified as part of the request and the PubliclyAccessible value
            has not been set, the DB instance will be private.

        :type auto_minor_version_upgrade: boolean
        :param auto_minor_version_upgrade: Indicates that minor version
            upgrades will be applied automatically to the DB instance during
            the maintenance window.

        :type license_model: string
        :param license_model: License model information for the restored DB
            instance.
        Default: Same as source.

        Valid values: `license-included` | `bring-your-own-license` | `general-
            public-license`

        :type db_name: string
        :param db_name:
        The database name for the restored DB instance.


        This parameter is not used for the MySQL engine.

        :type engine: string
        :param engine: The database engine to use for the new instance.
        Default: The same as source

        Constraint: Must be compatible with the engine of the source

        Example: `oracle-ee`

        :type iops: integer
        :param iops: The amount of Provisioned IOPS (input/output operations
            per second) to be initially allocated for the DB instance.
        Constraints: Must be an integer greater than 1000.

        :type option_group_name: string
        :param option_group_name: The name of the option group to be used for
            the restored DB instance.
        Permanent options, such as the TDE option for Oracle Advanced Security
            TDE, cannot be removed from an option group, and that option group
            cannot be removed from a DB instance once it is associated with a
            DB instance

        :type tags: list
        :param tags: A list of tags. Tags must be passed as tuples in the form
            [('key1', 'valueForKey1'), ('key2', 'valueForKey2')]

        """
        params = {
            'SourceDBInstanceIdentifier': source_db_instance_identifier,
            'TargetDBInstanceIdentifier': target_db_instance_identifier,
        }
        if restore_time is not None:
            params['RestoreTime'] = restore_time
        if use_latest_restorable_time is not None:
            params['UseLatestRestorableTime'] = str(
                use_latest_restorable_time).lower()
        if db_instance_class is not None:
            params['DBInstanceClass'] = db_instance_class
        if port is not None:
            params['Port'] = port
        if availability_zone is not None:
            params['AvailabilityZone'] = availability_zone
        if db_subnet_group_name is not None:
            params['DBSubnetGroupName'] = db_subnet_group_name
        if multi_az is not None:
            params['MultiAZ'] = str(
                multi_az).lower()
        if publicly_accessible is not None:
            params['PubliclyAccessible'] = str(
                publicly_accessible).lower()
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(
                auto_minor_version_upgrade).lower()
        if license_model is not None:
            params['LicenseModel'] = license_model
        if db_name is not None:
            params['DBName'] = db_name
        if engine is not None:
            params['Engine'] = engine
        if iops is not None:
            params['Iops'] = iops
        if option_group_name is not None:
            params['OptionGroupName'] = option_group_name
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='RestoreDBInstanceToPointInTime',
            verb='POST',
            path='/', params=params)

    def revoke_db_security_group_ingress(self, db_security_group_name,
                                         cidrip=None,
                                         ec2_security_group_name=None,
                                         ec2_security_group_id=None,
                                         ec2_security_group_owner_id=None):
        """
        Revokes ingress from a DBSecurityGroup for previously
        authorized IP ranges or EC2 or VPC Security Groups. Required
        parameters for this API are one of CIDRIP, EC2SecurityGroupId
        for VPC, or (EC2SecurityGroupOwnerId and either
        EC2SecurityGroupName or EC2SecurityGroupId).

        :type db_security_group_name: string
        :param db_security_group_name: The name of the DB security group to
            revoke ingress from.

        :type cidrip: string
        :param cidrip: The IP range to revoke access from. Must be a valid CIDR
            range. If `CIDRIP` is specified, `EC2SecurityGroupName`,
            `EC2SecurityGroupId` and `EC2SecurityGroupOwnerId` cannot be
            provided.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The name of the EC2 security group to
            revoke access from. For VPC DB security groups,
            `EC2SecurityGroupId` must be provided. Otherwise,
            EC2SecurityGroupOwnerId and either `EC2SecurityGroupName` or
            `EC2SecurityGroupId` must be provided.

        :type ec2_security_group_id: string
        :param ec2_security_group_id: The id of the EC2 security group to
            revoke access from. For VPC DB security groups,
            `EC2SecurityGroupId` must be provided. Otherwise,
            EC2SecurityGroupOwnerId and either `EC2SecurityGroupName` or
            `EC2SecurityGroupId` must be provided.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The AWS Account Number of the owner
            of the EC2 security group specified in the `EC2SecurityGroupName`
            parameter. The AWS Access Key ID is not an acceptable value. For
            VPC DB security groups, `EC2SecurityGroupId` must be provided.
            Otherwise, EC2SecurityGroupOwnerId and either
            `EC2SecurityGroupName` or `EC2SecurityGroupId` must be provided.

        """
        params = {'DBSecurityGroupName': db_security_group_name, }
        if cidrip is not None:
            params['CIDRIP'] = cidrip
        if ec2_security_group_name is not None:
            params['EC2SecurityGroupName'] = ec2_security_group_name
        if ec2_security_group_id is not None:
            params['EC2SecurityGroupId'] = ec2_security_group_id
        if ec2_security_group_owner_id is not None:
            params['EC2SecurityGroupOwnerId'] = ec2_security_group_owner_id
        return self._make_request(
            action='RevokeDBSecurityGroupIngress',
            verb='POST',
            path='/', params=params)

    def _make_request(self, action, verb, path, params):
        params['ContentType'] = 'JSON'
        response = self.make_request(action=action, verb='POST',
                                     path='/', params=params)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            json_body = json.loads(body)
            fault_name = json_body.get('Error', {}).get('Code', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)
