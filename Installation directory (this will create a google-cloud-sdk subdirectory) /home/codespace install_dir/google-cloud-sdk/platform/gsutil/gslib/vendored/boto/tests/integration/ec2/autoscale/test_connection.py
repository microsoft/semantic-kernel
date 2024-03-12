# Copyright (c) 2011 Reza Lotun http://reza.lotun.name
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
Some unit tests for the AutoscaleConnection
"""

import time
from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2.autoscale.activity import Activity
from boto.ec2.autoscale.group import AutoScalingGroup, ProcessType
from boto.ec2.autoscale.launchconfig import LaunchConfiguration
from boto.ec2.autoscale.policy import AdjustmentType, MetricCollectionTypes, ScalingPolicy
from boto.ec2.autoscale.scheduled import ScheduledUpdateGroupAction
from boto.ec2.autoscale.instance import Instance
from boto.ec2.autoscale.tag import Tag
from tests.compat import unittest


class AutoscaleConnectionTest(unittest.TestCase):
    ec2 = True
    autoscale = True

    def test_basic(self):
        # NB: as it says on the tin these are really basic tests that only
        # (lightly) exercise read-only behaviour - and that's only if you
        # have any autoscale groups to introspect. It's useful, however, to
        # catch simple errors

        print('--- running %s tests ---' % self.__class__.__name__)
        c = AutoScaleConnection()

        self.assertTrue(repr(c).startswith('AutoScaleConnection'))

        groups = c.get_all_groups()
        for group in groups:
            self.assertIsInstance(group, AutoScalingGroup)

            # get activities
            activities = group.get_activities()

            for activity in activities:
                self.assertIsInstance(activity, Activity)

        # get launch configs
        configs = c.get_all_launch_configurations()
        for config in configs:
            self.assertIsInstance(config, LaunchConfiguration)

        # get policies
        policies = c.get_all_policies()
        for policy in policies:
            self.assertIsInstance(policy, ScalingPolicy)

        # get scheduled actions
        actions = c.get_all_scheduled_actions()
        for action in actions:
            self.assertIsInstance(action, ScheduledUpdateGroupAction)

        # get instances
        instances = c.get_all_autoscaling_instances()
        for instance in instances:
            self.assertIsInstance(instance, Instance)

        # get all scaling process types
        ptypes = c.get_all_scaling_process_types()
        for ptype in ptypes:
            self.assertTrue(ptype, ProcessType)

        # get adjustment types
        adjustments = c.get_all_adjustment_types()
        for adjustment in adjustments:
            self.assertIsInstance(adjustment, AdjustmentType)

        # get metrics collection types
        types = c.get_all_metric_collection_types()
        self.assertIsInstance(types, MetricCollectionTypes)

        # create the simplest possible AutoScale group
        # first create the launch configuration
        time_string = '%d' % int(time.time())
        lc_name = 'lc-%s' % time_string
        lc = LaunchConfiguration(name=lc_name, image_id='ami-2272864b',
                                 instance_type='t1.micro')
        c.create_launch_configuration(lc)
        found = False
        lcs = c.get_all_launch_configurations()
        for lc in lcs:
            if lc.name == lc_name:
                found = True
                break
        assert found

        # now create autoscaling group
        group_name = 'group-%s' % time_string
        group = AutoScalingGroup(name=group_name, launch_config=lc,
                                 availability_zones=['us-east-1a'],
                                 min_size=1, max_size=1)
        c.create_auto_scaling_group(group)
        found = False
        groups = c.get_all_groups()
        for group in groups:
            if group.name == group_name:
                found = True
                break
        assert found

        # now create a tag
        tag = Tag(key='foo', value='bar', resource_id=group_name,
                  propagate_at_launch=True)
        c.create_or_update_tags([tag])

        found = False
        tags = c.get_all_tags()
        for tag in tags:
            if tag.resource_id == group_name and tag.key == 'foo':
                found = True
                break
        assert found

        c.delete_tags([tag])

        # shutdown instances and wait for them to disappear
        group.shutdown_instances()
        instances = True
        while instances:
            time.sleep(5)
            groups = c.get_all_groups()
            for group in groups:
                if group.name == group_name:
                    if not group.instances:
                        instances = False

        group.delete()
        lc.delete()

        found = True
        while found:
            found = False
            time.sleep(5)
            tags = c.get_all_tags()
            for tag in tags:
                if tag.resource_id == group_name and tag.key == 'foo':
                    found = True

        assert not found

        print('--- tests completed ---')

    def test_ebs_optimized_regression(self):
        c = AutoScaleConnection()
        time_string = '%d' % int(time.time())
        lc_name = 'lc-%s' % time_string
        lc = LaunchConfiguration(
            name=lc_name,
            image_id='ami-2272864b',
            instance_type='t1.micro',
            ebs_optimized=True
        )
        # This failed due to the difference between native Python ``True/False``
        # & the expected string variants.
        c.create_launch_configuration(lc)
        self.addCleanup(c.delete_launch_configuration, lc_name)
