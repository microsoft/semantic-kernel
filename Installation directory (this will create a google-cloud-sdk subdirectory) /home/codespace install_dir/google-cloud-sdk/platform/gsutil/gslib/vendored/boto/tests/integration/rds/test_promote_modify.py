# Author: Bruce Pennypacker
#
# Create a temporary RDS database instance, then create a read-replica of the
# instance. Once the replica is available, promote it and verify that the 
# promotion succeeds, then rename it. Delete the databases upon completion i
# of the tests.
#
# For each step (creating the databases, promoting, etc) we loop for up
# to 15 minutes to wait for the instance to become available.  It should
# never take that long for any of the steps to complete.

"""
Check that promotion of read replicas and renaming instances works as expected
"""

import unittest
import time
from boto.rds import RDSConnection

class PromoteReadReplicaTest(unittest.TestCase):
    rds = True

    def setUp(self):
        self.conn = RDSConnection()
        self.masterDB_name = "boto-db-%s" % str(int(time.time()))
        self.replicaDB_name = "replica-%s" % self.masterDB_name
        self.renamedDB_name = "renamed-replica-%s" % self.masterDB_name

  
    def tearDown(self):
        instances = self.conn.get_all_dbinstances()
        for db in [self.masterDB_name, self.replicaDB_name, self.renamedDB_name]:
            for i in instances:
                if i.id == db:
                    self.conn.delete_dbinstance(db, skip_final_snapshot=True)

    def test_promote(self):
        print('--- running RDS promotion & renaming tests ---')
        self.masterDB = self.conn.create_dbinstance(self.masterDB_name, 5, 'db.t1.micro', 'root', 'bototestpw')
        
        # Wait up to 15 minutes for the masterDB to become available
        print('--- waiting for "%s" to become available  ---' % self.masterDB_name)
        wait_timeout = time.time() + (15 * 60)
        time.sleep(60)
 
        instances = self.conn.get_all_dbinstances(self.masterDB_name)
        inst = instances[0]

        while wait_timeout > time.time() and inst.status != 'available':
            time.sleep(15)
            instances = self.conn.get_all_dbinstances(self.masterDB_name)
            inst = instances[0]

        self.assertTrue(inst.status == 'available')

        self.replicaDB = self.conn.create_dbinstance_read_replica(self.replicaDB_name, self.masterDB_name)

        # Wait up to 15 minutes for the replicaDB to become available
        print('--- waiting for "%s" to become available  ---' % self.replicaDB_name)
        wait_timeout = time.time() + (15 * 60)
        time.sleep(60)
        
        instances = self.conn.get_all_dbinstances(self.replicaDB_name)
        inst = instances[0]

        while wait_timeout > time.time() and inst.status != 'available':
            time.sleep(15)
            instances = self.conn.get_all_dbinstances(self.replicaDB_name)
            inst = instances[0]

        self.assertTrue(inst.status == 'available')
        
        # Promote the replicaDB and wait for it to become available
        self.replicaDB = self.conn.promote_read_replica(self.replicaDB_name)

        # Wait up to 15 minutes for the replicaDB to become available
        print('--- waiting for "%s" to be promoted and available  ---' % self.replicaDB_name)
        wait_timeout = time.time() + (15 * 60)
        time.sleep(60)
        
        instances = self.conn.get_all_dbinstances(self.replicaDB_name)
        inst = instances[0]

        while wait_timeout > time.time() and inst.status != 'available':
            time.sleep(15)
            instances = self.conn.get_all_dbinstances(self.replicaDB_name)
            inst = instances[0]

        # Verify that the replica is now a standalone instance and no longer
        # functioning as a read replica
        self.assertTrue(inst)
        self.assertTrue(inst.status == 'available')
        self.assertFalse(inst.status_infos)

        # Verify that the master no longer has any read replicas
        instances = self.conn.get_all_dbinstances(self.masterDB_name)
        inst = instances[0]
        self.assertFalse(inst.read_replica_dbinstance_identifiers)

        print('--- renaming "%s" to "%s" ---' % ( self.replicaDB_name, self.renamedDB_name ))

        self.renamedDB = self.conn.modify_dbinstance(self.replicaDB_name, new_instance_id=self.renamedDB_name, apply_immediately=True)

        # Wait up to 15 minutes for the masterDB to become available
        print('--- waiting for "%s" to exist  ---' % self.renamedDB_name)

        wait_timeout = time.time() + (15 * 60)
        time.sleep(60)

        # Wait up to 15 minutes until the new name shows up in the instance table
        found = False
        while found == False and wait_timeout > time.time():
          instances = self.conn.get_all_dbinstances()
          for i in instances:
              if i.id == self.renamedDB_name:
                  found = True
          if found == False:
              time.sleep(15)

        self.assertTrue(found)

        print('--- waiting for "%s" to become available ---' % self.renamedDB_name)

        instances = self.conn.get_all_dbinstances(self.renamedDB_name)
        inst = instances[0]

        # Now wait for the renamed instance to become available
        while wait_timeout > time.time() and inst.status != 'available':
            time.sleep(15) 
            instances = self.conn.get_all_dbinstances(self.renamedDB_name)
            inst = instances[0]

        self.assertTrue(inst.status == 'available')

        # Since the replica DB was renamed...
        self.replicaDB = None

        print('--- tests completed ---')
