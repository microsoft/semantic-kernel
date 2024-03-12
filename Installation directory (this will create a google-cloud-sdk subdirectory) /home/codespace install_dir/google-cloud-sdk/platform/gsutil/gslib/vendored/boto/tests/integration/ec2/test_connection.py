# Copyright (c) 2006-2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2009, Eucalyptus Systems, Inc.
# All rights reserved.
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

"""
Some unit tests for the EC2Connection
"""

import unittest
import time
import telnetlib
import socket

from nose.plugins.attrib import attr
from boto.ec2.connection import EC2Connection
from boto.exception import EC2ResponseError
import boto.ec2


class EC2ConnectionTest(unittest.TestCase):
    ec2 = True

    @attr('notdefault')
    def test_launch_permissions(self):
        # this is my user_id, if you want to run these tests you should
        # replace this with yours or they won't work
        user_id = '963068290131'
        print('--- running EC2Connection tests ---')
        c = EC2Connection()
        # get list of private AMI's
        rs = c.get_all_images(owners=[user_id])
        assert len(rs) > 0
        # now pick the first one
        image = rs[0]
        # temporarily make this image runnable by everyone
        status = image.set_launch_permissions(group_names=['all'])
        assert status
        d = image.get_launch_permissions()
        assert 'groups' in d
        assert len(d['groups']) > 0
        # now remove that permission
        status = image.remove_launch_permissions(group_names=['all'])
        assert status
        time.sleep(10)
        d = image.get_launch_permissions()
        assert 'groups' not in d

    def test_1_basic(self):
        # create 2 new security groups
        c = EC2Connection()
        group1_name = 'test-%d' % int(time.time())
        group_desc = 'This is a security group created during unit testing'
        group1 = c.create_security_group(group1_name, group_desc)
        time.sleep(2)
        group2_name = 'test-%d' % int(time.time())
        group_desc = 'This is a security group created during unit testing'
        group2 = c.create_security_group(group2_name, group_desc)
        # now get a listing of all security groups and look for our new one
        rs = c.get_all_security_groups()
        found = False
        for g in rs:
            if g.name == group1_name:
                found = True
        assert found
        # now pass arg to filter results to only our new group
        rs = c.get_all_security_groups([group1_name])
        assert len(rs) == 1
        # try some group to group authorizations/revocations
        # first try the old style
        status = c.authorize_security_group(group1.name,
                                            group2.name,
                                            group2.owner_id)
        assert status
        status = c.revoke_security_group(group1.name,
                                         group2.name,
                                         group2.owner_id)
        assert status
        # now try specifying a specific port
        status = c.authorize_security_group(group1.name,
                                            group2.name,
                                            group2.owner_id,
                                            'tcp', 22, 22)
        assert status
        status = c.revoke_security_group(group1.name,
                                         group2.name,
                                         group2.owner_id,
                                         'tcp', 22, 22)
        assert status

        # now delete the second security group
        status = c.delete_security_group(group2_name)
        # now make sure it's really gone
        rs = c.get_all_security_groups()
        found = False
        for g in rs:
            if g.name == group2_name:
                found = True
        assert not found

        group = group1

        # now try to launch apache image with our new security group
        rs = c.get_all_images()
        img_loc = 'ec2-public-images/fedora-core4-apache.manifest.xml'
        for image in rs:
            if image.location == img_loc:
                break
        reservation = image.run(security_groups=[group.name])
        instance = reservation.instances[0]
        while instance.state != 'running':
            print('\tinstance is %s' % instance.state)
            time.sleep(30)
            instance.update()
        # instance in now running, try to telnet to port 80
        t = telnetlib.Telnet()
        try:
            t.open(instance.dns_name, 80)
        except socket.error:
            pass
        # now open up port 80 and try again, it should work
        group.authorize('tcp', 80, 80, '0.0.0.0/0')
        t.open(instance.dns_name, 80)
        t.close()
        # now revoke authorization and try again
        group.revoke('tcp', 80, 80, '0.0.0.0/0')
        try:
            t.open(instance.dns_name, 80)
        except socket.error:
            pass
        # now kill the instance and delete the security group
        instance.terminate()

        # check that state and previous_state have updated
        assert instance.state == 'shutting-down'
        assert instance.state_code == 32
        assert instance.previous_state == 'running'
        assert instance.previous_state_code == 16

        # unfortunately, I can't delete the sg within this script
        #sg.delete()

        # create a new key pair
        key_name = 'test-%d' % int(time.time())
        status = c.create_key_pair(key_name)
        assert status
        # now get a listing of all key pairs and look for our new one
        rs = c.get_all_key_pairs()
        found = False
        for k in rs:
            if k.name == key_name:
                found = True
        assert found
        # now pass arg to filter results to only our new key pair
        rs = c.get_all_key_pairs([key_name])
        assert len(rs) == 1
        key_pair = rs[0]
        # now delete the key pair
        status = c.delete_key_pair(key_name)
        # now make sure it's really gone
        rs = c.get_all_key_pairs()
        found = False
        for k in rs:
            if k.name == key_name:
                found = True
        assert not found

        # short test around Paid AMI capability
        demo_paid_ami_id = 'ami-bd9d78d4'
        demo_paid_ami_product_code = 'A79EC0DB'
        l = c.get_all_images([demo_paid_ami_id])
        assert len(l) == 1
        assert len(l[0].product_codes) == 1
        assert l[0].product_codes[0] == demo_paid_ami_product_code

        print('--- tests completed ---')

    def test_dry_run(self):
        c = EC2Connection()
        dry_run_msg = 'Request would have succeeded, but DryRun flag is set.'

        try:
            rs = c.get_all_images(dry_run=True)
            self.fail("Should have gotten an exception")
        except EC2ResponseError as e:
            self.assertTrue(dry_run_msg in str(e))

        try:
            rs = c.run_instances(
                image_id='ami-a0cd60c9',
                instance_type='m1.small',
                dry_run=True
            )
            self.fail("Should have gotten an exception")
        except EC2ResponseError as e:
            self.assertTrue(dry_run_msg in str(e))

        # Need an actual instance for the rest of this...
        rs = c.run_instances(
            image_id='ami-a0cd60c9',
            instance_type='m1.small'
        )
        time.sleep(120)

        try:
            rs = c.stop_instances(
                instance_ids=[rs.instances[0].id],
                dry_run=True
            )
            self.fail("Should have gotten an exception")
        except EC2ResponseError as e:
            self.assertTrue(dry_run_msg in str(e))

        try:
            rs = c.terminate_instances(
                instance_ids=[rs.instances[0].id],
                dry_run=True
            )
            self.fail("Should have gotten an exception")
        except EC2ResponseError as e:
            self.assertTrue(dry_run_msg in str(e))

        # And kill it.
        rs.instances[0].terminate()

    def test_can_get_all_instances_sigv4(self):
        connection = boto.ec2.connect_to_region('eu-central-1')
        self.assertTrue(isinstance(connection.get_all_instances(), list))
