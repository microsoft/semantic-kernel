# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

class DBSnapshot(object):
    """
    Represents a RDS DB Snapshot

    Properties reference available from the AWS documentation at http://docs.amazonwebservices.com/AmazonRDS/latest/APIReference/API_DBSnapshot.html

    :ivar engine_version: Specifies the version of the database engine
    :ivar license_model: License model information for the restored DB instance
    :ivar allocated_storage: Specifies the allocated storage size in gigabytes (GB)
    :ivar availability_zone: Specifies the name of the Availability Zone the DB Instance was located in at the time of the DB Snapshot
    :ivar connection: boto.rds.RDSConnection associated with the current object
    :ivar engine: Specifies the name of the database engine
    :ivar id: Specifies the identifier for the DB Snapshot (DBSnapshotIdentifier)
    :ivar instance_create_time: Specifies the time (UTC) when the snapshot was taken
    :ivar instance_id: Specifies the the DBInstanceIdentifier of the DB Instance this DB Snapshot was created from (DBInstanceIdentifier)
    :ivar master_username: Provides the master username for the DB Instance
    :ivar port: Specifies the port that the database engine was listening on at the time of the snapshot
    :ivar snapshot_create_time: Provides the time (UTC) when the snapshot was taken
    :ivar status: Specifies the status of this DB Snapshot. Possible values are [ available, backing-up, creating, deleted, deleting, failed, modifying, rebooting, resetting-master-credentials ]
    :ivar iops: Specifies the Provisioned IOPS (I/O operations per second) value of the DB instance at the time of the snapshot.
    :ivar option_group_name: Provides the option group name for the DB snapshot.
    :ivar percent_progress: The percentage of the estimated data that has been transferred.
    :ivar snapshot_type: Provides the type of the DB snapshot.
    :ivar source_region: The region that the DB snapshot was created in or copied from.
    :ivar vpc_id: Provides the Vpc Id associated with the DB snapshot.
    """

    def __init__(self, connection=None, id=None):
        self.connection = connection
        self.id = id
        self.engine = None
        self.engine_version = None
        self.snapshot_create_time = None
        self.instance_create_time = None
        self.port = None
        self.status = None
        self.availability_zone = None
        self.master_username = None
        self.allocated_storage = None
        self.instance_id = None
        self.availability_zone = None
        self.license_model = None
        self.iops = None
        self.option_group_name = None
        self.percent_progress = None
        self.snapshot_type = None
        self.source_region = None
        self.vpc_id = None

    def __repr__(self):
        return 'DBSnapshot:%s' % self.id

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Engine':
            self.engine = value
        elif name == 'EngineVersion':
            self.engine_version = value
        elif name == 'InstanceCreateTime':
            self.instance_create_time = value
        elif name == 'SnapshotCreateTime':
            self.snapshot_create_time = value
        elif name == 'DBInstanceIdentifier':
            self.instance_id = value
        elif name == 'DBSnapshotIdentifier':
            self.id = value
        elif name == 'Port':
            self.port = int(value)
        elif name == 'Status':
            self.status = value
        elif name == 'AvailabilityZone':
            self.availability_zone = value
        elif name == 'MasterUsername':
            self.master_username = value
        elif name == 'AllocatedStorage':
            self.allocated_storage = int(value)
        elif name == 'SnapshotTime':
            self.time = value
        elif name == 'LicenseModel':
            self.license_model = value
        elif name == 'Iops':
            self.iops = int(value)
        elif name == 'OptionGroupName':
            self.option_group_name = value
        elif name == 'PercentProgress':
            self.percent_progress = int(value)
        elif name == 'SnapshotType':
            self.snapshot_type = value
        elif name == 'SourceRegion':
            self.source_region = value
        elif name == 'VpcId':
            self.vpc_id = value
        else:
            setattr(self, name, value)

    def update(self, validate=False):
        """
        Update the DB snapshot's status information by making a call to fetch
        the current snapshot attributes from the service.

        :type validate: bool
        :param validate: By default, if EC2 returns no data about the
                         instance the update method returns quietly.  If
                         the validate param is True, however, it will
                         raise a ValueError exception if no data is
                         returned from EC2.
        """
        rs = self.connection.get_all_dbsnapshots(self.id)
        if len(rs) > 0:
            for i in rs:
                if i.id == self.id:
                    self.__dict__.update(i.__dict__)
        elif validate:
            raise ValueError('%s is not a valid Snapshot ID' % self.id)
        return self.status
