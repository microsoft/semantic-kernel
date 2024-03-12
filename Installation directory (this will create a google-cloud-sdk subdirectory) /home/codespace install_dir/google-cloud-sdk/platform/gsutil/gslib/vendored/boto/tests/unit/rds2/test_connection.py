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
from boto.rds2.layer1 import RDSConnection


class TestRDS2Connection(AWSMockServiceTestCase):
    connection_class = RDSConnection

    def setUp(self):
        super(TestRDS2Connection, self).setUp()

    def default_body(self):
        return """{
    "DescribeDBInstancesResponse": {
        "DescribeDBInstancesResult": {
            "DBInstances": [{
                "DBInstance": {
                    "Iops": 2000,
                    "BackupRetentionPeriod": 1,
                    "MultiAZ": false,
                    "DBInstanceStatus": "backing-up",
                    "DBInstanceIdentifier": "mydbinstance2",
                    "PreferredBackupWindow": "10:30-11:00",
                    "PreferredMaintenanceWindow": "wed:06:30-wed:07:00",
                    "OptionGroupMembership": {
                        "OptionGroupName": "default:mysql-5-5",
                        "Status": "in-sync"
                    },
                    "AvailabilityZone": "us-west-2b",
                    "ReadReplicaDBInstanceIdentifiers": null,
                    "Engine": "mysql",
                    "PendingModifiedValues": null,
                    "LicenseModel": "general-public-license",
                    "DBParameterGroups": [{
                        "DBParameterGroup": {
                            "ParameterApplyStatus": "in-sync",
                            "DBParameterGroupName": "default.mysql5.5"
                        }
                    }],
                    "Endpoint": {
                        "Port": 3306,
                        "Address": "mydbinstance2.c0hjqouvn9mf.us-west-2.rds.amazonaws.com"
                    },
                    "EngineVersion": "5.5.27",
                    "DBSecurityGroups": [{
                        "DBSecurityGroup": {
                            "Status": "active",
                            "DBSecurityGroupName": "default"
                        }
                    }],
                    "VpcSecurityGroups": [{
                        "VpcSecurityGroupMembership": {
                            "VpcSecurityGroupId": "sg-1",
                            "Status": "active"
                        }
                    }],
                    "DBName": "mydb2",
                    "AutoMinorVersionUpgrade": true,
                    "InstanceCreateTime": "2012-10-03T22:01:51.047Z",
                    "AllocatedStorage": 200,
                    "DBInstanceClass": "db.m1.large",
                    "MasterUsername": "awsuser",
                    "StatusInfos": [{
                        "DBInstanceStatusInfo": {
                            "Message": null,
                            "Normal": true,
                            "Status": "replicating",
                            "StatusType": "read replication"
                        }
                    }],
                    "DBSubnetGroup": {
                        "VpcId": "990524496922",
                        "SubnetGroupStatus": "Complete",
                        "DBSubnetGroupDescription": "My modified DBSubnetGroup",
                        "DBSubnetGroupName": "mydbsubnetgroup",
                        "Subnets": [{
                            "Subnet": {
                                "SubnetStatus": "Active",
                                "SubnetIdentifier": "subnet-7c5b4115",
                                "SubnetAvailabilityZone": {
                                    "Name": "us-east-1c"
                                }
                            },
                            "Subnet": {
                                "SubnetStatus": "Active",
                                "SubnetIdentifier": "subnet-7b5b4112",
                                "SubnetAvailabilityZone": {
                                    "Name": "us-east-1b"
                                }
                            },
                            "Subnet": {
                                "SubnetStatus": "Active",
                                "SubnetIdentifier": "subnet-3ea6bd57",
                                "SubnetAvailabilityZone": {
                                    "Name": "us-east-1d"
                                }
                            }
                        }]
                    }
                }
            }]
        }
    }
    }"""

    def test_describe_db_instances(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.describe_db_instances('instance_id')
        self.assertEqual(len(response), 1)
        self.assert_request_parameters({
            'Action': 'DescribeDBInstances',
            'ContentType': 'JSON',
            'DBInstanceIdentifier': 'instance_id',
        }, ignore_params_values=['Version'])
        db = response['DescribeDBInstancesResponse']\
                     ['DescribeDBInstancesResult']['DBInstances'][0]\
                     ['DBInstance']
        self.assertEqual(db['DBInstanceIdentifier'], 'mydbinstance2')
        self.assertEqual(db['InstanceCreateTime'], '2012-10-03T22:01:51.047Z')
        self.assertEqual(db['Engine'], 'mysql')
        self.assertEqual(db['DBInstanceStatus'], 'backing-up')
        self.assertEqual(db['AllocatedStorage'], 200)
        self.assertEqual(db['Endpoint']['Port'], 3306)
        self.assertEqual(db['DBInstanceClass'], 'db.m1.large')
        self.assertEqual(db['MasterUsername'], 'awsuser')
        self.assertEqual(db['AvailabilityZone'], 'us-west-2b')
        self.assertEqual(db['BackupRetentionPeriod'], 1)
        self.assertEqual(db['PreferredBackupWindow'], '10:30-11:00')
        self.assertEqual(db['PreferredMaintenanceWindow'],
                         'wed:06:30-wed:07:00')
        self.assertEqual(db['MultiAZ'], False)
        self.assertEqual(db['Iops'], 2000)
        self.assertEqual(db['PendingModifiedValues'], None)
        self.assertEqual(
            db['DBParameterGroups'][0]['DBParameterGroup']\
              ['DBParameterGroupName'],
            'default.mysql5.5'
        )
        self.assertEqual(
            db['DBSecurityGroups'][0]['DBSecurityGroup']['DBSecurityGroupName'],
            'default'
        )
        self.assertEqual(
            db['DBSecurityGroups'][0]['DBSecurityGroup']['Status'],
            'active'
        )
        self.assertEqual(len(db['StatusInfos']), 1)
        self.assertEqual(
            db['StatusInfos'][0]['DBInstanceStatusInfo']['Message'],
            None
        )
        self.assertEqual(
            db['StatusInfos'][0]['DBInstanceStatusInfo']['Normal'],
            True
        )
        self.assertEqual(
            db['StatusInfos'][0]['DBInstanceStatusInfo']['Status'],
            'replicating'
        )
        self.assertEqual(
            db['StatusInfos'][0]['DBInstanceStatusInfo']['StatusType'],
            'read replication'
        )
        self.assertEqual(
            db['VpcSecurityGroups'][0]['VpcSecurityGroupMembership']['Status'],
            'active'
        )
        self.assertEqual(
            db['VpcSecurityGroups'][0]['VpcSecurityGroupMembership']\
              ['VpcSecurityGroupId'],
            'sg-1'
        )
        self.assertEqual(db['LicenseModel'], 'general-public-license')
        self.assertEqual(db['EngineVersion'], '5.5.27')
        self.assertEqual(db['AutoMinorVersionUpgrade'], True)
        self.assertEqual(
            db['DBSubnetGroup']['DBSubnetGroupName'],
            'mydbsubnetgroup'
        )


if __name__ == '__main__':
    unittest.main()

