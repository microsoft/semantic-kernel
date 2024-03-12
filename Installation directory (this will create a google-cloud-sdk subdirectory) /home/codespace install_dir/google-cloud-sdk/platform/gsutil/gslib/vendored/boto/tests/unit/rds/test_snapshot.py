from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.rds import RDSConnection
from boto.rds.dbsnapshot import DBSnapshot
from boto.rds import DBInstance


class TestDescribeDBSnapshots(AWSMockServiceTestCase):
    connection_class = RDSConnection
    
    def default_body(self):
        return """
        <DescribeDBSnapshotsResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
            <DescribeDBSnapshotsResult>
                <DBSnapshots>
                <DBSnapshot>
                    <Port>3306</Port>
                    <SnapshotCreateTime>2011-05-23T06:29:03.483Z</SnapshotCreateTime>
                    <Engine>mysql</Engine>
                    <Status>available</Status>
                    <AvailabilityZone>us-east-1a</AvailabilityZone>
                    <LicenseModel>general-public-license</LicenseModel>
                    <InstanceCreateTime>2011-05-23T06:06:43.110Z</InstanceCreateTime>
                    <AllocatedStorage>10</AllocatedStorage>
                    <DBInstanceIdentifier>simcoprod01</DBInstanceIdentifier>
                    <EngineVersion>5.1.50</EngineVersion>
                    <DBSnapshotIdentifier>mydbsnapshot</DBSnapshotIdentifier>
                    <SnapshotType>manual</SnapshotType>
                    <MasterUsername>master</MasterUsername>
                    <OptionGroupName>myoptiongroupname</OptionGroupName>
                    <Iops>1000</Iops>
                    <PercentProgress>100</PercentProgress>
                    <SourceRegion>eu-west-1</SourceRegion>
                    <VpcId>myvpc</VpcId>
                </DBSnapshot>
                <DBSnapshot>
                    <Port>3306</Port>
                    <SnapshotCreateTime>2011-03-11T07:20:24.082Z</SnapshotCreateTime>
                    <Engine>mysql</Engine>
                    <Status>available</Status>
                    <AvailabilityZone>us-east-1a</AvailabilityZone>
                    <LicenseModel>general-public-license</LicenseModel>
                    <InstanceCreateTime>2010-08-04T23:27:36.420Z</InstanceCreateTime>
                    <AllocatedStorage>50</AllocatedStorage>
                    <DBInstanceIdentifier>mydbinstance</DBInstanceIdentifier>
                    <EngineVersion>5.1.49</EngineVersion>
                    <DBSnapshotIdentifier>mysnapshot1</DBSnapshotIdentifier>
                    <SnapshotType>manual</SnapshotType>
                    <MasterUsername>sa</MasterUsername>
                    <OptionGroupName>myoptiongroupname</OptionGroupName>
                    <Iops>1000</Iops>
                </DBSnapshot>
                <DBSnapshot>
                    <Port>3306</Port>
                    <SnapshotCreateTime>2012-04-02T00:01:24.082Z</SnapshotCreateTime>
                    <Engine>mysql</Engine>
                    <Status>available</Status>
                    <AvailabilityZone>us-east-1d</AvailabilityZone>
                    <LicenseModel>general-public-license</LicenseModel>
                    <InstanceCreateTime>2010-07-16T00:06:59.107Z</InstanceCreateTime>
                    <AllocatedStorage>60</AllocatedStorage>
                    <DBInstanceIdentifier>simcoprod01</DBInstanceIdentifier>
                    <EngineVersion>5.1.47</EngineVersion>
                    <DBSnapshotIdentifier>rds:simcoprod01-2012-04-02-00-01</DBSnapshotIdentifier>
                    <SnapshotType>automated</SnapshotType>
                    <MasterUsername>master</MasterUsername>
                    <OptionGroupName>myoptiongroupname</OptionGroupName>
                    <Iops>1000</Iops>
                </DBSnapshot>
                </DBSnapshots>
            </DescribeDBSnapshotsResult>
            <ResponseMetadata>
                <RequestId>c4191173-8506-11e0-90aa-eb648410240d</RequestId>
            </ResponseMetadata>
        </DescribeDBSnapshotsResponse>        
        """
        
    def test_describe_dbinstances_by_instance(self):
        self.set_http_response(status_code=200)        
        response = self.service_connection.get_all_dbsnapshots(instance_id='simcoprod01')
        self.assert_request_parameters({
            'Action': 'DescribeDBSnapshots',
            'DBInstanceIdentifier': 'simcoprod01'
            }, ignore_params_values=['Version'])
        self.assertEqual(len(response), 3)
        self.assertIsInstance(response[0], DBSnapshot)
        self.assertEqual(response[0].id, 'mydbsnapshot')
        self.assertEqual(response[0].status, 'available')
        self.assertEqual(response[0].instance_id, 'simcoprod01')
        self.assertEqual(response[0].engine_version, '5.1.50')
        self.assertEqual(response[0].license_model, 'general-public-license')
        self.assertEqual(response[0].iops, 1000)
        self.assertEqual(response[0].option_group_name, 'myoptiongroupname')
        self.assertEqual(response[0].percent_progress, 100)
        self.assertEqual(response[0].snapshot_type, 'manual')
        self.assertEqual(response[0].source_region, 'eu-west-1')
        self.assertEqual(response[0].vpc_id, 'myvpc')
        


class TestCreateDBSnapshot(AWSMockServiceTestCase):
    connection_class = RDSConnection
    
    def default_body(self):
        return """
        <CreateDBSnapshotResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
            <CreateDBSnapshotResult>
                <DBSnapshot>
                <Port>3306</Port>
                <Engine>mysql</Engine>
                <Status>creating</Status>
                <AvailabilityZone>us-east-1a</AvailabilityZone>
                <LicenseModel>general-public-license</LicenseModel>
                <InstanceCreateTime>2011-05-23T06:06:43.110Z</InstanceCreateTime>
                <AllocatedStorage>10</AllocatedStorage>
                <DBInstanceIdentifier>simcoprod01</DBInstanceIdentifier>
                <EngineVersion>5.1.50</EngineVersion>
                <DBSnapshotIdentifier>mydbsnapshot</DBSnapshotIdentifier>
                <SnapshotType>manual</SnapshotType>
                <MasterUsername>master</MasterUsername>
                </DBSnapshot>
            </CreateDBSnapshotResult>
            <ResponseMetadata>
                <RequestId>c4181d1d-8505-11e0-90aa-eb648410240d</RequestId>
            </ResponseMetadata>
        </CreateDBSnapshotResponse>
        """        
        
    def test_create_dbinstance(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.create_dbsnapshot('mydbsnapshot', 'simcoprod01')
        self.assert_request_parameters({
            'Action': 'CreateDBSnapshot',
            'DBSnapshotIdentifier': 'mydbsnapshot',
            'DBInstanceIdentifier': 'simcoprod01'
            }, ignore_params_values=['Version'])        
        self.assertIsInstance(response, DBSnapshot)
        self.assertEqual(response.id, 'mydbsnapshot')
        self.assertEqual(response.instance_id, 'simcoprod01')
        self.assertEqual(response.status, 'creating')


class TestCopyDBSnapshot(AWSMockServiceTestCase):
    connection_class = RDSConnection
    
    def default_body(self):
        return """
        <CopyDBSnapshotResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
            <CopyDBSnapshotResult>
                <DBSnapshot>
                <Port>3306</Port>
                <Engine>mysql</Engine>
                <Status>available</Status>
                <AvailabilityZone>us-east-1a</AvailabilityZone>
                <LicenseModel>general-public-license</LicenseModel>
                <InstanceCreateTime>2011-05-23T06:06:43.110Z</InstanceCreateTime>
                <AllocatedStorage>10</AllocatedStorage>
                <DBInstanceIdentifier>simcoprod01</DBInstanceIdentifier>
                <EngineVersion>5.1.50</EngineVersion>
                <DBSnapshotIdentifier>mycopieddbsnapshot</DBSnapshotIdentifier>
                <SnapshotType>manual</SnapshotType>
                <MasterUsername>master</MasterUsername>
                </DBSnapshot>
            </CopyDBSnapshotResult>
            <ResponseMetadata>
                <RequestId>c4181d1d-8505-11e0-90aa-eb648410240d</RequestId>
            </ResponseMetadata>
        </CopyDBSnapshotResponse>        
        """
        
    def test_copy_dbinstance(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.copy_dbsnapshot('myautomaticdbsnapshot', 'mycopieddbsnapshot')
        self.assert_request_parameters({
            'Action': 'CopyDBSnapshot',
            'SourceDBSnapshotIdentifier': 'myautomaticdbsnapshot',
            'TargetDBSnapshotIdentifier': 'mycopieddbsnapshot'
            }, ignore_params_values=['Version'])
        self.assertIsInstance(response, DBSnapshot)
        self.assertEqual(response.id, 'mycopieddbsnapshot')
        self.assertEqual(response.status, 'available')
        

class TestDeleteDBSnapshot(AWSMockServiceTestCase):
    connection_class = RDSConnection
    
    def default_body(self): 
        return """
        <DeleteDBSnapshotResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
            <DeleteDBSnapshotResult>
                <DBSnapshot>
                <Port>3306</Port>
                <SnapshotCreateTime>2011-03-11T07:20:24.082Z</SnapshotCreateTime>
                <Engine>mysql</Engine>
                <Status>deleted</Status>
                <AvailabilityZone>us-east-1d</AvailabilityZone>
                <LicenseModel>general-public-license</LicenseModel>
                <InstanceCreateTime>2010-07-16T00:06:59.107Z</InstanceCreateTime>
                <AllocatedStorage>60</AllocatedStorage>
                <DBInstanceIdentifier>simcoprod01</DBInstanceIdentifier>
                <EngineVersion>5.1.47</EngineVersion>
                <DBSnapshotIdentifier>mysnapshot2</DBSnapshotIdentifier>
                <SnapshotType>manual</SnapshotType>
                <MasterUsername>master</MasterUsername>
                </DBSnapshot>
            </DeleteDBSnapshotResult>
            <ResponseMetadata>
                <RequestId>627a43a1-8507-11e0-bd9b-a7b1ece36d51</RequestId>
            </ResponseMetadata>
        </DeleteDBSnapshotResponse>
        """
        
    def test_delete_dbinstance(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.delete_dbsnapshot('mysnapshot2')
        self.assert_request_parameters({
            'Action': 'DeleteDBSnapshot',
            'DBSnapshotIdentifier': 'mysnapshot2'
            }, ignore_params_values=['Version'])
        self.assertIsInstance(response, DBSnapshot)
        self.assertEqual(response.id, 'mysnapshot2')
        self.assertEqual(response.status, 'deleted')        
        
        
class TestRestoreDBInstanceFromDBSnapshot(AWSMockServiceTestCase):
    connection_class = RDSConnection
    
    def default_body(self): 
        return """
        <RestoreDBInstanceFromDBSnapshotResponse xmlns="http://rds.amazonaws.com/doc/2013-05-15/">
            <RestoreDBInstanceFromDBSnapshotResult>
                <DBInstance>
                <ReadReplicaDBInstanceIdentifiers/>
                <Engine>mysql</Engine>
                <PendingModifiedValues/>
                <BackupRetentionPeriod>1</BackupRetentionPeriod>
                <MultiAZ>false</MultiAZ>
                <LicenseModel>general-public-license</LicenseModel>
                <DBInstanceStatus>creating</DBInstanceStatus>
                <EngineVersion>5.1.50</EngineVersion>
                <DBInstanceIdentifier>myrestoreddbinstance</DBInstanceIdentifier>
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
            </RestoreDBInstanceFromDBSnapshotResult>
            <ResponseMetadata>
                <RequestId>7ca622e8-8508-11e0-bd9b-a7b1ece36d51</RequestId>
            </ResponseMetadata>
        </RestoreDBInstanceFromDBSnapshotResponse>
        """
        
    def test_restore_dbinstance_from_dbsnapshot(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.restore_dbinstance_from_dbsnapshot('mydbsnapshot',
                                                                              'myrestoreddbinstance',
                                                                              'db.m1.large',
                                                                              '3306',
                                                                              'us-east-1a',
                                                                              'false', 
                                                                              'true')        
        self.assert_request_parameters({
            'Action': 'RestoreDBInstanceFromDBSnapshot',
            'DBSnapshotIdentifier': 'mydbsnapshot',
            'DBInstanceIdentifier': 'myrestoreddbinstance',
            'DBInstanceClass': 'db.m1.large',
            'Port': '3306',
            'AvailabilityZone': 'us-east-1a',
            'MultiAZ': 'false',
            'AutoMinorVersionUpgrade': 'true'
            }, ignore_params_values=['Version'])
        self.assertIsInstance(response, DBInstance)
        self.assertEqual(response.id, 'myrestoreddbinstance')
        self.assertEqual(response.status, 'creating')
        self.assertEqual(response.instance_class, 'db.m1.large')
        self.assertEqual(response.multi_az, False)
        
        
if __name__ == '__main__':
    unittest.main()
