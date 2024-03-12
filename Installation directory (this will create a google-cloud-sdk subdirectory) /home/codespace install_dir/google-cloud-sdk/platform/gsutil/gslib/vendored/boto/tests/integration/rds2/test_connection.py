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

import unittest
import time
from boto.rds2.layer1 import RDSConnection


class TestRDS2Connection(unittest.TestCase):
    rds = True

    def setUp(self):
        self.conn = RDSConnection()
        self.db_name = "test-db-%s" % str(int(time.time()))

    def test_connect_rds(self):
        # Upon release, this did not function correct. Ensure that
        # args are passed correctly.
        import boto
        conn = boto.connect_rds2()

    def test_integration(self):
        resp = self.conn.create_db_instance(
            db_instance_identifier=self.db_name,
            allocated_storage=5,
            db_instance_class='db.t1.micro',
            engine='postgres',
            master_username='bototestuser',
            master_user_password='testtestt3st',
            # Try to limit the impact & test options.
            multi_az=False,
            backup_retention_period=0
        )
        self.addCleanup(
            self.conn.delete_db_instance,
            self.db_name,
            skip_final_snapshot=True
        )

        # Wait for 6 minutes for it to come up.
        time.sleep(60 * 6)

        instances = self.conn.describe_db_instances(self.db_name)
        inst = instances['DescribeDBInstancesResponse']\
                        ['DescribeDBInstancesResult']['DBInstances'][0]
        self.assertEqual(inst['DBInstanceStatus'], 'available')
        self.assertEqual(inst['Engine'], 'postgres')
        self.assertEqual(inst['AllocatedStorage'], 5)

        # Try renaming it.
        resp = self.conn.modify_db_instance(
            self.db_name,
            allocated_storage=10,
            apply_immediately=True
        )

        # Give it a chance to start modifying...
        time.sleep(60)

        instances = self.conn.describe_db_instances(self.db_name)
        inst = instances['DescribeDBInstancesResponse']\
                        ['DescribeDBInstancesResult']['DBInstances'][0]
        self.assertEqual(inst['DBInstanceStatus'], 'modifying')
        self.assertEqual(inst['Engine'], 'postgres')

        # ...then finish the remainder of 10 minutes for the change.
        time.sleep(60 * 9)

        instances = self.conn.describe_db_instances(self.db_name)
        inst = instances['DescribeDBInstancesResponse']\
                        ['DescribeDBInstancesResult']['DBInstances'][0]
        self.assertEqual(inst['DBInstanceStatus'], 'available')
        self.assertEqual(inst['Engine'], 'postgres')
        self.assertEqual(inst['AllocatedStorage'], 10)
