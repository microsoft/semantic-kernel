#!/usr/bin/env python
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.ec2.securitygroup import SecurityGroup
from boto.rds import RDSConnection
from boto.rds.vpcsecuritygroupmembership import VPCSecurityGroupMembership
from boto.rds.parametergroup import ParameterGroup
from boto.rds.logfile import LogFile, LogFileObject

import xml.sax.saxutils as saxutils

class TestRDSConnection(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDSConnection, self).setUp()

    def default_body(self):
        return """
        <DescribeDBInstancesResponse>
          <DescribeDBInstancesResult>
            <DBInstances>
                <DBInstance>
                  <Iops>2000</Iops>
                  <BackupRetentionPeriod>1</BackupRetentionPeriod>
                  <MultiAZ>false</MultiAZ>
                  <DBInstanceStatus>backing-up</DBInstanceStatus>
                  <DBInstanceIdentifier>mydbinstance2</DBInstanceIdentifier>
                  <PreferredBackupWindow>10:30-11:00</PreferredBackupWindow>
                  <PreferredMaintenanceWindow>wed:06:30-wed:07:00</PreferredMaintenanceWindow>
                  <OptionGroupMembership>
                    <OptionGroupName>default:mysql-5-5</OptionGroupName>
                    <Status>in-sync</Status>
                  </OptionGroupMembership>
                  <AvailabilityZone>us-west-2b</AvailabilityZone>
                  <ReadReplicaDBInstanceIdentifiers/>
                  <Engine>mysql</Engine>
                  <PendingModifiedValues/>
                  <LicenseModel>general-public-license</LicenseModel>
                  <DBParameterGroups>
                    <DBParameterGroup>
                      <ParameterApplyStatus>in-sync</ParameterApplyStatus>
                      <DBParameterGroupName>default.mysql5.5</DBParameterGroupName>
                    </DBParameterGroup>
                  </DBParameterGroups>
                  <Endpoint>
                    <Port>3306</Port>
                    <Address>mydbinstance2.c0hjqouvn9mf.us-west-2.rds.amazonaws.com</Address>
                  </Endpoint>
                  <EngineVersion>5.5.27</EngineVersion>
                  <DBSecurityGroups>
                    <DBSecurityGroup>
                      <Status>active</Status>
                      <DBSecurityGroupName>default</DBSecurityGroupName>
                    </DBSecurityGroup>
                  </DBSecurityGroups>
                  <VpcSecurityGroups>
                    <VpcSecurityGroupMembership>
                      <VpcSecurityGroupId>sg-1</VpcSecurityGroupId>
                      <Status>active</Status>
                    </VpcSecurityGroupMembership>
                  </VpcSecurityGroups>
                  <DBName>mydb2</DBName>
                  <AutoMinorVersionUpgrade>true</AutoMinorVersionUpgrade>
                  <InstanceCreateTime>2012-10-03T22:01:51.047Z</InstanceCreateTime>
                  <AllocatedStorage>200</AllocatedStorage>
                  <DBInstanceClass>db.m1.large</DBInstanceClass>
                  <MasterUsername>awsuser</MasterUsername>
                  <StatusInfos>
                    <DBInstanceStatusInfo>
                      <Message></Message>
                      <Normal>true</Normal>
                      <Status>replicating</Status>
                      <StatusType>read replication</StatusType>
                    </DBInstanceStatusInfo>
                  </StatusInfos>
                  <DBSubnetGroup>
                    <VpcId>990524496922</VpcId>
                    <SubnetGroupStatus>Complete</SubnetGroupStatus>
                    <DBSubnetGroupDescription>My modified DBSubnetGroup</DBSubnetGroupDescription>
                    <DBSubnetGroupName>mydbsubnetgroup</DBSubnetGroupName>
                    <Subnets>
                      <Subnet>
                        <SubnetStatus>Active</SubnetStatus>
                        <SubnetIdentifier>subnet-7c5b4115</SubnetIdentifier>
                        <SubnetAvailabilityZone>
                        <Name>us-east-1c</Name>
                      </SubnetAvailabilityZone>
                      </Subnet>
                      <Subnet>
                        <SubnetStatus>Active</SubnetStatus>
                        <SubnetIdentifier>subnet-7b5b4112</SubnetIdentifier>
                        <SubnetAvailabilityZone>
                          <Name>us-east-1b</Name>
                        </SubnetAvailabilityZone>
                      </Subnet>
                      <Subnet>
                        <SubnetStatus>Active</SubnetStatus>
                        <SubnetIdentifier>subnet-3ea6bd57</SubnetIdentifier>
                        <SubnetAvailabilityZone>
                          <Name>us-east-1d</Name>
                        </SubnetAvailabilityZone>
                      </Subnet>
                    </Subnets>
                  </DBSubnetGroup>  
              </DBInstance>
            </DBInstances>
          </DescribeDBInstancesResult>
        </DescribeDBInstancesResponse>
        """

    def test_get_all_db_instances(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_dbinstances('instance_id')
        self.assertEqual(len(response), 1)
        self.assert_request_parameters({
            'Action': 'DescribeDBInstances',
            'DBInstanceIdentifier': 'instance_id',
        }, ignore_params_values=['Version'])
        db = response[0]
        self.assertEqual(db.id, 'mydbinstance2')
        self.assertEqual(db.create_time, '2012-10-03T22:01:51.047Z')
        self.assertEqual(db.engine, 'mysql')
        self.assertEqual(db.status, 'backing-up')
        self.assertEqual(db.allocated_storage, 200)
        self.assertEqual(
            db.endpoint,
            (u'mydbinstance2.c0hjqouvn9mf.us-west-2.rds.amazonaws.com', 3306))
        self.assertEqual(db.instance_class, 'db.m1.large')
        self.assertEqual(db.master_username, 'awsuser')
        self.assertEqual(db.availability_zone, 'us-west-2b')
        self.assertEqual(db.backup_retention_period, 1)
        self.assertEqual(db.preferred_backup_window, '10:30-11:00')
        self.assertEqual(db.preferred_maintenance_window,
                         'wed:06:30-wed:07:00')
        self.assertEqual(db.latest_restorable_time, None)
        self.assertEqual(db.multi_az, False)
        self.assertEqual(db.iops, 2000)
        self.assertEqual(db.pending_modified_values, {})

        self.assertEqual(db.parameter_group.name,
                         'default.mysql5.5')
        self.assertEqual(db.parameter_group.description, None)
        self.assertEqual(db.parameter_group.engine, None)

        self.assertEqual(db.security_group.owner_id, None)
        self.assertEqual(db.security_group.name, 'default')
        self.assertEqual(db.security_group.description, None)
        self.assertEqual(db.security_group.ec2_groups, [])
        self.assertEqual(db.security_group.ip_ranges, [])
        self.assertEqual(len(db.status_infos), 1)
        self.assertEqual(db.status_infos[0].message, '')
        self.assertEqual(db.status_infos[0].normal, True)
        self.assertEqual(db.status_infos[0].status, 'replicating')
        self.assertEqual(db.status_infos[0].status_type, 'read replication')
        self.assertEqual(db.vpc_security_groups[0].status, 'active')
        self.assertEqual(db.vpc_security_groups[0].vpc_group, 'sg-1')
        self.assertEqual(db.license_model, 'general-public-license')
        self.assertEqual(db.engine_version, '5.5.27')
        self.assertEqual(db.auto_minor_version_upgrade, True)
        self.assertEqual(db.subnet_group.name, 'mydbsubnetgroup')


class TestRDSCCreateDBInstance(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDSCCreateDBInstance, self).setUp()

    def default_body(self):
        return """
        <CreateDBInstanceResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
            <CreateDBInstanceResult>
                <DBInstance>
                    <ReadReplicaDBInstanceIdentifiers/>
                    <Engine>mysql</Engine>
                    <PendingModifiedValues>
                        <MasterUserPassword>****</MasterUserPassword>
                    </PendingModifiedValues>
                    <BackupRetentionPeriod>0</BackupRetentionPeriod>
                    <MultiAZ>false</MultiAZ>
                    <LicenseModel>general-public-license</LicenseModel>
                    <DBSubnetGroup>
                        <VpcId>990524496922</VpcId>
                        <SubnetGroupStatus>Complete</SubnetGroupStatus>
                        <DBSubnetGroupDescription>description</DBSubnetGroupDescription>
                        <DBSubnetGroupName>subnet_grp1</DBSubnetGroupName>
                        <Subnets>
                            <Subnet>
                                <SubnetStatus>Active</SubnetStatus>
                                <SubnetIdentifier>subnet-7c5b4115</SubnetIdentifier>
                                <SubnetAvailabilityZone>
                                    <Name>us-east-1c</Name>
                                </SubnetAvailabilityZone>
                            </Subnet>
                            <Subnet>
                                <SubnetStatus>Active</SubnetStatus>
                                <SubnetIdentifier>subnet-7b5b4112</SubnetIdentifier>
                                <SubnetAvailabilityZone>
                                    <Name>us-east-1b</Name>
                                </SubnetAvailabilityZone>
                            </Subnet>
                            <Subnet>
                                <SubnetStatus>Active</SubnetStatus>
                                <SubnetIdentifier>subnet-3ea6bd57</SubnetIdentifier>
                                <SubnetAvailabilityZone>
                                    <Name>us-east-1d</Name>
                                </SubnetAvailabilityZone>
                            </Subnet>
                        </Subnets>
                    </DBSubnetGroup>
                    <DBInstanceStatus>creating</DBInstanceStatus>
                    <EngineVersion>5.1.50</EngineVersion>
                    <DBInstanceIdentifier>simcoprod01</DBInstanceIdentifier>
                    <DBParameterGroups>
                        <DBParameterGroup>
                            <ParameterApplyStatus>in-sync</ParameterApplyStatus>
                            <DBParameterGroupName>default.mysql5.1</DBParameterGroupName>
                        </DBParameterGroup>
                    </DBParameterGroups>
                    <DBSecurityGroups>
                        <DBSecurityGroup>
                            <Status>active</Status>
                            <DBSecurityGroupName>default</DBSecurityGroupName>
                        </DBSecurityGroup>
                    </DBSecurityGroups>
                    <PreferredBackupWindow>00:00-00:30</PreferredBackupWindow>
                    <AutoMinorVersionUpgrade>true</AutoMinorVersionUpgrade>
                    <PreferredMaintenanceWindow>sat:07:30-sat:08:00</PreferredMaintenanceWindow>
                        <AllocatedStorage>10</AllocatedStorage>
                        <DBInstanceClass>db.m1.large</DBInstanceClass>
                        <MasterUsername>master</MasterUsername>
                </DBInstance>
            </CreateDBInstanceResult>
            <ResponseMetadata>
                <RequestId>2e5d4270-8501-11e0-bd9b-a7b1ece36d51</RequestId>
            </ResponseMetadata>
        </CreateDBInstanceResponse>
        """

    def test_create_db_instance_param_group_name(self):
        self.set_http_response(status_code=200)
        db = self.service_connection.create_dbinstance(
            'SimCoProd01',
            10,
            'db.m1.large',
            'master',
            'Password01',
            param_group='default.mysql5.1',
            db_subnet_group_name='dbSubnetgroup01',
            backup_retention_period=0)

        self.assert_request_parameters({
            'Action': 'CreateDBInstance',
            'AllocatedStorage': 10,
            'AutoMinorVersionUpgrade': 'true',
            'BackupRetentionPeriod': 0,
            'DBInstanceClass': 'db.m1.large',
            'DBInstanceIdentifier': 'SimCoProd01',
            'DBParameterGroupName': 'default.mysql5.1',
            'DBSubnetGroupName': 'dbSubnetgroup01',
            'Engine': 'MySQL5.1',
            'MasterUsername': 'master',
            'MasterUserPassword': 'Password01',
            'Port': 3306
        }, ignore_params_values=['Version'])

        self.assertEqual(db.id, 'simcoprod01')
        self.assertEqual(db.engine, 'mysql')
        self.assertEqual(db.status, 'creating')
        self.assertEqual(db.allocated_storage, 10)
        self.assertEqual(db.instance_class, 'db.m1.large')
        self.assertEqual(db.master_username, 'master')
        self.assertEqual(db.multi_az, False)
        self.assertEqual(db.pending_modified_values,
            {'MasterUserPassword': '****'})

        self.assertEqual(db.parameter_group.name,
                         'default.mysql5.1')
        self.assertEqual(db.parameter_group.description, None)
        self.assertEqual(db.parameter_group.engine, None)
        self.assertEqual(db.backup_retention_period, 0)

    def test_create_db_instance_param_group_instance(self):
        self.set_http_response(status_code=200)
        param_group = ParameterGroup()
        param_group.name = 'default.mysql5.1'
        db = self.service_connection.create_dbinstance(
            'SimCoProd01',
            10,
            'db.m1.large',
            'master',
            'Password01',
            param_group=param_group,
            db_subnet_group_name='dbSubnetgroup01')

        self.assert_request_parameters({
            'Action': 'CreateDBInstance',
            'AllocatedStorage': 10,
            'AutoMinorVersionUpgrade': 'true',
            'DBInstanceClass': 'db.m1.large',
            'DBInstanceIdentifier': 'SimCoProd01',
            'DBParameterGroupName': 'default.mysql5.1',
            'DBSubnetGroupName': 'dbSubnetgroup01',
            'Engine': 'MySQL5.1',
            'MasterUsername': 'master',
            'MasterUserPassword': 'Password01',
            'Port': 3306,
        }, ignore_params_values=['Version'])

        self.assertEqual(db.id, 'simcoprod01')
        self.assertEqual(db.engine, 'mysql')
        self.assertEqual(db.status, 'creating')
        self.assertEqual(db.allocated_storage, 10)
        self.assertEqual(db.instance_class, 'db.m1.large')
        self.assertEqual(db.master_username, 'master')
        self.assertEqual(db.multi_az, False)
        self.assertEqual(db.pending_modified_values,
            {'MasterUserPassword': '****'})
        self.assertEqual(db.parameter_group.name,
                         'default.mysql5.1')
        self.assertEqual(db.parameter_group.description, None)
        self.assertEqual(db.parameter_group.engine, None)


class TestRDSConnectionRestoreDBInstanceFromPointInTime(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDSConnectionRestoreDBInstanceFromPointInTime, self).setUp()

    def default_body(self):
        return """
        <RestoreDBInstanceToPointInTimeResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
          <RestoreDBInstanceToPointInTimeResult>
            <DBInstance>
              <ReadReplicaDBInstanceIdentifiers/>
              <Engine>mysql</Engine>
              <PendingModifiedValues/>
              <BackupRetentionPeriod>1</BackupRetentionPeriod>
              <MultiAZ>false</MultiAZ>
              <LicenseModel>general-public-license</LicenseModel>
              <DBInstanceStatus>creating</DBInstanceStatus>
              <EngineVersion>5.1.50</EngineVersion>
              <DBInstanceIdentifier>restored-db</DBInstanceIdentifier>
              <DBParameterGroups>
                <DBParameterGroup>
                  <ParameterApplyStatus>in-sync</ParameterApplyStatus>
                  <DBParameterGroupName>default.mysql5.1</DBParameterGroupName>
                </DBParameterGroup>
              </DBParameterGroups>
              <DBSecurityGroups>
                <DBSecurityGroup>
                  <Status>active</Status>
                  <DBSecurityGroupName>default</DBSecurityGroupName>
                </DBSecurityGroup>
              </DBSecurityGroups>
              <PreferredBackupWindow>00:00-00:30</PreferredBackupWindow>
              <AutoMinorVersionUpgrade>true</AutoMinorVersionUpgrade>
              <PreferredMaintenanceWindow>sat:07:30-sat:08:00</PreferredMaintenanceWindow>
              <AllocatedStorage>10</AllocatedStorage>
              <DBInstanceClass>db.m1.large</DBInstanceClass>
              <MasterUsername>master</MasterUsername>
            </DBInstance>
          </RestoreDBInstanceToPointInTimeResult>
          <ResponseMetadata>
            <RequestId>1ef546bc-850b-11e0-90aa-eb648410240d</RequestId>
          </ResponseMetadata>
        </RestoreDBInstanceToPointInTimeResponse>
        """

    def test_restore_dbinstance_from_point_in_time(self):
        self.set_http_response(status_code=200)
        db = self.service_connection.restore_dbinstance_from_point_in_time(
            'simcoprod01',
            'restored-db',
            True)

        self.assert_request_parameters({
            'Action': 'RestoreDBInstanceToPointInTime',
            'SourceDBInstanceIdentifier': 'simcoprod01',
            'TargetDBInstanceIdentifier': 'restored-db',
            'UseLatestRestorableTime': 'true',
        }, ignore_params_values=['Version'])

        self.assertEqual(db.id, 'restored-db')
        self.assertEqual(db.engine, 'mysql')
        self.assertEqual(db.status, 'creating')
        self.assertEqual(db.allocated_storage, 10)
        self.assertEqual(db.instance_class, 'db.m1.large')
        self.assertEqual(db.master_username, 'master')
        self.assertEqual(db.multi_az, False)

        self.assertEqual(db.parameter_group.name,
                         'default.mysql5.1')
        self.assertEqual(db.parameter_group.description, None)
        self.assertEqual(db.parameter_group.engine, None)

    def test_restore_dbinstance_from_point_in_time__db_subnet_group_name(self):
        self.set_http_response(status_code=200)
        db = self.service_connection.restore_dbinstance_from_point_in_time(
            'simcoprod01',
            'restored-db',
            True,
            db_subnet_group_name='dbsubnetgroup')

        self.assert_request_parameters({
            'Action': 'RestoreDBInstanceToPointInTime',
            'SourceDBInstanceIdentifier': 'simcoprod01',
            'TargetDBInstanceIdentifier': 'restored-db',
            'UseLatestRestorableTime': 'true',
            'DBSubnetGroupName': 'dbsubnetgroup',
        }, ignore_params_values=['Version'])

    def test_create_db_instance_vpc_sg_str(self):
        self.set_http_response(status_code=200)
        vpc_security_groups = [
            VPCSecurityGroupMembership(self.service_connection, 'active', 'sg-1'),
            VPCSecurityGroupMembership(self.service_connection, None, 'sg-2')]

        db = self.service_connection.create_dbinstance(
            'SimCoProd01',
            10,
            'db.m1.large',
            'master',
            'Password01',
            param_group='default.mysql5.1',
            db_subnet_group_name='dbSubnetgroup01',
            vpc_security_groups=vpc_security_groups)

        self.assert_request_parameters({
            'Action': 'CreateDBInstance',
            'AllocatedStorage': 10,
            'AutoMinorVersionUpgrade': 'true',
            'DBInstanceClass': 'db.m1.large',
            'DBInstanceIdentifier': 'SimCoProd01',
            'DBParameterGroupName': 'default.mysql5.1',
            'DBSubnetGroupName': 'dbSubnetgroup01',
            'Engine': 'MySQL5.1',
            'MasterUsername': 'master',
            'MasterUserPassword': 'Password01',
            'Port': 3306,
            'VpcSecurityGroupIds.member.1': 'sg-1',
            'VpcSecurityGroupIds.member.2': 'sg-2'
        }, ignore_params_values=['Version'])

    def test_create_db_instance_vpc_sg_obj(self):
        self.set_http_response(status_code=200)

        sg1 = SecurityGroup(name='sg-1')
        sg2 = SecurityGroup(name='sg-2')

        vpc_security_groups = [
            VPCSecurityGroupMembership(self.service_connection, 'active', sg1.name),
            VPCSecurityGroupMembership(self.service_connection, None, sg2.name)]

        db = self.service_connection.create_dbinstance(
            'SimCoProd01',
            10,
            'db.m1.large',
            'master',
            'Password01',
            param_group='default.mysql5.1',
            db_subnet_group_name='dbSubnetgroup01',
            vpc_security_groups=vpc_security_groups)

        self.assert_request_parameters({
            'Action': 'CreateDBInstance',
            'AllocatedStorage': 10,
            'AutoMinorVersionUpgrade': 'true',
            'DBInstanceClass': 'db.m1.large',
            'DBInstanceIdentifier': 'SimCoProd01',
            'DBParameterGroupName': 'default.mysql5.1',
            'DBSubnetGroupName': 'dbSubnetgroup01',
            'Engine': 'MySQL5.1',
            'MasterUsername': 'master',
            'MasterUserPassword': 'Password01',
            'Port': 3306,
            'VpcSecurityGroupIds.member.1': 'sg-1',
            'VpcSecurityGroupIds.member.2': 'sg-2'
        }, ignore_params_values=['Version'])


class TestRDSOptionGroups(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDSOptionGroups, self).setUp()

    def default_body(self):
        return """
        <DescribeOptionGroupsResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
          <DescribeOptionGroupsResult>
            <OptionGroupsList>
              <OptionGroup>
                <MajorEngineVersion>11.2</MajorEngineVersion>
                <OptionGroupName>myoptiongroup</OptionGroupName>
                <EngineName>oracle-se1</EngineName>
                <OptionGroupDescription>Test option group</OptionGroupDescription>
                <Options/>
              </OptionGroup>
              <OptionGroup>
                <MajorEngineVersion>11.2</MajorEngineVersion>
                <OptionGroupName>default:oracle-se1-11-2</OptionGroupName>
                <EngineName>oracle-se1</EngineName>
                <OptionGroupDescription>Default Option Group.</OptionGroupDescription>
                <Options/>
              </OptionGroup>
            </OptionGroupsList>
          </DescribeOptionGroupsResult>
          <ResponseMetadata>
            <RequestId>e4b234d9-84d5-11e1-87a6-71059839a52b</RequestId>
          </ResponseMetadata>
        </DescribeOptionGroupsResponse>
        """

    def test_describe_option_groups(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.describe_option_groups()
        self.assertEqual(len(response), 2)
        options = response[0]
        self.assertEqual(options.name, 'myoptiongroup')
        self.assertEqual(options.description, 'Test option group')
        self.assertEqual(options.engine_name, 'oracle-se1')
        self.assertEqual(options.major_engine_version, '11.2')
        options = response[1]
        self.assertEqual(options.name, 'default:oracle-se1-11-2')
        self.assertEqual(options.description, 'Default Option Group.')
        self.assertEqual(options.engine_name, 'oracle-se1')
        self.assertEqual(options.major_engine_version, '11.2')

class TestRDSLogFile(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDSLogFile, self).setUp()

    def default_body(self):
        return """
        <DescribeDBLogFilesResponse xmlns="http://rds.amazonaws.com/doc/2013-02-12/">
          <DescribeDBLogFilesResult>
            <DescribeDBLogFiles>
              <DescribeDBLogFilesDetails>
                <LastWritten>1364403600000</LastWritten>
                <LogFileName>error/mysql-error-running.log</LogFileName>
                <Size>0</Size>
              </DescribeDBLogFilesDetails>
              <DescribeDBLogFilesDetails>
                <LastWritten>1364338800000</LastWritten>
                <LogFileName>error/mysql-error-running.log.0</LogFileName>
                <Size>0</Size>
              </DescribeDBLogFilesDetails>
              <DescribeDBLogFilesDetails>
                <LastWritten>1364342400000</LastWritten>
                <LogFileName>error/mysql-error-running.log.1</LogFileName>
                <Size>0</Size>
              </DescribeDBLogFilesDetails>
              <DescribeDBLogFilesDetails>
                <LastWritten>1364346000000</LastWritten>
                <LogFileName>error/mysql-error-running.log.2</LogFileName>
                <Size>0</Size>
              </DescribeDBLogFilesDetails>
              <DescribeDBLogFilesDetails>
                <LastWritten>1364349600000</LastWritten>
                <LogFileName>error/mysql-error-running.log.3</LogFileName>
                <Size>0</Size>
              </DescribeDBLogFilesDetails>
              <DescribeDBLogFilesDetails>
                <LastWritten>1364405700000</LastWritten>
                <LogFileName>error/mysql-error.log</LogFileName>
                <Size>0</Size>
              </DescribeDBLogFilesDetails>
            </DescribeDBLogFiles>
          </DescribeDBLogFilesResult>
          <ResponseMetadata>
            <RequestId>d70fb3b3-9704-11e2-a0db-871552e0ef19</RequestId>
          </ResponseMetadata>
        </DescribeDBLogFilesResponse>
        """

    def test_get_all_logs_simple(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_logs('db1')

        self.assert_request_parameters({
            'Action': 'DescribeDBLogFiles',
            'DBInstanceIdentifier': 'db1',
        }, ignore_params_values=['Version'])

        self.assertEqual(len(response), 6)
        self.assertTrue(isinstance(response[0], LogFile))
        self.assertEqual(response[0].log_filename, 'error/mysql-error-running.log')
        self.assertEqual(response[0].last_written, '1364403600000')
        self.assertEqual(response[0].size, '0')

    def test_get_all_logs_filtered(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_logs('db_instance_1', max_records=100, marker='error/mysql-error.log', file_size=2000000, filename_contains='error', file_last_written=12345678)

        self.assert_request_parameters({
            'Action': 'DescribeDBLogFiles',
            'DBInstanceIdentifier': 'db_instance_1',
            'MaxRecords': 100,
            'Marker': 'error/mysql-error.log',
            'FileSize': 2000000,
            'FilenameContains': 'error',
            'FileLastWritten': 12345678,
        }, ignore_params_values=['Version'])

        self.assertEqual(len(response), 6)
        self.assertTrue(isinstance(response[0], LogFile))
        self.assertEqual(response[0].log_filename, 'error/mysql-error-running.log')
        self.assertEqual(response[0].last_written, '1364403600000')
        self.assertEqual(response[0].size, '0')


class TestRDSLogFileDownload(AWSMockServiceTestCase):
    connection_class = RDSConnection
    logfile_sample = """
??2014-01-26 23:59:00.01 spid54      Microsoft SQL Server 2012 - 11.0.2100.60 (X64) 
    
    Feb 10 2012 19:39:15 
    
    Copyright (c) Microsoft Corporation
    
    Web Edition (64-bit) on Windows NT 6.1 &lt;X64&gt; (Build 7601: Service Pack 1) (Hypervisor)
    
    
    
2014-01-26 23:59:00.01 spid54      (c) Microsoft Corporation.

2014-01-26 23:59:00.01 spid54      All rights reserved.

2014-01-26 23:59:00.01 spid54      Server process ID is 2976.

2014-01-26 23:59:00.01 spid54      System Manufacturer: 'Xen', System Model: 'HVM domU'.

2014-01-26 23:59:00.01 spid54      Authentication mode is MIXED.

2014-01-26 23:59:00.01 spid54      Logging SQL Server messages in file 'D:\RDSDBDATA\Log\ERROR'.

2014-01-26 23:59:00.01 spid54      The service account is 'WORKGROUP\AMAZONA-NUQUUMV$'. This is an informational message; no user action is required.

2014-01-26 23:59:00.01 spid54      The error log has been reinitialized. See the previous log for older entries.

2014-01-27 00:00:56.42 spid25s     This instance of SQL Server has been using a process ID of 2976 since 10/21/2013 2:16:50 AM (local) 10/21/2013 2:16:50 AM (UTC). This is an informational message only; no user action is required.

2014-01-27 09:35:15.43 spid71      I/O is frozen on database model. No user action is required. However, if I/O is not resumed promptly, you could cancel the backup.

2014-01-27 09:35:15.44 spid72      I/O is frozen on database msdb. No user action is required. However, if I/O is not resumed promptly, you could cancel the backup.

2014-01-27 09:35:15.44 spid74      I/O is frozen on database rdsadmin. No user action is required. However, if I/O is not resumed promptly, you could cancel the backup.

2014-01-27 09:35:15.44 spid73      I/O is frozen on database master. No user action is required. However, if I/O is not resumed promptly, you could cancel the backup.

2014-01-27 09:35:25.57 spid73      I/O was resumed on database master. No user action is required.

2014-01-27 09:35:25.57 spid74      I/O was resumed on database rdsadmin. No user action is required.

2014-01-27 09:35:25.57 spid71      I/O was resumed on database model. No user action is required.

2014-01-27 09:35:25.57 spid72      I/O was resumed on database msdb. No user action is required.
    """

    def setUp(self):
        super(TestRDSLogFileDownload, self).setUp()

    def default_body(self):
        return """
<DownloadDBLogFilePortionResponse xmlns="http://rds.amazonaws.com/doc/2013-09-09/">
  <DownloadDBLogFilePortionResult>
    <Marker>0:4485</Marker>
    <LogFileData>%s</LogFileData>
    <AdditionalDataPending>false</AdditionalDataPending>
  </DownloadDBLogFilePortionResult>
  <ResponseMetadata>
    <RequestId>27143615-87ae-11e3-acc9-fb64b157268e</RequestId>
  </ResponseMetadata>
</DownloadDBLogFilePortionResponse>
        """ % self.logfile_sample

    def test_single_download(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_log_file('db1', 'foo.log')

        self.assertTrue(isinstance(response, LogFileObject))
        self.assertEqual(response.marker, '0:4485')
        self.assertEqual(response.dbinstance_id, 'db1')
        self.assertEqual(response.log_filename, 'foo.log')

        self.assertEqual(response.data, saxutils.unescape(self.logfile_sample))

        self.assert_request_parameters({
            'Action': 'DownloadDBLogFilePortion',
            'DBInstanceIdentifier': 'db1',
            'LogFileName': 'foo.log',
        }, ignore_params_values=['Version'])

    def test_multi_args(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_log_file('db1', 'foo.log', marker='0:4485', number_of_lines=10)

        self.assertTrue(isinstance(response, LogFileObject))

        self.assert_request_parameters({
            'Action': 'DownloadDBLogFilePortion',
            'DBInstanceIdentifier': 'db1',
            'Marker': '0:4485',
            'NumberOfLines': 10,
            'LogFileName': 'foo.log',
        }, ignore_params_values=['Version'])


class TestRDSOptionGroupOptions(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDSOptionGroupOptions, self).setUp()

    def default_body(self):
        return """
        <DescribeOptionGroupOptionsResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
          <DescribeOptionGroupOptionsResult>
            <OptionGroupOptions>
              <OptionGroupOption>
                <MajorEngineVersion>11.2</MajorEngineVersion>
                <PortRequired>true</PortRequired>
                <OptionsDependedOn/>
                <Description>Oracle Enterprise Manager</Description>
                <DefaultPort>1158</DefaultPort>
                <Name>OEM</Name>
                <EngineName>oracle-se1</EngineName>
                <MinimumRequiredMinorEngineVersion>0.2.v3</MinimumRequiredMinorEngineVersion>
                <Persistent>false</Persistent>
                <Permanent>false</Permanent>
              </OptionGroupOption>
            </OptionGroupOptions>
          </DescribeOptionGroupOptionsResult>
          <ResponseMetadata>
            <RequestId>d9c8f6a1-84c7-11e1-a264-0b23c28bc344</RequestId>
          </ResponseMetadata>
        </DescribeOptionGroupOptionsResponse>
        """

    def test_describe_option_group_options(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.describe_option_group_options()
        self.assertEqual(len(response), 1)
        options = response[0]
        self.assertEqual(options.name, 'OEM')
        self.assertEqual(options.description, 'Oracle Enterprise Manager')
        self.assertEqual(options.engine_name, 'oracle-se1')
        self.assertEqual(options.major_engine_version, '11.2')
        self.assertEqual(options.min_minor_engine_version, '0.2.v3')
        self.assertEqual(options.port_required, True)
        self.assertEqual(options.default_port, 1158)
        self.assertEqual(options.permanent, False)
        self.assertEqual(options.persistent, False)
        self.assertEqual(options.depends_on, [])


if __name__ == '__main__':
    unittest.main()

