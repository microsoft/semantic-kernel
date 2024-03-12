# Copyright (c) 2009-2012 Mitch Garnaat http://garnaat.org/
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

import urllib
from boto.connection import AWSQueryConnection
from boto.rds.dbinstance import DBInstance
from boto.rds.dbsecuritygroup import DBSecurityGroup
from boto.rds.optiongroup  import OptionGroup, OptionGroupOption
from boto.rds.parametergroup import ParameterGroup
from boto.rds.dbsnapshot import DBSnapshot
from boto.rds.event import Event
from boto.rds.regioninfo import RDSRegionInfo
from boto.rds.dbsubnetgroup import DBSubnetGroup
from boto.rds.vpcsecuritygroupmembership import VPCSecurityGroupMembership
from boto.regioninfo import get_regions
from boto.regioninfo import connect
from boto.rds.logfile import LogFile, LogFileObject


def regions():
    """
    Get all available regions for the RDS service.

    :rtype: list
    :return: A list of :class:`boto.rds.regioninfo.RDSRegionInfo`
    """
    return get_regions(
        'rds',
        region_cls=RDSRegionInfo,
        connection_cls=RDSConnection
    )


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.rds.RDSConnection`.
    Any additional parameters after the region_name are passed on to
    the connect method of the region object.

    :type: str
    :param region_name: The name of the region to connect to.

    :rtype: :class:`boto.rds.RDSConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
             name is given
    """
    return connect('rds', region_name, region_cls=RDSRegionInfo,
                   connection_cls=RDSConnection, **kw_params)

#boto.set_stream_logger('rds')


class RDSConnection(AWSQueryConnection):

    DefaultRegionName = 'us-east-1'
    DefaultRegionEndpoint = 'rds.amazonaws.com'
    APIVersion = '2013-05-15'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True,
                 profile_name=None):
        if not region:
            region = RDSRegionInfo(self, self.DefaultRegionName,
                                   self.DefaultRegionEndpoint)
        self.region = region
        super(RDSConnection, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    self.region.endpoint, debug,
                                    https_connection_factory, path,
                                    security_token,
                                    validate_certs=validate_certs,
                                    profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    # DB Instance methods

    def get_all_dbinstances(self, instance_id=None, max_records=None,
                            marker=None):
        """
        Retrieve all the DBInstances in your account.

        :type instance_id: str
        :param instance_id: DB Instance identifier.  If supplied, only
                            information this instance will be returned.
                            Otherwise, info about all DB Instances will
                            be returned.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of :class:`boto.rds.dbinstance.DBInstance`
        """
        params = {}
        if instance_id:
            params['DBInstanceIdentifier'] = instance_id
        if max_records:
            params['MaxRecords'] = max_records
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeDBInstances', params,
                             [('DBInstance', DBInstance)])

    def create_dbinstance(self,
                          id,
                          allocated_storage,
                          instance_class,
                          master_username,
                          master_password,
                          port=3306,
                          engine='MySQL5.1',
                          db_name=None,
                          param_group=None,
                          security_groups=None,
                          availability_zone=None,
                          preferred_maintenance_window=None,
                          backup_retention_period=None,
                          preferred_backup_window=None,
                          multi_az=False,
                          engine_version=None,
                          auto_minor_version_upgrade=True,
                          character_set_name = None,
                          db_subnet_group_name = None,
                          license_model = None,
                          option_group_name = None,
                          iops=None,
                          vpc_security_groups=None,
                          ):
        # API version: 2013-09-09
        # Parameter notes:
        # =================
        # id should be db_instance_identifier according to API docs but has been left
        # id for backwards compatibility
        #
        # security_groups should be db_security_groups according to API docs but has been left
        # security_groups for backwards compatibility
        #
        # master_password should be master_user_password according to API docs but has been left
        # master_password for backwards compatibility
        #
        # instance_class should be db_instance_class according to API docs but has been left
        # instance_class for backwards compatibility
        """
        Create a new DBInstance.

        :type id: str
        :param id: Unique identifier for the new instance.
                   Must contain 1-63 alphanumeric characters.
                   First character must be a letter.
                   May not end with a hyphen or contain two consecutive hyphens

        :type allocated_storage: int
        :param allocated_storage: Initially allocated storage size, in GBs.
                                  Valid values are depending on the engine value.

                                  * MySQL = 5--3072
                                  * oracle-se1 = 10--3072
                                  * oracle-se = 10--3072
                                  * oracle-ee = 10--3072
                                  * sqlserver-ee = 200--1024
                                  * sqlserver-se = 200--1024
                                  * sqlserver-ex = 30--1024
                                  * sqlserver-web = 30--1024
                                  * postgres = 5--3072

        :type instance_class: str
        :param instance_class: The compute and memory capacity of
                               the DBInstance. Valid values are:

                               * db.t1.micro
                               * db.m1.small
                               * db.m1.medium
                               * db.m1.large
                               * db.m1.xlarge
                               * db.m2.xlarge
                               * db.m2.2xlarge
                               * db.m2.4xlarge

        :type engine: str
        :param engine: Name of database engine. Defaults to MySQL but can be;

                       * MySQL
                       * oracle-se1
                       * oracle-se
                       * oracle-ee
                       * sqlserver-ee
                       * sqlserver-se
                       * sqlserver-ex
                       * sqlserver-web
                       * postgres

        :type master_username: str
        :param master_username: Name of master user for the DBInstance.

                                * MySQL must be;
                                  - 1--16 alphanumeric characters
                                  - first character must be a letter
                                  - cannot be a reserved MySQL word

                                * Oracle must be:
                                  - 1--30 alphanumeric characters
                                  - first character must be a letter
                                  - cannot be a reserved Oracle word

                                * SQL Server must be:
                                  - 1--128 alphanumeric characters
                                  - first character must be a letter
                                  - cannot be a reserver SQL Server word

        :type master_password: str
        :param master_password: Password of master user for the DBInstance.

                                * MySQL must be 8--41 alphanumeric characters

                                * Oracle must be 8--30 alphanumeric characters

                                * SQL Server must be 8--128 alphanumeric characters.

        :type port: int
        :param port: Port number on which database accepts connections.
                     Valid values [1115-65535].

                     * MySQL defaults to 3306

                     * Oracle defaults to 1521

                     * SQL Server defaults to 1433 and _cannot_ be 1434, 3389,
                       47001, 49152, and 49152 through 49156.

                     * PostgreSQL defaults to 5432

        :type db_name: str
        :param db_name: * MySQL:
                          Name of a database to create when the DBInstance
                          is created. Default is to create no databases.

                          Must contain 1--64 alphanumeric characters and cannot
                          be a reserved MySQL word.

                        * Oracle:
                          The Oracle System ID (SID) of the created DB instances.
                          Default is ORCL. Cannot be longer than 8 characters.

                        * SQL Server:
                          Not applicable and must be None.

                        * PostgreSQL:
                          Name of a database to create when the DBInstance
                          is created. Default is to create no databases.

                          Must contain 1--63 alphanumeric characters. Must
                          begin with a letter or an underscore. Subsequent
                          characters can be letters, underscores, or digits (0-9)
                          and cannot be a reserved PostgreSQL word.

        :type param_group: str or ParameterGroup object
        :param param_group: Name of DBParameterGroup or ParameterGroup instance
                            to associate with this DBInstance.  If no groups are
                            specified no parameter groups will be used.

        :type security_groups: list of str or list of DBSecurityGroup objects
        :param security_groups: List of names of DBSecurityGroup to
            authorize on this DBInstance.

        :type availability_zone: str
        :param availability_zone: Name of the availability zone to place
                                  DBInstance into.

        :type preferred_maintenance_window: str
        :param preferred_maintenance_window: The weekly time range (in UTC)
                                             during which maintenance can occur.
                                             Default is Sun:05:00-Sun:09:00

        :type backup_retention_period: int
        :param backup_retention_period: The number of days for which automated
                                        backups are retained.  Setting this to
                                        zero disables automated backups.

        :type preferred_backup_window: str
        :param preferred_backup_window: The daily time range during which
                                        automated backups are created (if
                                        enabled).  Must be in h24:mi-hh24:mi
                                        format (UTC).

        :type multi_az: bool
        :param multi_az: If True, specifies the DB Instance will be
                         deployed in multiple availability zones.

                         For Microsoft SQL Server, must be set to false. You cannot set
                         the AvailabilityZone parameter if the MultiAZ parameter is
                         set to true.

        :type engine_version: str
        :param engine_version: The version number of the database engine to use.

                               * MySQL format example: 5.1.42

                               * Oracle format example: 11.2.0.2.v2

                               * SQL Server format example: 10.50.2789.0.v1

                               * PostgreSQL format example: 9.3

        :type auto_minor_version_upgrade: bool
        :param auto_minor_version_upgrade: Indicates that minor engine
                                           upgrades will be applied
                                           automatically to the Read Replica
                                           during the maintenance window.
                                           Default is True.
        :type character_set_name: str
        :param character_set_name: For supported engines, indicates that the DB Instance
                                   should be associated with the specified CharacterSet.

        :type db_subnet_group_name: str
        :param db_subnet_group_name: A DB Subnet Group to associate with this DB Instance.
                                     If there is no DB Subnet Group, then it is a non-VPC DB
                                     instance.

        :type license_model: str
        :param license_model: License model information for this DB Instance.

                              Valid values are;
                              - license-included
                              - bring-your-own-license
                              - general-public-license

                              All license types are not supported on all engines.

        :type option_group_name: str
        :param option_group_name: Indicates that the DB Instance should be associated
                                  with the specified option group.

        :type iops: int
        :param iops:  The amount of IOPS (input/output operations per second) to Provisioned
                      for the DB Instance. Can be modified at a later date.

                      Must scale linearly. For every 1000 IOPS provision, you must allocated
                      100 GB of storage space. This scales up to 1 TB / 10 000 IOPS for MySQL
                      and Oracle. MSSQL is limited to 700 GB / 7 000 IOPS.

                      If you specify a value, it must be at least 1000 IOPS and you must
                      allocate 100 GB of storage.

        :type vpc_security_groups: list of str or a VPCSecurityGroupMembership object
        :param vpc_security_groups: List of VPC security group ids or a list of
            VPCSecurityGroupMembership objects this DBInstance should be a member of

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The new db instance.
        """
        # boto argument alignment with AWS API parameter names:
        # =====================================================
        # arg => AWS parameter
        # allocated_storage => AllocatedStorage
        # auto_minor_version_update => AutoMinorVersionUpgrade
        # availability_zone => AvailabilityZone
        # backup_retention_period => BackupRetentionPeriod
        # character_set_name => CharacterSetName
        # db_instance_class => DBInstanceClass
        # db_instance_identifier => DBInstanceIdentifier
        # db_name => DBName
        # db_parameter_group_name => DBParameterGroupName
        # db_security_groups => DBSecurityGroups.member.N
        # db_subnet_group_name => DBSubnetGroupName
        # engine => Engine
        # engine_version => EngineVersion
        # license_model => LicenseModel
        # master_username => MasterUsername
        # master_user_password => MasterUserPassword
        # multi_az => MultiAZ
        # option_group_name => OptionGroupName
        # port => Port
        # preferred_backup_window => PreferredBackupWindow
        # preferred_maintenance_window => PreferredMaintenanceWindow
        # vpc_security_groups => VpcSecurityGroupIds.member.N
        params = {
                  'AllocatedStorage': allocated_storage,
                  'AutoMinorVersionUpgrade': str(auto_minor_version_upgrade).lower() if auto_minor_version_upgrade else None,
                  'AvailabilityZone': availability_zone,
                  'BackupRetentionPeriod': backup_retention_period,
                  'CharacterSetName': character_set_name,
                  'DBInstanceClass': instance_class,
                  'DBInstanceIdentifier': id,
                  'DBName': db_name,
                  'DBParameterGroupName': (param_group.name
                                           if isinstance(param_group, ParameterGroup)
                                           else param_group),
                  'DBSubnetGroupName': db_subnet_group_name,
                  'Engine': engine,
                  'EngineVersion': engine_version,
                  'Iops': iops,
                  'LicenseModel': license_model,
                  'MasterUsername': master_username,
                  'MasterUserPassword': master_password,
                  'MultiAZ': str(multi_az).lower() if multi_az else None,
                  'OptionGroupName': option_group_name,
                  'Port': port,
                  'PreferredBackupWindow': preferred_backup_window,
                  'PreferredMaintenanceWindow': preferred_maintenance_window,
                  }
        if security_groups:
            l = []
            for group in security_groups:
                if isinstance(group, DBSecurityGroup):
                    l.append(group.name)
                else:
                    l.append(group)
            self.build_list_params(params, l, 'DBSecurityGroups.member')

        if vpc_security_groups:
            l = []
            for vpc_grp in vpc_security_groups:
                if isinstance(vpc_grp, VPCSecurityGroupMembership):
                    l.append(vpc_grp.vpc_group)
                else:
                    l.append(vpc_grp)
            self.build_list_params(params, l, 'VpcSecurityGroupIds.member')

        # Remove any params set to None
        for k, v in list(params.items()):
          if v is None: del(params[k])

        return self.get_object('CreateDBInstance', params, DBInstance)

    def create_dbinstance_read_replica(self, id, source_id,
                                       instance_class=None,
                                       port=3306,
                                       availability_zone=None,
                                       auto_minor_version_upgrade=None):
        """
        Create a new DBInstance Read Replica.

        :type id: str
        :param id: Unique identifier for the new instance.
                   Must contain 1-63 alphanumeric characters.
                   First character must be a letter.
                   May not end with a hyphen or contain two consecutive hyphens

        :type source_id: str
        :param source_id: Unique identifier for the DB Instance for which this
                          DB Instance will act as a Read Replica.

        :type instance_class: str
        :param instance_class: The compute and memory capacity of the
                               DBInstance.  Default is to inherit from
                               the source DB Instance.

                               Valid values are:

                               * db.m1.small
                               * db.m1.large
                               * db.m1.xlarge
                               * db.m2.xlarge
                               * db.m2.2xlarge
                               * db.m2.4xlarge

        :type port: int
        :param port: Port number on which database accepts connections.
                     Default is to inherit from source DB Instance.
                     Valid values [1115-65535].  Defaults to 3306.

        :type availability_zone: str
        :param availability_zone: Name of the availability zone to place
                                  DBInstance into.

        :type auto_minor_version_upgrade: bool
        :param auto_minor_version_upgrade: Indicates that minor engine
                                           upgrades will be applied
                                           automatically to the Read Replica
                                           during the maintenance window.
                                           Default is to inherit this value
                                           from the source DB Instance.

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The new db instance.
        """
        params = {'DBInstanceIdentifier': id,
                  'SourceDBInstanceIdentifier': source_id}
        if instance_class:
            params['DBInstanceClass'] = instance_class
        if port:
            params['Port'] = port
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if auto_minor_version_upgrade is not None:
            if auto_minor_version_upgrade is True:
                params['AutoMinorVersionUpgrade'] = 'true'
            else:
                params['AutoMinorVersionUpgrade'] = 'false'

        return self.get_object('CreateDBInstanceReadReplica',
                               params, DBInstance)


    def promote_read_replica(self, id,
                          backup_retention_period=None,
                          preferred_backup_window=None):
        """
        Promote a Read Replica to a standalone DB Instance.

        :type id: str
        :param id: Unique identifier for the new instance.
                   Must contain 1-63 alphanumeric characters.
                   First character must be a letter.
                   May not end with a hyphen or contain two consecutive hyphens

        :type backup_retention_period: int
        :param backup_retention_period: The number of days for which automated
                                        backups are retained.  Setting this to
                                        zero disables automated backups.

        :type preferred_backup_window: str
        :param preferred_backup_window: The daily time range during which
                                        automated backups are created (if
                                        enabled).  Must be in h24:mi-hh24:mi
                                        format (UTC).

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The new db instance.
        """
        params = {'DBInstanceIdentifier': id}
        if backup_retention_period is not None:
            params['BackupRetentionPeriod'] = backup_retention_period
        if preferred_backup_window:
            params['PreferredBackupWindow'] = preferred_backup_window

        return self.get_object('PromoteReadReplica', params, DBInstance)


    def modify_dbinstance(self, id, param_group=None, security_groups=None,
                          preferred_maintenance_window=None,
                          master_password=None, allocated_storage=None,
                          instance_class=None,
                          backup_retention_period=None,
                          preferred_backup_window=None,
                          multi_az=False,
                          apply_immediately=False,
                          iops=None,
                          vpc_security_groups=None,
                          new_instance_id=None,
                          ):
        """
        Modify an existing DBInstance.

        :type id: str
        :param id: Unique identifier for the new instance.

        :type param_group: str or ParameterGroup object
        :param param_group: Name of DBParameterGroup or ParameterGroup instance
                            to associate with this DBInstance.  If no groups are
                            specified no parameter groups will be used.

        :type security_groups: list of str or list of DBSecurityGroup objects
        :param security_groups: List of names of DBSecurityGroup to authorize on
                                this DBInstance.

        :type preferred_maintenance_window: str
        :param preferred_maintenance_window: The weekly time range (in UTC)
                                             during which maintenance can
                                             occur.
                                             Default is Sun:05:00-Sun:09:00

        :type master_password: str
        :param master_password: Password of master user for the DBInstance.
                                Must be 4-15 alphanumeric characters.

        :type allocated_storage: int
        :param allocated_storage: The new allocated storage size, in GBs.
                                  Valid values are [5-1024]

        :type instance_class: str
        :param instance_class: The compute and memory capacity of the
                               DBInstance.  Changes will be applied at
                               next maintenance window unless
                               apply_immediately is True.

                               Valid values are:

                               * db.m1.small
                               * db.m1.large
                               * db.m1.xlarge
                               * db.m2.xlarge
                               * db.m2.2xlarge
                               * db.m2.4xlarge

        :type apply_immediately: bool
        :param apply_immediately: If true, the modifications will be applied
                                  as soon as possible rather than waiting for
                                  the next preferred maintenance window.

        :type backup_retention_period: int
        :param backup_retention_period: The number of days for which automated
                                        backups are retained.  Setting this to
                                        zero disables automated backups.

        :type preferred_backup_window: str
        :param preferred_backup_window: The daily time range during which
                                        automated backups are created (if
                                        enabled).  Must be in h24:mi-hh24:mi
                                        format (UTC).

        :type multi_az: bool
        :param multi_az: If True, specifies the DB Instance will be
                         deployed in multiple availability zones.

        :type iops: int
        :param iops:  The amount of IOPS (input/output operations per second) to Provisioned
                      for the DB Instance. Can be modified at a later date.

                      Must scale linearly. For every 1000 IOPS provision, you must allocated
                      100 GB of storage space. This scales up to 1 TB / 10 000 IOPS for MySQL
                      and Oracle. MSSQL is limited to 700 GB / 7 000 IOPS.

                      If you specify a value, it must be at least 1000 IOPS and you must
                      allocate 100 GB of storage.

        :type vpc_security_groups: list of str or a VPCSecurityGroupMembership object
        :param vpc_security_groups: List of VPC security group ids or a
            VPCSecurityGroupMembership object this DBInstance should be a member of

        :type new_instance_id: str
        :param new_instance_id: New name to rename the DBInstance to.

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The modified db instance.
        """
        params = {'DBInstanceIdentifier': id}
        if param_group:
            params['DBParameterGroupName'] = (param_group.name
                                              if isinstance(param_group, ParameterGroup)
                                              else param_group)
        if security_groups:
            l = []
            for group in security_groups:
                if isinstance(group, DBSecurityGroup):
                    l.append(group.name)
                else:
                    l.append(group)
            self.build_list_params(params, l, 'DBSecurityGroups.member')
        if vpc_security_groups:
            l = []
            for vpc_grp in vpc_security_groups:
                if isinstance(vpc_grp, VPCSecurityGroupMembership):
                    l.append(vpc_grp.vpc_group)
                else:
                    l.append(vpc_grp)
            self.build_list_params(params, l, 'VpcSecurityGroupIds.member')
        if preferred_maintenance_window:
            params['PreferredMaintenanceWindow'] = preferred_maintenance_window
        if master_password:
            params['MasterUserPassword'] = master_password
        if allocated_storage:
            params['AllocatedStorage'] = allocated_storage
        if instance_class:
            params['DBInstanceClass'] = instance_class
        if backup_retention_period is not None:
            params['BackupRetentionPeriod'] = backup_retention_period
        if preferred_backup_window:
            params['PreferredBackupWindow'] = preferred_backup_window
        if multi_az:
            params['MultiAZ'] = 'true'
        if apply_immediately:
            params['ApplyImmediately'] = 'true'
        if iops:
            params['Iops'] = iops
        if new_instance_id:
            params['NewDBInstanceIdentifier'] = new_instance_id

        return self.get_object('ModifyDBInstance', params, DBInstance)

    def delete_dbinstance(self, id, skip_final_snapshot=False,
                          final_snapshot_id=''):
        """
        Delete an existing DBInstance.

        :type id: str
        :param id: Unique identifier for the new instance.

        :type skip_final_snapshot: bool
        :param skip_final_snapshot: This parameter determines whether a final
                                    db snapshot is created before the instance
                                    is deleted.  If True, no snapshot
                                    is created.  If False, a snapshot
                                    is created before deleting the instance.

        :type final_snapshot_id: str
        :param final_snapshot_id: If a final snapshot is requested, this
                                  is the identifier used for that snapshot.

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The deleted db instance.
        """
        params = {'DBInstanceIdentifier': id}
        if skip_final_snapshot:
            params['SkipFinalSnapshot'] = 'true'
        else:
            params['SkipFinalSnapshot'] = 'false'
            params['FinalDBSnapshotIdentifier'] = final_snapshot_id
        return self.get_object('DeleteDBInstance', params, DBInstance)

    def reboot_dbinstance(self, id):
        """
        Reboot DBInstance.

        :type id: str
        :param id: Unique identifier of the instance.

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The rebooting db instance.
        """
        params = {'DBInstanceIdentifier': id}
        return self.get_object('RebootDBInstance', params, DBInstance)

    # DBParameterGroup methods

    def get_all_dbparameter_groups(self, groupname=None, max_records=None,
                                  marker=None):
        """
        Get all parameter groups associated with your account in a region.

        :type groupname: str
        :param groupname: The name of the DBParameter group to retrieve.
                          If not provided, all DBParameter groups will be returned.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of :class:`boto.ec2.parametergroup.ParameterGroup`
        """
        params = {}
        if groupname:
            params['DBParameterGroupName'] = groupname
        if max_records:
            params['MaxRecords'] = max_records
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeDBParameterGroups', params,
                             [('DBParameterGroup', ParameterGroup)])

    def get_all_dbparameters(self, groupname, source=None,
                             max_records=None, marker=None):
        """
        Get all parameters associated with a ParameterGroup

        :type groupname: str
        :param groupname: The name of the DBParameter group to retrieve.

        :type source: str
        :param source: Specifies which parameters to return.
                       If not specified, all parameters will be returned.
                       Valid values are: user|system|engine-default

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: :class:`boto.ec2.parametergroup.ParameterGroup`
        :return: The ParameterGroup
        """
        params = {'DBParameterGroupName': groupname}
        if source:
            params['Source'] = source
        if max_records:
            params['MaxRecords'] = max_records
        if marker:
            params['Marker'] = marker
        pg = self.get_object('DescribeDBParameters', params, ParameterGroup)
        pg.name = groupname
        return pg

    def create_parameter_group(self, name, engine='MySQL5.1', description=''):
        """
        Create a new dbparameter group for your account.

        :type name: string
        :param name: The name of the new dbparameter group

        :type engine: str
        :param engine: Name of database engine.

        :type description: string
        :param description: The description of the new dbparameter group

        :rtype: :class:`boto.rds.parametergroup.ParameterGroup`
        :return: The newly created ParameterGroup
        """
        params = {'DBParameterGroupName': name,
                  'DBParameterGroupFamily': engine,
                  'Description': description}
        return self.get_object('CreateDBParameterGroup', params, ParameterGroup)

    def modify_parameter_group(self, name, parameters=None):
        """
        Modify a ParameterGroup for your account.

        :type name: string
        :param name: The name of the new ParameterGroup

        :type parameters: list of :class:`boto.rds.parametergroup.Parameter`
        :param parameters: The new parameters

        :rtype: :class:`boto.rds.parametergroup.ParameterGroup`
        :return: The newly created ParameterGroup
        """
        params = {'DBParameterGroupName': name}
        for i in range(0, len(parameters)):
            parameter = parameters[i]
            parameter.merge(params, i+1)
        return self.get_list('ModifyDBParameterGroup', params,
                             ParameterGroup, verb='POST')

    def reset_parameter_group(self, name, reset_all_params=False,
                              parameters=None):
        """
        Resets some or all of the parameters of a ParameterGroup to the
        default value

        :type key_name: string
        :param key_name: The name of the ParameterGroup to reset

        :type parameters: list of :class:`boto.rds.parametergroup.Parameter`
        :param parameters: The parameters to reset.  If not supplied,
                           all parameters will be reset.
        """
        params = {'DBParameterGroupName': name}
        if reset_all_params:
            params['ResetAllParameters'] = 'true'
        else:
            params['ResetAllParameters'] = 'false'
            for i in range(0, len(parameters)):
                parameter = parameters[i]
                parameter.merge(params, i+1)
        return self.get_status('ResetDBParameterGroup', params)

    def delete_parameter_group(self, name):
        """
        Delete a ParameterGroup from your account.

        :type key_name: string
        :param key_name: The name of the ParameterGroup to delete
        """
        params = {'DBParameterGroupName': name}
        return self.get_status('DeleteDBParameterGroup', params)

    # DBSecurityGroup methods

    def get_all_dbsecurity_groups(self, groupname=None, max_records=None,
                                  marker=None):
        """
        Get all security groups associated with your account in a region.

        :type groupnames: list
        :param groupnames: A list of the names of security groups to retrieve.
                           If not provided, all security groups will
                           be returned.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of :class:`boto.rds.dbsecuritygroup.DBSecurityGroup`
        """
        params = {}
        if groupname:
            params['DBSecurityGroupName'] = groupname
        if max_records:
            params['MaxRecords'] = max_records
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeDBSecurityGroups', params,
                             [('DBSecurityGroup', DBSecurityGroup)])

    def create_dbsecurity_group(self, name, description=None):
        """
        Create a new security group for your account.
        This will create the security group within the region you
        are currently connected to.

        :type name: string
        :param name: The name of the new security group

        :type description: string
        :param description: The description of the new security group

        :rtype: :class:`boto.rds.dbsecuritygroup.DBSecurityGroup`
        :return: The newly created DBSecurityGroup
        """
        params = {'DBSecurityGroupName': name}
        if description:
            params['DBSecurityGroupDescription'] = description
        group = self.get_object('CreateDBSecurityGroup', params,
                                DBSecurityGroup)
        group.name = name
        group.description = description
        return group

    def delete_dbsecurity_group(self, name):
        """
        Delete a DBSecurityGroup from your account.

        :type key_name: string
        :param key_name: The name of the DBSecurityGroup to delete
        """
        params = {'DBSecurityGroupName': name}
        return self.get_status('DeleteDBSecurityGroup', params)

    def authorize_dbsecurity_group(self, group_name, cidr_ip=None,
                                   ec2_security_group_name=None,
                                   ec2_security_group_owner_id=None):
        """
        Add a new rule to an existing security group.
        You need to pass in either src_security_group_name and
        src_security_group_owner_id OR a CIDR block but not both.

        :type group_name: string
        :param group_name: The name of the security group you are adding
                           the rule to.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The name of the EC2 security group
                                        you are granting access to.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The ID of the owner of the EC2
                                            security group you are granting
                                            access to.

        :type cidr_ip: string
        :param cidr_ip: The CIDR block you are providing access to.
                        See http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing

        :rtype: bool
        :return: True if successful.
        """
        params = {'DBSecurityGroupName': group_name}
        if ec2_security_group_name:
            params['EC2SecurityGroupName'] = ec2_security_group_name
        if ec2_security_group_owner_id:
            params['EC2SecurityGroupOwnerId'] = ec2_security_group_owner_id
        if cidr_ip:
            params['CIDRIP'] = urllib.quote(cidr_ip)
        return self.get_object('AuthorizeDBSecurityGroupIngress', params,
                               DBSecurityGroup)

    def revoke_dbsecurity_group(self, group_name, ec2_security_group_name=None,
                                ec2_security_group_owner_id=None, cidr_ip=None):
        """
        Remove an existing rule from an existing security group.
        You need to pass in either ec2_security_group_name and
        ec2_security_group_owner_id OR a CIDR block.

        :type group_name: string
        :param group_name: The name of the security group you are removing
                           the rule from.

        :type ec2_security_group_name: string
        :param ec2_security_group_name: The name of the EC2 security group
                                        from which you are removing access.

        :type ec2_security_group_owner_id: string
        :param ec2_security_group_owner_id: The ID of the owner of the EC2
                                            security from which you are
                                            removing access.

        :type cidr_ip: string
        :param cidr_ip: The CIDR block from which you are removing access.
                        See http://en.wikipedia.org/wiki/Classless_Inter-Domain_Routing

        :rtype: bool
        :return: True if successful.
        """
        params = {'DBSecurityGroupName': group_name}
        if ec2_security_group_name:
            params['EC2SecurityGroupName'] = ec2_security_group_name
        if ec2_security_group_owner_id:
            params['EC2SecurityGroupOwnerId'] = ec2_security_group_owner_id
        if cidr_ip:
            params['CIDRIP'] = cidr_ip
        return self.get_object('RevokeDBSecurityGroupIngress', params,
                               DBSecurityGroup)

    # For backwards compatibility.  This method was improperly named
    # in previous versions.  I have renamed it to match the others.
    revoke_security_group = revoke_dbsecurity_group

    # DBSnapshot methods

    def get_all_dbsnapshots(self, snapshot_id=None, instance_id=None,
                            max_records=None, marker=None):
        """
        Get information about DB Snapshots.

        :type snapshot_id: str
        :param snapshot_id: The unique identifier of an RDS snapshot.
                            If not provided, all RDS snapshots will be returned.

        :type instance_id: str
        :param instance_id: The identifier of a DBInstance.  If provided,
                            only the DBSnapshots related to that instance will
                            be returned.
                            If not provided, all RDS snapshots will be returned.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of :class:`boto.rds.dbsnapshot.DBSnapshot`
        """
        params = {}
        if snapshot_id:
            params['DBSnapshotIdentifier'] = snapshot_id
        if instance_id:
            params['DBInstanceIdentifier'] = instance_id
        if max_records:
            params['MaxRecords'] = max_records
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeDBSnapshots', params,
                             [('DBSnapshot', DBSnapshot)])

    def get_all_logs(self, dbinstance_id, max_records=None, marker=None, file_size=None, filename_contains=None, file_last_written=None):
        """
        Get all log files

        :type instance_id: str
        :param instance_id: The identifier of a DBInstance.

        :type max_records: int
        :param max_records: Number of log file names to return.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :file_size: int
        :param file_size: Filter results to files large than this size in bytes.

        :filename_contains: str
        :param filename_contains: Filter results to files with filename containing this string

        :file_last_written: int
        :param file_last_written: Filter results to files written after this time (POSIX timestamp)

        :rtype: list
        :return: A list of :class:`boto.rds.logfile.LogFile`
        """
        params = {'DBInstanceIdentifier': dbinstance_id}

        if file_size:
            params['FileSize'] = file_size

        if filename_contains:
            params['FilenameContains'] = filename_contains

        if file_last_written:
            params['FileLastWritten'] = file_last_written

        if marker:
            params['Marker'] = marker

        if max_records:
            params['MaxRecords'] = max_records

        return self.get_list('DescribeDBLogFiles', params,
                             [('DescribeDBLogFilesDetails',LogFile)])

    def get_log_file(self, dbinstance_id, log_file_name, marker=None, number_of_lines=None, max_records=None):
        """
        Download a log file from RDS

        :type instance_id: str
        :param instance_id: The identifier of a DBInstance.

        :type log_file_name: str
        :param log_file_name: The name of the log file to retrieve

        :type marker: str
        :param marker: A marker returned from a previous call to this method, or 0 to indicate the start of file. If
                       no marker is specified, this will fetch log lines from the end of file instead.

        :type number_of_lines: int
        :param marker: The maximium number of lines to be returned.
        """

        params = {
                'DBInstanceIdentifier': dbinstance_id,
                'LogFileName': log_file_name,
                }

        if marker:
            params['Marker'] = marker

        if number_of_lines:
            params['NumberOfLines'] = number_of_lines

        if max_records:
            params['MaxRecords'] = max_records

        logfile =  self.get_object('DownloadDBLogFilePortion', params, LogFileObject)

        if logfile:
            logfile.log_filename = log_file_name
            logfile.dbinstance_id = dbinstance_id

        return logfile

    def create_dbsnapshot(self, snapshot_id, dbinstance_id):
        """
        Create a new DB snapshot.

        :type snapshot_id: string
        :param snapshot_id: The identifier for the DBSnapshot

        :type dbinstance_id: string
        :param dbinstance_id: The source identifier for the RDS instance from
                              which the snapshot is created.

        :rtype: :class:`boto.rds.dbsnapshot.DBSnapshot`
        :return: The newly created DBSnapshot
        """
        params = {'DBSnapshotIdentifier': snapshot_id,
                  'DBInstanceIdentifier': dbinstance_id}
        return self.get_object('CreateDBSnapshot', params, DBSnapshot)

    def copy_dbsnapshot(self, source_snapshot_id, target_snapshot_id):
        """
        Copies the specified DBSnapshot.

        :type source_snapshot_id: string
        :param source_snapshot_id: The identifier for the source DB snapshot.

        :type target_snapshot_id: string
        :param target_snapshot_id: The identifier for the copied snapshot.

        :rtype: :class:`boto.rds.dbsnapshot.DBSnapshot`
        :return: The newly created DBSnapshot.
        """
        params = {'SourceDBSnapshotIdentifier': source_snapshot_id,
                  'TargetDBSnapshotIdentifier': target_snapshot_id}
        return self.get_object('CopyDBSnapshot', params, DBSnapshot)

    def delete_dbsnapshot(self, identifier):
        """
        Delete a DBSnapshot

        :type identifier: string
        :param identifier: The identifier of the DBSnapshot to delete
        """
        params = {'DBSnapshotIdentifier': identifier}
        return self.get_object('DeleteDBSnapshot', params, DBSnapshot)

    def restore_dbinstance_from_dbsnapshot(self, identifier, instance_id,
                                           instance_class, port=None,
                                           availability_zone=None,
                                           multi_az=None,
                                           auto_minor_version_upgrade=None,
                                           db_subnet_group_name=None):
        """
        Create a new DBInstance from a DB snapshot.

        :type identifier: string
        :param identifier: The identifier for the DBSnapshot

        :type instance_id: string
        :param instance_id: The source identifier for the RDS instance from
                              which the snapshot is created.

        :type instance_class: str
        :param instance_class: The compute and memory capacity of the
                               DBInstance.  Valid values are:
                               db.m1.small | db.m1.large | db.m1.xlarge |
                               db.m2.2xlarge | db.m2.4xlarge

        :type port: int
        :param port: Port number on which database accepts connections.
                     Valid values [1115-65535].  Defaults to 3306.

        :type availability_zone: str
        :param availability_zone: Name of the availability zone to place
                                  DBInstance into.

        :type multi_az: bool
        :param multi_az: If True, specifies the DB Instance will be
                         deployed in multiple availability zones.
                         Default is the API default.

        :type auto_minor_version_upgrade: bool
        :param auto_minor_version_upgrade: Indicates that minor engine
                                           upgrades will be applied
                                           automatically to the Read Replica
                                           during the maintenance window.
                                           Default is the API default.

        :type db_subnet_group_name: str
        :param db_subnet_group_name: A DB Subnet Group to associate with this DB Instance.
                                     If there is no DB Subnet Group, then it is a non-VPC DB
                                     instance.

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The newly created DBInstance
        """
        params = {'DBSnapshotIdentifier': identifier,
                  'DBInstanceIdentifier': instance_id,
                  'DBInstanceClass': instance_class}
        if port:
            params['Port'] = port
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if multi_az is not None:
            params['MultiAZ'] = str(multi_az).lower()
        if auto_minor_version_upgrade is not None:
            params['AutoMinorVersionUpgrade'] = str(auto_minor_version_upgrade).lower()
        if db_subnet_group_name is not None:
            params['DBSubnetGroupName'] = db_subnet_group_name
        return self.get_object('RestoreDBInstanceFromDBSnapshot',
                               params, DBInstance)

    def restore_dbinstance_from_point_in_time(self, source_instance_id,
                                              target_instance_id,
                                              use_latest=False,
                                              restore_time=None,
                                              dbinstance_class=None,
                                              port=None,
                                              availability_zone=None,
                                              db_subnet_group_name=None):

        """
        Create a new DBInstance from a point in time.

        :type source_instance_id: string
        :param source_instance_id: The identifier for the source DBInstance.

        :type target_instance_id: string
        :param target_instance_id: The identifier of the new DBInstance.

        :type use_latest: bool
        :param use_latest: If True, the latest snapshot availabile will
                           be used.

        :type restore_time: datetime
        :param restore_time: The date and time to restore from.  Only
                             used if use_latest is False.

        :type instance_class: str
        :param instance_class: The compute and memory capacity of the
                               DBInstance.  Valid values are:
                               db.m1.small | db.m1.large | db.m1.xlarge |
                               db.m2.2xlarge | db.m2.4xlarge

        :type port: int
        :param port: Port number on which database accepts connections.
                     Valid values [1115-65535].  Defaults to 3306.

        :type availability_zone: str
        :param availability_zone: Name of the availability zone to place
                                  DBInstance into.

        :type db_subnet_group_name: str
        :param db_subnet_group_name: A DB Subnet Group to associate with this DB Instance.
                                     If there is no DB Subnet Group, then it is a non-VPC DB
                                     instance.

        :rtype: :class:`boto.rds.dbinstance.DBInstance`
        :return: The newly created DBInstance
        """
        params = {'SourceDBInstanceIdentifier': source_instance_id,
                  'TargetDBInstanceIdentifier': target_instance_id}
        if use_latest:
            params['UseLatestRestorableTime'] = 'true'
        elif restore_time:
            params['RestoreTime'] = restore_time.isoformat()
        if dbinstance_class:
            params['DBInstanceClass'] = dbinstance_class
        if port:
            params['Port'] = port
        if availability_zone:
            params['AvailabilityZone'] = availability_zone
        if db_subnet_group_name is not None:
            params['DBSubnetGroupName'] = db_subnet_group_name
        return self.get_object('RestoreDBInstanceToPointInTime',
                               params, DBInstance)

    # Events

    def get_all_events(self, source_identifier=None, source_type=None,
                       start_time=None, end_time=None,
                       max_records=None, marker=None):
        """
        Get information about events related to your DBInstances,
        DBSecurityGroups and DBParameterGroups.

        :type source_identifier: str
        :param source_identifier: If supplied, the events returned will be
                                  limited to those that apply to the identified
                                  source.  The value of this parameter depends
                                  on the value of source_type.  If neither
                                  parameter is specified, all events in the time
                                  span will be returned.

        :type source_type: str
        :param source_type: Specifies how the source_identifier should
                            be interpreted.  Valid values are:
                            b-instance | db-security-group |
                            db-parameter-group | db-snapshot

        :type start_time: datetime
        :param start_time: The beginning of the time interval for events.
                           If not supplied, all available events will
                           be returned.

        :type end_time: datetime
        :param end_time: The ending of the time interval for events.
                         If not supplied, all available events will
                         be returned.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of class:`boto.rds.event.Event`
        """
        params = {}
        if source_identifier and source_type:
            params['SourceIdentifier'] = source_identifier
            params['SourceType'] = source_type
        if start_time:
            params['StartTime'] = start_time.isoformat()
        if end_time:
            params['EndTime'] = end_time.isoformat()
        if max_records:
            params['MaxRecords'] = max_records
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeEvents', params, [('Event', Event)])

    def create_db_subnet_group(self, name, desc, subnet_ids):
        """
        Create a new Database Subnet Group.

        :type name: string
        :param name: The identifier for the db_subnet_group

        :type desc: string
        :param desc: A description of the db_subnet_group

        :type subnet_ids: list
        :param subnets: A list of the subnet identifiers to include in the
                        db_subnet_group

        :rtype: :class:`boto.rds.dbsubnetgroup.DBSubnetGroup
        :return: the created db_subnet_group
        """

        params = {'DBSubnetGroupName': name,
                  'DBSubnetGroupDescription': desc}
        self.build_list_params(params, subnet_ids, 'SubnetIds.member')

        return self.get_object('CreateDBSubnetGroup', params, DBSubnetGroup)

    def delete_db_subnet_group(self, name):
        """
        Delete a Database Subnet Group.

        :type name: string
        :param name: The identifier of the db_subnet_group to delete

        :rtype: :class:`boto.rds.dbsubnetgroup.DBSubnetGroup`
        :return: The deleted db_subnet_group.
        """

        params = {'DBSubnetGroupName': name}

        return self.get_object('DeleteDBSubnetGroup', params, DBSubnetGroup)


    def get_all_db_subnet_groups(self, name=None, max_records=None, marker=None):
        """
        Retrieve all the DBSubnetGroups in your account.

        :type name: str
        :param name: DBSubnetGroup name If supplied, only information about
                     this DBSubnetGroup will be returned. Otherwise, info
                     about all DBSubnetGroups will be returned.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a Token will be
                            returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of :class:`boto.rds.dbsubnetgroup.DBSubnetGroup`
        """
        params = dict()
        if name is not None:
            params['DBSubnetGroupName'] = name
        if max_records is not None:
            params['MaxRecords'] = max_records
        if marker is not None:
            params['Marker'] = marker

        return self.get_list('DescribeDBSubnetGroups', params, [('DBSubnetGroup',DBSubnetGroup)])

    def modify_db_subnet_group(self, name, description=None, subnet_ids=None):
        """
        Modify a parameter group for your account.

        :type name: string
        :param name: The name of the new parameter group

        :type parameters: list of :class:`boto.rds.parametergroup.Parameter`
        :param parameters: The new parameters

        :rtype: :class:`boto.rds.parametergroup.ParameterGroup`
        :return: The newly created ParameterGroup
        """
        params = {'DBSubnetGroupName': name}
        if description is not None:
            params['DBSubnetGroupDescription'] = description
        if subnet_ids is not None:
            self.build_list_params(params, subnet_ids, 'SubnetIds.member')

        return self.get_object('ModifyDBSubnetGroup', params, DBSubnetGroup)

    def create_option_group(self, name, engine_name, major_engine_version,
                            description=None):
        """
        Create a new option group for your account.
        This will create the option group within the region you
        are currently connected to.

        :type name: string
        :param name: The name of the new option group

        :type engine_name: string
        :param engine_name: Specifies the name of the engine that this option
                            group should be associated with.

        :type major_engine_version: string
        :param major_engine_version: Specifies the major version of the engine
                                     that this option group should be
                                     associated with.

        :type description: string
        :param description: The description of the new option group

        :rtype: :class:`boto.rds.optiongroup.OptionGroup`
        :return: The newly created OptionGroup
        """
        params = {
            'OptionGroupName': name,
            'EngineName': engine_name,
            'MajorEngineVersion': major_engine_version,
            'OptionGroupDescription': description,
        }
        group = self.get_object('CreateOptionGroup', params, OptionGroup)
        group.name = name
        group.engine_name = engine_name
        group.major_engine_version = major_engine_version
        group.description = description
        return group

    def delete_option_group(self, name):
        """
        Delete an OptionGroup from your account.

        :type key_name: string
        :param key_name: The name of the OptionGroup to delete
        """
        params = {'OptionGroupName': name}
        return self.get_status('DeleteOptionGroup', params)

    def describe_option_groups(self, name=None, engine_name=None,
                               major_engine_version=None, max_records=100,
                               marker=None):
        """
        Describes the available option groups.

        :type name: str
        :param name: The name of the option group to describe. Cannot be
                     supplied together with engine_name or major_engine_version.

        :type engine_name: str
        :param engine_name: Filters the list of option groups to only include
                            groups associated with a specific database engine.

        :type major_engine_version: datetime
        :param major_engine_version: Filters the list of option groups to only
                                     include groups associated with a specific
                                     database engine version. If specified, then
                                     engine_name must also be specified.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of class:`boto.rds.optiongroup.OptionGroup`
        """
        params = {}
        if name:
            params['OptionGroupName'] = name
        elif engine_name and major_engine_version:
            params['EngineName'] = engine_name
            params['MajorEngineVersion'] = major_engine_version
        if max_records:
            params['MaxRecords'] = int(max_records)
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeOptionGroups', params, [
            ('OptionGroup', OptionGroup)
        ])

    def describe_option_group_options(self, engine_name=None,
                               major_engine_version=None, max_records=100,
                               marker=None):
        """
        Describes the available option group options.

        :type engine_name: str
        :param engine_name: Filters the list of option groups to only include
                            groups associated with a specific database engine.

        :type major_engine_version: datetime
        :param major_engine_version: Filters the list of option groups to only
                                     include groups associated with a specific
                                     database engine version. If specified, then
                                     engine_name must also be specified.

        :type max_records: int
        :param max_records: The maximum number of records to be returned.
                            If more results are available, a MoreToken will
                            be returned in the response that can be used to
                            retrieve additional records.  Default is 100.

        :type marker: str
        :param marker: The marker provided by a previous request.

        :rtype: list
        :return: A list of class:`boto.rds.optiongroup.Option`
        """
        params = {}
        if engine_name and major_engine_version:
            params['EngineName'] = engine_name
            params['MajorEngineVersion'] = major_engine_version
        if max_records:
            params['MaxRecords'] = int(max_records)
        if marker:
            params['Marker'] = marker
        return self.get_list('DescribeOptionGroupOptions', params, [
            ('OptionGroupOptions', OptionGroupOption)
        ])
