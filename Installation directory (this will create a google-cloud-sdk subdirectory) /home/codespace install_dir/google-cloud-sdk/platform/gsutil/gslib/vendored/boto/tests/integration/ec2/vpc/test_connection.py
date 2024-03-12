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
import time

import boto
from boto.compat import six
from tests.compat import unittest
from boto.ec2.networkinterface import NetworkInterfaceCollection
from boto.ec2.networkinterface import NetworkInterfaceSpecification
from boto.ec2.networkinterface import PrivateIPAddress


class TestVPCConnection(unittest.TestCase):

    def setUp(self):
        # Registry of instances to be removed
        self.instances = []
        # Registry for cleaning up the vpc after all instances are terminated
        # in the format [ ( func, (arg1, ... argn) ) ]
        self.post_terminate_cleanups = []

        self.api = boto.connect_vpc()
        self.vpc = self.api.create_vpc('10.0.0.0/16')

        # Need time for the VPC to be in place. :/
        time.sleep(5)
        self.subnet = self.api.create_subnet(self.vpc.id, '10.0.0.0/24')
        # Register the subnet to be deleted after instance termination
        self.post_terminate_cleanups.append((self.api.delete_subnet, (self.subnet.id,)))

        # Need time for the subnet to be in place.
        time.sleep(10)

    def post_terminate_cleanup(self):
        """Helper to run clean up tasks after instances are removed."""
        for fn, args in self.post_terminate_cleanups:
            fn(*args)
            # Give things time to catch up each time
            time.sleep(10)

        # Now finally delete the vpc
        if self.vpc:
            self.api.delete_vpc(self.vpc.id)

    def terminate_instances(self):
        """Helper to remove all instances and kick off additional cleanup
        once they are terminated.
        """
        for instance in self.instances:
            self.terminate_instance(instance)
        self.post_terminate_cleanup()

    def terminate_instance(self, instance):
        instance.terminate()
        for i in six.moves.range(300):
            instance.update()
            if instance.state == 'terminated':
                # Give it a litle more time to settle.
                time.sleep(30)
                return
            else:
                time.sleep(10)

    def delete_elastic_ip(self, eip):
        # Fetch a new copy of the eip so we're up to date
        new_eip = self.api.get_all_addresses([eip.public_ip])[0]
        if new_eip.association_id:
            new_eip.disassociate()
        new_eip.release()
        time.sleep(10)

    def test_multi_ip_create(self):
        interface = NetworkInterfaceSpecification(
            device_index=0, subnet_id=self.subnet.id,
            private_ip_address='10.0.0.21',
            description="This is a test interface using boto.",
            delete_on_termination=True, private_ip_addresses=[
                PrivateIPAddress(private_ip_address='10.0.0.22',
                                 primary=False),
                PrivateIPAddress(private_ip_address='10.0.0.23',
                                 primary=False),
                PrivateIPAddress(private_ip_address='10.0.0.24',
                                 primary=False)])
        interfaces = NetworkInterfaceCollection(interface)

        reservation = self.api.run_instances(image_id='ami-a0cd60c9', instance_type='m1.small',
                                             network_interfaces=interfaces)
        # Give it a few seconds to start up.
        time.sleep(10)
        instance = reservation.instances[0]
        self.addCleanup(self.terminate_instance, instance)
        retrieved = self.api.get_all_reservations(instance_ids=[instance.id])
        self.assertEqual(len(retrieved), 1)
        retrieved_instances = retrieved[0].instances
        self.assertEqual(len(retrieved_instances), 1)
        retrieved_instance = retrieved_instances[0]

        self.assertEqual(len(retrieved_instance.interfaces), 1)
        interface = retrieved_instance.interfaces[0]

        private_ip_addresses = interface.private_ip_addresses
        self.assertEqual(len(private_ip_addresses), 4)
        self.assertEqual(private_ip_addresses[0].private_ip_address,
                         '10.0.0.21')
        self.assertEqual(private_ip_addresses[0].primary, True)
        self.assertEqual(private_ip_addresses[1].private_ip_address,
                         '10.0.0.22')
        self.assertEqual(private_ip_addresses[2].private_ip_address,
                         '10.0.0.23')
        self.assertEqual(private_ip_addresses[3].private_ip_address,
                         '10.0.0.24')

    def test_associate_public_ip(self):
        # Supplying basically nothing ought to work.
        interface = NetworkInterfaceSpecification(
            associate_public_ip_address=True,
            subnet_id=self.subnet.id,
            # Just for testing.
            delete_on_termination=True
        )
        interfaces = NetworkInterfaceCollection(interface)

        reservation = self.api.run_instances(
            image_id='ami-a0cd60c9',
            instance_type='m1.small',
            network_interfaces=interfaces
        )
        instance = reservation.instances[0]
        self.instances.append(instance)
        self.addCleanup(self.terminate_instances)

        # Give it a **LONG** time to start up.
        # Because the public IP won't be there right away.
        time.sleep(60)

        retrieved = self.api.get_all_reservations(
            instance_ids=[
                instance.id
            ]
        )
        self.assertEqual(len(retrieved), 1)
        retrieved_instances = retrieved[0].instances
        self.assertEqual(len(retrieved_instances), 1)
        retrieved_instance = retrieved_instances[0]

        self.assertEqual(len(retrieved_instance.interfaces), 1)
        interface = retrieved_instance.interfaces[0]

        # There ought to be a public IP there.
        # We can't reason about the IP itself, so just make sure it vaguely
        # resembles an IP (& isn't empty/``None``)...
        self.assertTrue(interface.publicIp.count('.') >= 3)

    def test_associate_elastic_ip(self):
        interface = NetworkInterfaceSpecification(
            associate_public_ip_address=False,
            subnet_id=self.subnet.id,
            # Just for testing.
            delete_on_termination=True
        )
        interfaces = NetworkInterfaceCollection(interface)

        reservation = self.api.run_instances(
            image_id='ami-a0cd60c9',
            instance_type='m1.small',
            network_interfaces=interfaces
        )
        instance = reservation.instances[0]
        # Register instance to be removed
        self.instances.append(instance)
        # Add terminate instances helper as cleanup command
        self.addCleanup(self.terminate_instances)

        # Create an internet gateway so we can attach an eip
        igw = self.api.create_internet_gateway()
        # Wait on gateway before attaching
        time.sleep(5)
        # Attach and register clean up tasks
        self.api.attach_internet_gateway(igw.id, self.vpc.id)
        self.post_terminate_cleanups.append((self.api.detach_internet_gateway, (igw.id, self.vpc.id)))
        self.post_terminate_cleanups.append((self.api.delete_internet_gateway, (igw.id,)))

        # Allocate an elastic ip to this vpc
        eip = self.api.allocate_address('vpc')
        self.post_terminate_cleanups.append((self.delete_elastic_ip, (eip,)))

        # Wait on instance and eip then try to associate directly to instance
        time.sleep(60)
        eip.associate(instance.id)


if __name__ == '__main__':
    unittest.main()
