from tests.compat import unittest

from boto.ec2.connection import EC2Connection
from boto.ec2.blockdevicemapping import BlockDeviceType, BlockDeviceMapping

from tests.compat import OrderedDict
from tests.unit import AWSMockServiceTestCase


class BlockDeviceTypeTests(unittest.TestCase):
    def setUp(self):
        self.block_device_type = BlockDeviceType()

    def check_that_attribute_has_been_set(self, name, value, attribute):
        self.block_device_type.endElement(name, value, None)
        self.assertEqual(getattr(self.block_device_type, attribute), value)

    def test_endElement_sets_correct_attributes_with_values(self):
        for arguments in [("volumeId", 1, "volume_id"),
                          ("virtualName", "some name", "ephemeral_name"),
                          ("snapshotId", 1, "snapshot_id"),
                          ("volumeSize", 1, "size"),
                          ("status", "some status", "status"),
                          ("attachTime", 1, "attach_time"),
                          ("somethingRandom", "somethingRandom", "somethingRandom")]:
            self.check_that_attribute_has_been_set(arguments[0], arguments[1], arguments[2])

    def test_endElement_with_name_NoDevice_value_true(self):
        self.block_device_type.endElement("NoDevice", 'true', None)
        self.assertEqual(self.block_device_type.no_device, True)

    def test_endElement_with_name_NoDevice_value_other(self):
        self.block_device_type.endElement("NoDevice", 'something else', None)
        self.assertEqual(self.block_device_type.no_device, False)

    def test_endElement_with_name_deleteOnTermination_value_true(self):
        self.block_device_type.endElement("deleteOnTermination", "true", None)
        self.assertEqual(self.block_device_type.delete_on_termination, True)

    def test_endElement_with_name_deleteOnTermination_value_other(self):
        self.block_device_type.endElement("deleteOnTermination", 'something else', None)
        self.assertEqual(self.block_device_type.delete_on_termination, False)

    def test_endElement_with_name_encrypted_value_true(self):
        self.block_device_type.endElement("Encrypted", "true", None)
        self.assertEqual(self.block_device_type.encrypted, True)

    def test_endElement_with_name_Encrypted_value_other(self):
        self.block_device_type.endElement("Encrypted", 'something else', None)
        self.assertEqual(self.block_device_type.encrypted, False)


class BlockDeviceMappingTests(unittest.TestCase):
    def setUp(self):
        self.block_device_mapping = BlockDeviceMapping()

    def block_device_type_eq(self, b1, b2):
        if isinstance(b1, BlockDeviceType) and isinstance(b2, BlockDeviceType):
            return all([b1.connection == b2.connection,
                        b1.ephemeral_name == b2.ephemeral_name,
                        b1.no_device == b2.no_device,
                        b1.volume_id == b2.volume_id,
                        b1.snapshot_id == b2.snapshot_id,
                        b1.status == b2.status,
                        b1.attach_time == b2.attach_time,
                        b1.delete_on_termination == b2.delete_on_termination,
                        b1.size == b2.size,
                        b1.encrypted == b2.encrypted])

    def test_startElement_with_name_ebs_sets_and_returns_current_value(self):
        retval = self.block_device_mapping.startElement("ebs", None, None)
        assert self.block_device_type_eq(retval, BlockDeviceType(self.block_device_mapping))

    def test_startElement_with_name_virtualName_sets_and_returns_current_value(self):
        retval = self.block_device_mapping.startElement("virtualName", None, None)
        assert self.block_device_type_eq(retval, BlockDeviceType(self.block_device_mapping))

    def test_endElement_with_name_device_sets_current_name_dev_null(self):
        self.block_device_mapping.endElement("device", "/dev/null", None)
        self.assertEqual(self.block_device_mapping.current_name, "/dev/null")

    def test_endElement_with_name_device_sets_current_name(self):
        self.block_device_mapping.endElement("deviceName", "some device name", None)
        self.assertEqual(self.block_device_mapping.current_name, "some device name")

    def test_endElement_with_name_item_sets_current_name_key_to_current_value(self):
        self.block_device_mapping.current_name = "some name"
        self.block_device_mapping.current_value = "some value"
        self.block_device_mapping.endElement("item", "some item", None)
        self.assertEqual(self.block_device_mapping["some name"], "some value")


class TestLaunchConfiguration(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def default_body(self):
        # This is a dummy response
        return b"""
        <DescribeLaunchConfigurationsResponse>
        </DescribeLaunchConfigurationsResponse>
        """

    def test_run_instances_block_device_mapping(self):
        # Same as the test in ``unit/ec2/autoscale/test_group.py:TestLaunchConfiguration``,
        # but with modified request parameters (due to a mismatch between EC2 &
        # Autoscaling).
        self.set_http_response(status_code=200)
        dev_sdf = BlockDeviceType(snapshot_id='snap-12345')
        dev_sdg = BlockDeviceType(snapshot_id='snap-12346', delete_on_termination=True, encrypted=True)

        class OrderedBlockDeviceMapping(OrderedDict, BlockDeviceMapping):
            pass

        bdm = OrderedBlockDeviceMapping()
        bdm.update(OrderedDict((('/dev/sdf', dev_sdf), ('/dev/sdg', dev_sdg))))

        response = self.service_connection.run_instances(
            image_id='123456',
            instance_type='m1.large',
            security_groups=['group1', 'group2'],
            block_device_map=bdm
        )

        self.assert_request_parameters({
            'Action': 'RunInstances',
            'BlockDeviceMapping.1.DeviceName': '/dev/sdf',
            'BlockDeviceMapping.1.Ebs.DeleteOnTermination': 'false',
            'BlockDeviceMapping.1.Ebs.SnapshotId': 'snap-12345',
            'BlockDeviceMapping.2.DeviceName': '/dev/sdg',
            'BlockDeviceMapping.2.Ebs.DeleteOnTermination': 'true',
            'BlockDeviceMapping.2.Ebs.SnapshotId': 'snap-12346',
            'BlockDeviceMapping.2.Ebs.Encrypted': 'true',
            'ImageId': '123456',
            'InstanceType': 'm1.large',
            'MaxCount': 1,
            'MinCount': 1,
            'SecurityGroup.1': 'group1',
            'SecurityGroup.2': 'group2',
        }, ignore_params_values=[
            'Version', 'AWSAccessKeyId', 'SignatureMethod', 'SignatureVersion',
            'Timestamp'
        ])


if __name__ == "__main__":
    unittest.main()
