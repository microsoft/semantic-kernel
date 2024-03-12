from tests.compat import mock, unittest

from boto.ec2.address import Address


class AddressTest(unittest.TestCase):
    def setUp(self):
        self.address = Address()
        self.address.connection = mock.Mock()
        self.address.public_ip = "192.168.1.1"

    def check_that_attribute_has_been_set(self, name, value, attribute):
        self.address.endElement(name, value, None)
        self.assertEqual(getattr(self.address, attribute), value)

    def test_endElement_sets_correct_attributes_with_values(self):
        for arguments in [("publicIp", "192.168.1.1", "public_ip"),
                          ("instanceId", 1, "instance_id"),
                          ("domain", "some domain", "domain"),
                          ("allocationId", 1, "allocation_id"),
                          ("associationId", 1, "association_id"),
                          ("somethingRandom", "somethingRandom", "somethingRandom")]:
            self.check_that_attribute_has_been_set(arguments[0], arguments[1], arguments[2])

    def test_release_calls_connection_release_address_with_correct_args(self):
        self.address.release()
        self.address.connection.release_address.assert_called_with(
            public_ip="192.168.1.1",
            dry_run=False
        )

    def test_associate_calls_connection_associate_address_with_correct_args(self):
        self.address.associate(1)
        self.address.connection.associate_address.assert_called_with(
            instance_id=1,
            public_ip="192.168.1.1",
            allow_reassociation=False,
            network_interface_id=None,
            private_ip_address=None,
            dry_run=False
        )

    def test_disassociate_calls_connection_disassociate_address_with_correct_args(self):
        self.address.disassociate()
        self.address.connection.disassociate_address.assert_called_with(
            public_ip="192.168.1.1",
            dry_run=False
        )


class AddressWithAllocationTest(unittest.TestCase):
    def setUp(self):
        self.address = Address()
        self.address.connection = mock.Mock()
        self.address.public_ip = "192.168.1.1"
        self.address.allocation_id = "aid1"

    def check_that_attribute_has_been_set(self, name, value, attribute):
        self.address.endElement(name, value, None)
        self.assertEqual(getattr(self.address, attribute), value)

    def test_endElement_sets_correct_attributes_with_values(self):
        for arguments in [("publicIp", "192.168.1.1", "public_ip"),
                          ("instanceId", 1, "instance_id"),
                          ("domain", "some domain", "domain"),
                          ("allocationId", 1, "allocation_id"),
                          ("associationId", 1, "association_id"),
                          ("somethingRandom", "somethingRandom", "somethingRandom")]:
            self.check_that_attribute_has_been_set(arguments[0], arguments[1], arguments[2])

    def test_release_calls_connection_release_address_with_correct_args(self):
        self.address.release()
        self.address.connection.release_address.assert_called_with(
            allocation_id="aid1",
            dry_run=False
        )

    def test_associate_calls_connection_associate_address_with_correct_args(self):
        self.address.associate(1)
        self.address.connection.associate_address.assert_called_with(
            instance_id=1,
            public_ip="192.168.1.1",
            allocation_id="aid1",
            network_interface_id=None,
            private_ip_address=None,
            allow_reassociation=False,
            dry_run=False
        )

    def test_disassociate_calls_connection_disassociate_address_with_correct_args(self):
        self.address.disassociate()
        self.address.connection.disassociate_address.assert_called_with(
            public_ip="192.168.1.1",
            dry_run=False
        )

class AddressWithNetworkInterfaceTest(unittest.TestCase):
    def setUp(self):
        self.address = Address()
        self.address.connection = mock.Mock()
        self.address.public_ip = "192.168.1.1"
        self.address.allocation_id = "aid1"

    def check_that_attribute_has_been_set(self, name, value, attribute):
        self.address.endElement(name, value, None)
        self.assertEqual(getattr(self.address, attribute), value)

    def test_endElement_sets_correct_attributes_with_values(self):
        for arguments in [("publicIp", "192.168.1.1", "public_ip"),
                          ("instanceId", 1, "instance_id"),
                          ("domain", "some domain", "domain"),
                          ("allocationId", 1, "allocation_id"),
                          ("associationId", 1, "association_id"),
                          ("somethingRandom", "somethingRandom", "somethingRandom")]:
            self.check_that_attribute_has_been_set(arguments[0], arguments[1], arguments[2])


    def test_release_calls_connection_release_address_with_correct_args(self):
        self.address.release()
        self.address.connection.release_address.assert_called_with(
            allocation_id="aid1",
            dry_run=False
        )

    def test_associate_calls_connection_associate_address_with_correct_args(self):
        self.address.associate(network_interface_id=1)
        self.address.connection.associate_address.assert_called_with(
            instance_id=None,
            public_ip="192.168.1.1",
            network_interface_id=1,
            private_ip_address=None,
            allocation_id="aid1",
            allow_reassociation=False,
            dry_run=False
        )

    def test_disassociate_calls_connection_disassociate_address_with_correct_args(self):
        self.address.disassociate()
        self.address.connection.disassociate_address.assert_called_with(
            public_ip="192.168.1.1",
            dry_run=False
        )

if __name__ == "__main__":
    unittest.main()
