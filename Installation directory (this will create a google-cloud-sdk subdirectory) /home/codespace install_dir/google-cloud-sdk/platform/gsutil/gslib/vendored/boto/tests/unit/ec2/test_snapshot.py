from tests.compat import OrderedDict
from tests.unit import AWSMockServiceTestCase

from boto.ec2.connection import EC2Connection
from boto.ec2.snapshot import Snapshot


class TestDescribeSnapshots(AWSMockServiceTestCase):

    connection_class = EC2Connection

    def default_body(self):
        return b"""
            <DescribeSnapshotsResponse xmlns="http://ec2.amazonaws.com/doc/2013-10-01/">
               <requestId>59dbff89-35bd-4eac-99ed-be587EXAMPLE</requestId>
               <snapshotSet>
                  <item>
                     <snapshotId>snap-1a2b3c4d</snapshotId>
                     <volumeId>vol-1a2b3c4d</volumeId>
                     <status>pending</status>
                     <startTime>YYYY-MM-DDTHH:MM:SS.SSSZ</startTime>
                     <progress>30%</progress>
                     <ownerId>111122223333</ownerId>
                     <volumeSize>15</volumeSize>
                     <description>Daily Backup</description>
                     <tagSet>
                        <item>
                           <key>Purpose</key>
                           <value>demo_db_14_backup</value>
                        </item>
                     </tagSet>
                     <encrypted>false</encrypted>
                  </item>
               </snapshotSet>
            </DescribeSnapshotsResponse>
        """

    def test_describe_snapshots(self):
        self.set_http_response(status_code=200)
        response = self.service_connection.get_all_snapshots(['snap-1a2b3c4d', 'snap-9f8e7d6c'],
                                                             owner=['self', '111122223333'],
                                                             restorable_by='999988887777',
                                                             filters=OrderedDict((('status', 'pending'),
                                                                                  ('tag-value', '*db_*'))))
        self.assert_request_parameters({
            'Action': 'DescribeSnapshots',
            'SnapshotId.1': 'snap-1a2b3c4d',
            'SnapshotId.2': 'snap-9f8e7d6c',
            'Owner.1': 'self',
            'Owner.2': '111122223333',
            'RestorableBy.1': '999988887777',
            'Filter.1.Name': 'status',
            'Filter.1.Value.1': 'pending',
            'Filter.2.Name': 'tag-value',
            'Filter.2.Value.1': '*db_*'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])
        self.assertEqual(len(response), 1)
        self.assertIsInstance(response[0], Snapshot)
        self.assertEqual(response[0].id, 'snap-1a2b3c4d')
