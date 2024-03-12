# Copyright (c) 2015 Shaun Brady.
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

import boto
import time
import json

from tests.compat import unittest


class TestIAMPolicy(unittest.TestCase):
    iam = True

    def test_policy_actions(self):
        # Test managed policy create/attach/detach/delete
        iam = boto.connect_iam()

        time_suffix = time.time()
        rolename = 'boto-test-role-%d' % time_suffix
        groupname = 'boto-test-group-%d' % time_suffix
        username = 'boto-test-user-%d' % time_suffix
        policyname = 'TestPolicyName-%d' % time_suffix

        iam.create_role(rolename)
        iam.create_group(groupname)
        iam.create_user(username)

        policy_doc = {
            "Version": "2012-10-17",
            "Id": "TestPermission",
            "Statement": [
                {
                  "Sid": "TestSid",
                  "Action": "s3:*",
                  "Effect": "Deny",
                  "Resource": "arn:aws:s3:::*"
                }
            ]
        }

        policy_json = json.dumps(policy_doc)

        # Create policy
        policy = iam.create_policy(policyname, policy_json)

        # Get it back, verify it is the same
        policy_copy = iam.get_policy(policy.arn)
        if not policy_copy.arn == policy.arn:
            raise Exception("Policies not equal.")

        # Show that policy is not attached
        result = iam.list_entities_for_policy(policy.arn)[
                'list_entities_for_policy_response'][
                'list_entities_for_policy_result']

        if not len(result['policy_roles']) == 0:
            raise Exception("Roles when not expected")

        if not len(result['policy_groups']) == 0:
            raise Exception("Groups when not expected")

        if not len(result['policy_users']) == 0:
            raise Exception("Users when not expected")

        # Attach the policy
        iam.attach_role_policy(policy.arn, rolename)
        iam.attach_group_policy(policy.arn, groupname)
        iam.attach_user_policy(policy.arn, username)

        # Show that policy is indeed attached
        result = iam.list_entities_for_policy(policy.arn)[
                'list_entities_for_policy_response'][
                'list_entities_for_policy_result']

        if not len(result['policy_roles']) == 1:
            raise Exception("Roles expected")

        if not len(result['policy_groups']) == 1:
            raise Exception("Groups expected")

        if not len(result['policy_users']) == 1:
            raise Exception("Users expected")

        # Detach the policy
        iam.detach_role_policy(policy.arn, rolename)
        iam.detach_group_policy(policy.arn, groupname)
        iam.detach_user_policy(policy.arn, username)

        # Clean up
        iam.delete_policy(policy.arn)
        iam.delete_role(rolename)
        iam.delete_user(username)
        iam.delete_group(groupname)
