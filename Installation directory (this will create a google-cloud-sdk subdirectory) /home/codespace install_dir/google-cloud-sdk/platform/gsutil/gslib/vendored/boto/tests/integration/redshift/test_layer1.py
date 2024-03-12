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
import unittest
import time

from nose.plugins.attrib import attr

from boto.redshift.layer1 import RedshiftConnection
from boto.redshift.exceptions import ClusterNotFoundFault
from boto.redshift.exceptions import ResizeNotFoundFault


class TestRedshiftLayer1Management(unittest.TestCase):
    redshift = True

    def setUp(self):
        self.api = RedshiftConnection()
        self.cluster_prefix = 'boto-redshift-cluster-%s'
        self.node_type = 'dw.hs1.xlarge'
        self.master_username = 'mrtest'
        self.master_password = 'P4ssword'
        self.db_name = 'simon'
        # Redshift was taking ~20 minutes to bring clusters up in testing.
        self.wait_time = 60 * 20

    def cluster_id(self):
        # This need to be unique per-test method.
        return self.cluster_prefix % str(int(time.time()))

    def create_cluster(self):
        cluster_id = self.cluster_id()
        self.api.create_cluster(
            cluster_id, self.node_type,
            self.master_username, self.master_password,
            db_name=self.db_name, number_of_nodes=3
        )

        # Wait for it to come up.
        time.sleep(self.wait_time)

        self.addCleanup(self.delete_cluster_the_slow_way, cluster_id)
        return cluster_id

    def delete_cluster_the_slow_way(self, cluster_id):
        # Because there might be other operations in progress. :(
        time.sleep(self.wait_time)

        self.api.delete_cluster(cluster_id, skip_final_cluster_snapshot=True)

    @attr('notdefault')
    def test_create_delete_cluster(self):
        cluster_id = self.cluster_id()
        self.api.create_cluster(
            cluster_id, self.node_type,
            self.master_username, self.master_password,
            db_name=self.db_name, number_of_nodes=3
        )

        # Wait for it to come up.
        time.sleep(self.wait_time)

        self.api.delete_cluster(cluster_id, skip_final_cluster_snapshot=True)

    @attr('notdefault')
    def test_as_much_as_possible_before_teardown(self):
        # Per @garnaat, for the sake of suite time, we'll test as much as we
        # can before we teardown.

        # Test a non-existent cluster ID.
        with self.assertRaises(ClusterNotFoundFault):
            self.api.describe_clusters('badpipelineid')

        # Now create the cluster & move on.
        cluster_id = self.create_cluster()

        # Test never resized.
        with self.assertRaises(ResizeNotFoundFault):
            self.api.describe_resize(cluster_id)

        # The cluster shows up in describe_clusters
        clusters = self.api.describe_clusters()['DescribeClustersResponse']\
                                               ['DescribeClustersResult']\
                                               ['Clusters']
        cluster_ids = [c['ClusterIdentifier'] for c in clusters]
        self.assertIn(cluster_id, cluster_ids)

        # The cluster shows up in describe_clusters w/ id
        response = self.api.describe_clusters(cluster_id)
        self.assertEqual(response['DescribeClustersResponse']\
                         ['DescribeClustersResult']['Clusters'][0]\
                         ['ClusterIdentifier'], cluster_id)

        snapshot_id = "snap-%s" % cluster_id

        # Test creating a snapshot.
        response = self.api.create_cluster_snapshot(snapshot_id, cluster_id)
        self.assertEqual(response['CreateClusterSnapshotResponse']\
                         ['CreateClusterSnapshotResult']['Snapshot']\
                         ['SnapshotIdentifier'], snapshot_id)
        self.assertEqual(response['CreateClusterSnapshotResponse']\
                         ['CreateClusterSnapshotResult']['Snapshot']\
                         ['Status'], 'creating')
        self.addCleanup(self.api.delete_cluster_snapshot, snapshot_id)

        # More waiting. :(
        time.sleep(self.wait_time)

        # Describe the snapshots.
        response = self.api.describe_cluster_snapshots(
            cluster_identifier=cluster_id
        )
        snap = response['DescribeClusterSnapshotsResponse']\
                       ['DescribeClusterSnapshotsResult']['Snapshots'][-1]
        self.assertEqual(snap['SnapshotType'], 'manual')
        self.assertEqual(snap['DBName'], self.db_name)
