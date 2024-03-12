# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Integration tests for the iam command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from collections import defaultdict
import json
import os
import subprocess

from gslib.commands import iam
from gslib.exception import CommandException
from gslib.project_id import PopulateProjectId
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import GenerationFromURI as urigen
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import unittest
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import shim_util
from gslib.utils.constants import UTF8
from gslib.utils.iam_helper import BindingsMessageToUpdateDict
from gslib.utils.iam_helper import BindingsDictToUpdateDict
from gslib.utils.iam_helper import BindingStringToTuple as bstt
from gslib.utils.iam_helper import DiffBindings
from gslib.utils.iam_helper import IsEqualBindings
from gslib.utils.iam_helper import PatchBindings
from gslib.utils.retry_util import Retry
from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

bvle = apitools_messages.Policy.BindingsValueListEntry

# Feature iam_bucket_roles must be turned on in bigstore dev config for setting
# the new IAM policies on buckets.
IAM_BUCKET_READ_ROLE_ABBREV = 'legacyBucketReader'
IAM_BUCKET_READ_ROLE = 'roles/storage.%s' % IAM_BUCKET_READ_ROLE_ABBREV
# GCS IAM does not currently support new object-level roles.
IAM_OBJECT_READ_ROLE = 'roles/storage.legacyObjectReader'
IAM_OBJECT_VIEWER_ROLE = 'roles/storage.objectViewer'

TEST_CONDITION_DESCRIPTION = 'Description for our test condition.'
TEST_CONDITION_EXPR_RESOURCE_IS_OBJECT = (
    'resource.type == "google.cloud.storage.Object"')
TEST_CONDITION_TITLE = 'Test Condition Title'


def gen_binding(role, members=None, condition=None):
  """Generate the "bindings" portion of an IAM Policy dictionary.

  Generates list of dicts which each represent a
  storage_v1_messages.Policy.BindingsValueListEntry object. The list will
  contain a single dict which has attributes corresponding to arguments passed
  to this method.

  Args:
    role: (str) An IAM policy role (e.g. "roles/storage.objectViewer"). Fully
        specified in BindingsValueListEntry.
    members: (List[str]) A list of members (e.g. ["user:foo@bar.com"]). If None,
        bind to ["allUsers"]. Fully specified in BindingsValueListEntry.
    condition: (Dict) A dictionary representing the JSON used to define a
        binding condition, containing the keys "description", "expression", and
        "title".

  Returns:
    (List[Dict[str, Any]]) A Python representation of the "bindings" portion of
    an IAM Policy.
  """
  binding = {
      'members': ['allUsers'] if members is None else members,
      'role': role,
  }
  if condition:
    binding['condition'] = condition
  return [binding]


def patch_binding(policy, role, new_policy):
  """Returns a patched Python object representation of a Policy.

  Given replaces the original role:members binding in policy with new_policy.

  Args:
    policy: Python dict representation of a Policy instance.
    role: An IAM policy role (e.g. "roles/storage.objectViewer"). Fully
          specified in BindingsValueListEntry.
    new_policy: A Python dict representation of a Policy instance, with a
                single BindingsValueListEntry entry.

  Returns:
    A Python dict representation of the patched IAM Policy object.
  """
  bindings = [
      b for b in policy.get('bindings', []) if b.get('role', '') != role
  ]
  bindings.extend(new_policy)
  policy = dict(policy)
  policy['bindings'] = bindings
  return policy


class TestIamIntegration(testcase.GsUtilIntegrationTestCase):
  """Superclass for iam integration test cases."""

  def assertEqualsPoliciesString(self, a, b):
    """Asserts two serialized policy bindings are equal."""
    expected = [
        bvle(members=binding_dict['members'], role=binding_dict['role'])
        for binding_dict in json.loads(a)['bindings']
    ]
    result = [
        bvle(members=binding_dict['members'], role=binding_dict['role'])
        for binding_dict in json.loads(b)['bindings']
    ]
    self.assertTrue(IsEqualBindings(expected, result))


@SkipForS3('Tests use GS IAM model.')
@SkipForXML('XML IAM control is not supported.')
class TestIamHelpers(testcase.GsUtilUnitTestCase):
  """Unit tests for iam command helper."""

  def test_convert_bindings_simple(self):
    """Tests that Policy.bindings lists are converted to dicts properly."""
    self.assertEqual(BindingsMessageToUpdateDict([]), defaultdict(set))
    expected = defaultdict(set, {'x': set(['y'])})
    self.assertEqual(
        BindingsMessageToUpdateDict([bvle(role='x', members=['y'])]), expected)

  def test_convert_bindings_duplicates(self):
    """Test that role and member duplication are converted correctly."""
    expected = defaultdict(set, {'x': set(['y', 'z'])})
    duplicate_roles = [
        bvle(role='x', members=['y']),
        bvle(role='x', members=['z'])
    ]
    duplicate_members = [
        bvle(role='x', members=['z', 'y']),
        bvle(role='x', members=['z'])
    ]
    self.assertEqual(BindingsMessageToUpdateDict(duplicate_roles), expected)
    self.assertEqual(BindingsMessageToUpdateDict(duplicate_members), expected)

  def test_convert_bindings_dict_simple(self):
    """Tests that Policy.bindings lists are converted to dicts properly."""
    self.assertEqual(BindingsDictToUpdateDict([]), defaultdict(set))
    expected = defaultdict(set, {'x': set(['y'])})
    self.assertEqual(
        BindingsDictToUpdateDict([{
            'role': 'x',
            'members': ['y']
        }]), expected)

  def test_convert_bindings_dict_duplicates(self):
    """Test that role and member duplication are converted correctly."""
    expected = defaultdict(set, {'x': set(['y', 'z'])})
    duplicate_roles = [{
        'role': 'x',
        'members': ['y']
    }, {
        'role': 'x',
        'members': ['z']
    }]
    duplicate_members = [{
        'role': 'x',
        'members': ['z', 'y']
    }, {
        'role': 'x',
        'members': ['z']
    }]
    self.assertEqual(BindingsDictToUpdateDict(duplicate_roles), expected)
    self.assertEqual(BindingsDictToUpdateDict(duplicate_members), expected)

  def test_equality_bindings_literal(self):
    """Tests an easy case of identical bindings."""
    bindings = [bvle(role='x', members=['y'])]
    self.assertTrue(IsEqualBindings([], []))
    self.assertTrue(IsEqualBindings(bindings, bindings))

  def test_equality_bindings_extra_roles(self):
    """Tests bindings equality when duplicate roles are added."""
    bindings = [bvle(role='x', members=['x', 'y'])]
    bindings2 = bindings * 2
    bindings3 = [
        bvle(role='x', members=['y']),
        bvle(role='x', members=['x']),
    ]
    self.assertTrue(IsEqualBindings(bindings, bindings2))
    self.assertTrue(IsEqualBindings(bindings, bindings3))

  def test_diff_bindings_add_role(self):
    """Tests simple grant behavior of Policy.bindings diff."""
    expected = [bvle(role='x', members=['y'])]
    (granted, removed) = DiffBindings([], expected)
    self.assertEqual(granted.bindings, expected)
    self.assertEqual(removed.bindings, [])

  def test_diff_bindings_drop_role(self):
    """Tests simple remove behavior of Policy.bindings diff."""
    expected = [bvle(role='x', members=['y'])]
    (granted, removed) = DiffBindings(expected, [])
    self.assertEqual(granted.bindings, [])
    self.assertEqual(removed.bindings, expected)

  def test_diff_bindings_swap_role(self):
    """Tests expected behavior of switching a role."""
    old = [bvle(role='x', members=['y'])]
    new = [bvle(role='a', members=['b'])]
    (granted, removed) = DiffBindings(old, new)
    self.assertEqual(granted.bindings, new)
    self.assertEqual(removed.bindings, old)

  def test_diff_bindings_add_member(self):
    """Tests expected behavior of adding a member to a role."""
    old = [bvle(role='x', members=['y'])]
    new = [bvle(role='x', members=['z', 'y'])]
    expected = [bvle(role='x', members=['z'])]
    (granted, removed) = DiffBindings(old, new)
    self.assertEqual(granted.bindings, expected)
    self.assertEqual(removed.bindings, [])

  def test_diff_bindings_drop_member(self):
    """Tests expected behavior of dropping a member from a role."""
    old = [bvle(role='x', members=['z', 'y'])]
    new = [bvle(role='x', members=['y'])]
    expected = [bvle(role='x', members=['z'])]
    (granted, removed) = DiffBindings(old, new)
    self.assertEqual(granted.bindings, [])
    self.assertEqual(removed.bindings, expected)

  def test_diff_bindings_swap_member(self):
    """Tests expected behavior of switching a member in a role."""
    old = [bvle(role='x', members=['z'])]
    new = [bvle(role='x', members=['y'])]
    (granted, removed) = DiffBindings(old, new)
    self.assertEqual(granted.bindings, new)
    self.assertEqual(removed.bindings, old)

  def test_patch_bindings_grant(self):
    """Tests patching a grant binding."""
    base_list = [
        bvle(role='a', members=['user:foo@bar.com']),
        bvle(role='b', members=['user:foo@bar.com']),
        bvle(role='c', members=['user:foo@bar.com']),
    ]
    base = BindingsMessageToUpdateDict(base_list)
    diff_list = [
        bvle(role='d', members=['user:foo@bar.com']),
    ]
    diff = BindingsMessageToUpdateDict(diff_list)
    expected = BindingsMessageToUpdateDict(base_list + diff_list)
    res = PatchBindings(base, diff, True)
    self.assertEqual(res, expected)

  def test_patch_bindings_remove(self):
    """Tests patching a remove binding."""
    base = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='a'),
        bvle(members=['user:foo@bar.com'], role='b'),
        bvle(members=['user:foo@bar.com'], role='c'),
    ])
    diff = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='a'),
    ])
    expected = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='b'),
        bvle(members=['user:foo@bar.com'], role='c'),
    ])

    res = PatchBindings(base, diff, False)
    self.assertEqual(res, expected)

  def test_patch_bindings_remove_all(self):
    """Tests removing all roles from a member."""
    base = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='a'),
        bvle(members=['user:foo@bar.com'], role='b'),
        bvle(members=['user:foo@bar.com'], role='c'),
    ])
    diff = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role=''),
    ])
    res = PatchBindings(base, diff, False)
    self.assertEqual(res, {})

    diff = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='a'),
        bvle(members=['user:foo@bar.com'], role='b'),
        bvle(members=['user:foo@bar.com'], role='c'),
    ])

    res = PatchBindings(base, diff, False)
    self.assertEqual(res, {})

  def test_patch_bindings_multiple_users(self):
    """Tests expected behavior when multiple users exist."""
    expected = BindingsMessageToUpdateDict([
        bvle(members=['user:fii@bar.com'], role='b'),
    ])
    base = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='a'),
        bvle(members=['user:foo@bar.com', 'user:fii@bar.com'], role='b'),
        bvle(members=['user:foo@bar.com'], role='c'),
    ])
    diff = BindingsMessageToUpdateDict([
        bvle(members=['user:foo@bar.com'], role='a'),
        bvle(members=['user:foo@bar.com'], role='b'),
        bvle(members=['user:foo@bar.com'], role='c'),
    ])
    res = PatchBindings(base, diff, False)
    self.assertEqual(res, expected)

  def test_patch_bindings_grant_all_users(self):
    """Tests a public member grant."""
    base = BindingsMessageToUpdateDict([
        bvle(role='a', members=['user:foo@bar.com']),
        bvle(role='b', members=['user:foo@bar.com']),
        bvle(role='c', members=['user:foo@bar.com']),
    ])
    diff = BindingsMessageToUpdateDict([
        bvle(role='a', members=['allUsers']),
    ])
    expected = BindingsMessageToUpdateDict([
        bvle(role='a', members=['allUsers', 'user:foo@bar.com']),
        bvle(role='b', members=['user:foo@bar.com']),
        bvle(role='c', members=['user:foo@bar.com']),
    ])

    res = PatchBindings(base, diff, True)
    self.assertEqual(res, expected)

  def test_patch_bindings_public_member_overwrite(self):
    """Tests public member vs. public member interaction."""
    base_list = [
        bvle(role='a', members=['allUsers']),
    ]
    base = BindingsMessageToUpdateDict(base_list)
    diff_list = [
        bvle(role='a', members=['allAuthenticatedUsers']),
    ]
    diff = BindingsMessageToUpdateDict(diff_list)

    res = PatchBindings(base, diff, True)
    self.assertEqual(res, BindingsMessageToUpdateDict(base_list + diff_list))

  def test_valid_public_member_single_role(self):
    """Tests parsing single role (case insensitive)."""
    (_, bindings) = bstt(True, 'allusers:admin')
    self.assertEqual(len(bindings), 1)
    self.assertIn({
        'members': ['allUsers'],
        'role': 'roles/storage.admin'
    }, bindings)

  def test_grant_no_role_error(self):
    """Tests that an error is raised when no role is specified for a grant."""
    with self.assertRaises(CommandException):
      bstt(True, 'allUsers')
    with self.assertRaises(CommandException):
      bstt(True, 'user:foo@bar.com')
    with self.assertRaises(CommandException):
      bstt(True, 'user:foo@bar.com:')
    with self.assertRaises(CommandException):
      bstt(True, 'deleted:user:foo@bar.com?uid=1234:')

  def test_remove_all_roles(self):
    """Tests parsing a -d allUsers or -d user:foo@bar.com request."""
    # Input specifies remove all roles from allUsers.
    (is_grant, bindings) = bstt(False, 'allUsers')
    self.assertEqual(len(bindings), 1)
    self.assertIn({'members': ['allUsers'], 'role': ''}, bindings)
    self.assertEqual((is_grant, bindings), bstt(False, 'allUsers:'))

    # Input specifies remove all roles from a user.
    (_, bindings) = bstt(False, 'user:foo@bar.com')
    self.assertEqual(len(bindings), 1)

  def test_valid_multiple_roles(self):
    """Tests parsing of multiple roles bound to one user."""
    (_, bindings) = bstt(True, 'allUsers:a,b,c,roles/custom')
    self.assertEqual(len(bindings), 4)
    self.assertIn({
        'members': ['allUsers'],
        'role': 'roles/storage.a'
    }, bindings)
    self.assertIn({
        'members': ['allUsers'],
        'role': 'roles/storage.b'
    }, bindings)
    self.assertIn({
        'members': ['allUsers'],
        'role': 'roles/storage.c'
    }, bindings)
    self.assertIn({'members': ['allUsers'], 'role': 'roles/custom'}, bindings)

  def test_valid_custom_roles(self):
    """Tests parsing of custom roles bound to one user."""
    (_, bindings) = bstt(True, 'user:foo@bar.com:roles/custom1,roles/custom2')
    self.assertEqual(len(bindings), 2)
    self.assertIn({
        'members': ['user:foo@bar.com'],
        'role': 'roles/custom1'
    }, bindings)
    self.assertIn({
        'members': ['user:foo@bar.com'],
        'role': 'roles/custom2'
    }, bindings)

  def test_valid_member(self):
    """Tests member parsing (case insensitive)."""
    (_, bindings) = bstt(True, 'User:foo@bar.com:admin')
    self.assertEqual(len(bindings), 1)
    self.assertIn(
        {
            'members': ['user:foo@bar.com'],
            'role': 'roles/storage.admin'
        }, bindings)

  def test_valid_deleted_member(self):
    """Tests deleted member parsing (case insensitive)."""
    (_, bindings) = bstt(False, 'Deleted:User:foo@bar.com?uid=123')
    self.assertEqual(len(bindings), 1)
    self.assertIn({
        'members': ['deleted:user:foo@bar.com?uid=123'],
        'role': ''
    }, bindings)
    (_, bindings) = bstt(True, 'deleted:User:foo@bar.com?uid=123:admin')
    self.assertEqual(len(bindings), 1)
    self.assertIn(
        {
            'members': ['deleted:user:foo@bar.com?uid=123'],
            'role': 'roles/storage.admin'
        }, bindings)
    # These emails can actually have multiple query params
    (_, bindings) = bstt(
        True,
        'deleted:user:foo@bar.com?query=param,uid=123?uid=456:admin,admin2')
    self.assertEqual(len(bindings), 2)
    self.assertIn(
        {
            'members': ['deleted:user:foo@bar.com?query=param,uid=123?uid=456'],
            'role': 'roles/storage.admin'
        }, bindings)
    self.assertIn(
        {
            'members': ['deleted:user:foo@bar.com?query=param,uid=123?uid=456'],
            'role': 'roles/storage.admin2'
        }, bindings)

  def test_duplicate_roles(self):
    """Tests that duplicate roles are ignored."""
    (_, bindings) = bstt(True, 'allUsers:a,a')
    self.assertEqual(len(bindings), 1)
    self.assertIn({
        'members': ['allUsers'],
        'role': 'roles/storage.a'
    }, bindings)

  def test_removing_project_convenience_groups(self):
    """Tests that project convenience roles can be removed."""
    (_, bindings) = bstt(False, 'projectViewer:123424:admin')
    self.assertEqual(len(bindings), 1)
    self.assertIn(
        {
            'members': ['projectViewer:123424'],
            'role': 'roles/storage.admin'
        }, bindings)
    (_, bindings) = bstt(False, 'projectViewer:123424')
    self.assertEqual(len(bindings), 1)
    self.assertIn({'members': ['projectViewer:123424'], 'role': ''}, bindings)

  def test_adding_project_convenience_groups(self):
    """Tests that project convenience roles cannot be added."""
    with self.assertRaises(CommandException):
      bstt(True, 'projectViewer:123424:admin')

  def test_invalid_input(self):
    """Tests invalid input handling."""
    with self.assertRaises(CommandException):
      bstt(True, 'non_valid_public_member:role')
    with self.assertRaises(CommandException):
      bstt(True, 'non_valid_type:id:role')
    with self.assertRaises(CommandException):
      bstt(True, 'user:r')
    with self.assertRaises(CommandException):
      bstt(True, 'deleted:user')
    with self.assertRaises(CommandException):
      bstt(True, 'deleted:not_a_type')
    with self.assertRaises(CommandException):
      bstt(True, 'deleted:user:foo@no_uid_suffix')

  def test_invalid_n_args(self):
    """Tests invalid input due to too many colons."""
    with self.assertRaises(CommandException):
      bstt(True, 'allUsers:some_id:some_role')
    with self.assertRaises(CommandException):
      bstt(True, 'user:foo@bar.com:r:nonsense')
    with self.assertRaises(CommandException):
      bstt(True, 'deleted:user:foo@bar.com?uid=1234:r:nonsense')


@SkipForS3('Tests use GS IAM model.')
@SkipForXML('XML IAM control is not supported.')
class TestIamCh(TestIamIntegration):
  """Integration tests for iam ch command."""

  def setUp(self):
    super(TestIamCh, self).setUp()
    self.bucket = self.CreateBucket()
    self.bucket2 = self.CreateBucket()
    self.object = self.CreateObject(bucket_uri=self.bucket, contents=b'foo')
    self.object2 = self.CreateObject(bucket_uri=self.bucket, contents=b'bar')

    self.bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                            return_stdout=True)
    self.object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                            return_stdout=True)
    self.object2_iam_string = self.RunGsUtil(['iam', 'get', self.object2.uri],
                                             return_stdout=True)

    self.user = 'user:foo@bar.com'
    self.user2 = 'user:bar@foo.com'

  def test_patch_no_role(self):
    """Tests expected failure if no bindings are listed."""
    stderr = self.RunGsUtil(['iam', 'ch', self.bucket.uri],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('CommandException', stderr)

  def test_raises_error_message_for_d_flag_missing_argument(self):
    """Tests expected failure if no bindings are listed."""
    stderr = self.RunGsUtil(
        ['iam', 'ch',
         '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), '-d'],
        return_stderr=True,
        expected_status=1)
    self.assertIn(
        'A -d flag is missing an argument specifying bindings to remove.',
        stderr)

  def test_path_mix_of_buckets_and_objects(self):
    """Tests expected failure if both buckets and objects are provided."""
    stderr = self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri,
        self.object.uri
    ],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('CommandException', stderr)

  def test_path_file_url(self):
    """Tests expected failure is caught when a file url is provided."""
    stderr = self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), 'file://somefile'
    ],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('AttributeError', stderr)

  def test_patch_single_grant_single_bucket(self):
    """Tests granting single role."""
    self.assertHasNo(self.bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)

  def test_patch_repeated_grant(self):
    """Granting multiple times for the same member will have no effect."""
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)

  def test_patch_single_remove_single_bucket(self):
    """Tests removing a single role."""
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])
    self.RunGsUtil([
        'iam', 'ch', '-d',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHasNo(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)

  def test_patch_null_remove(self):
    """Removing a non-existent binding will have no effect."""
    self.RunGsUtil([
        'iam', 'ch', '-d',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHasNo(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)
    self.assertEqualsPoliciesString(bucket_iam_string, self.bucket_iam_string)

  def test_patch_mixed_grant_remove_single_bucket(self):
    """Tests that mixing grant and remove requests will succeed."""
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user2, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), '-d',
        '%s:%s' % (self.user2, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)
    self.assertHasNo(bucket_iam_string, self.user2, IAM_BUCKET_READ_ROLE)

  def test_patch_public_grant_single_bucket(self):
    """Test public grant request interacts properly with existing members."""
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])
    self.RunGsUtil([
        'iam', 'ch',
        'allUsers:%s' % IAM_BUCKET_READ_ROLE_ABBREV, self.bucket.uri
    ])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHas(bucket_iam_string, 'allUsers', IAM_BUCKET_READ_ROLE)
    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)

  def test_patch_remove_all_roles(self):
    """Remove with no roles specified will remove member from all bindings."""
    self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri
    ])
    self.RunGsUtil(['iam', 'ch', '-d', self.user, self.bucket.uri])

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHasNo(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)

  def test_patch_single_object(self):
    """Tests object IAM patch behavior."""
    self.assertHasNo(self.object_iam_string, self.user, IAM_OBJECT_READ_ROLE)
    self.RunGsUtil(
        ['iam', 'ch',
         '%s:legacyObjectReader' % self.user, self.object.uri])

    object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                       return_stdout=True)
    self.assertHas(object_iam_string, self.user, IAM_OBJECT_READ_ROLE)

  def test_patch_multithreaded_single_object(self):
    """Tests the edge-case behavior of multithreaded execution."""
    self.assertHasNo(self.object_iam_string, self.user, IAM_OBJECT_READ_ROLE)
    self.RunGsUtil([
        '-m', 'iam', 'ch',
        '%s:legacyObjectReader' % self.user, self.object.uri
    ])

    object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                       return_stdout=True)
    self.assertHas(object_iam_string, self.user, IAM_OBJECT_READ_ROLE)

  def test_patch_invalid_input(self):
    """Tests that listing bindings after a bucket will throw an error."""
    stderr = self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri,
        '%s:%s' % (self.user2, IAM_BUCKET_READ_ROLE_ABBREV)
    ],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('CommandException', stderr)

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)
    self.assertHasNo(bucket_iam_string, self.user2, IAM_BUCKET_READ_ROLE)

  def test_patch_disallowed_binding_type(self):
    """Tests that we disallow certain binding types with appropriate err."""
    stderr = self.RunGsUtil(
        ['iam', 'ch', 'projectOwner:my-project:admin', self.bucket.uri],
        return_stderr=True,
        expected_status=1)
    self.assertIn('not supported', stderr)

  def test_patch_remove_disallowed_binding_type(self):
    """Tests that we can remove project convenience values."""
    # Set up the bucket to include a disallowed member which we can then remove.
    disallowed_member = 'projectViewer:%s' % PopulateProjectId()
    policy_file_path = self.CreateTempFile(contents=json.dumps(
        patch_binding(
            json.loads(self.bucket_iam_string), IAM_OBJECT_READ_ROLE,
            gen_binding(IAM_OBJECT_READ_ROLE, members=[disallowed_member
                                                      ]))).encode(UTF8))
    self.RunGsUtil(['iam', 'set', policy_file_path, self.bucket.uri])
    # Confirm the disallowed member was actually added.
    iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                return_stdout=True)
    self.assertHas(iam_string, disallowed_member, IAM_OBJECT_READ_ROLE)
    # Use iam ch to remove the disallowed member.
    self.RunGsUtil(['iam', 'ch', '-d', disallowed_member, self.bucket.uri])
    # Confirm the disallowed member was actually removed.
    iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                return_stdout=True)
    self.assertHasNo(iam_string, disallowed_member, IAM_OBJECT_READ_ROLE)

  def test_patch_multiple_objects(self):
    """Tests IAM patch against multiple objects."""
    self.RunGsUtil([
        'iam', 'ch', '-r',
        '%s:legacyObjectReader' % self.user, self.bucket.uri
    ])

    object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                       return_stdout=True)
    object2_iam_string = self.RunGsUtil(['iam', 'get', self.object2.uri],
                                        return_stdout=True)
    self.assertHas(object_iam_string, self.user, IAM_OBJECT_READ_ROLE)
    self.assertHas(object2_iam_string, self.user, IAM_OBJECT_READ_ROLE)

  def test_patch_multithreaded_multiple_objects(self):
    """Tests multithreaded behavior against multiple objects."""
    self.RunGsUtil([
        '-m', 'iam', 'ch', '-r',
        '%s:legacyObjectReader' % self.user, self.bucket.uri
    ])

    object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                       return_stdout=True)
    object2_iam_string = self.RunGsUtil(['iam', 'get', self.object2.uri],
                                        return_stdout=True)
    self.assertHas(object_iam_string, self.user, IAM_OBJECT_READ_ROLE)
    self.assertHas(object2_iam_string, self.user, IAM_OBJECT_READ_ROLE)

  def test_patch_error(self):
    """See TestIamSet.test_set_error."""
    stderr = self.RunGsUtil([
        'iam', 'ch',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri,
        'gs://%s' % self.nonexistent_bucket_name, self.bucket2.uri
    ],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn('not found: 404.', stderr)
    else:
      self.assertIn('BucketNotFoundException', stderr)

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    bucket2_iam_string = self.RunGsUtil(['iam', 'get', self.bucket2.uri],
                                        return_stdout=True)

    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)
    self.assertEqualsPoliciesString(bucket2_iam_string, self.bucket_iam_string)

  def test_patch_force_error(self):
    """See TestIamSet.test_set_force_error."""
    stderr = self.RunGsUtil([
        'iam', 'ch', '-f',
        '%s:%s' % (self.user, IAM_BUCKET_READ_ROLE_ABBREV), self.bucket.uri,
        'gs://%s' % self.nonexistent_bucket_name, self.bucket2.uri
    ],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn('not found: 404.', stderr)
    else:
      self.assertIn('CommandException', stderr)

    bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                       return_stdout=True)
    bucket2_iam_string = self.RunGsUtil(['iam', 'get', self.bucket2.uri],
                                        return_stdout=True)

    self.assertHas(bucket_iam_string, self.user, IAM_BUCKET_READ_ROLE)
    self.assertHas(bucket2_iam_string, self.user, IAM_BUCKET_READ_ROLE)

  def test_patch_multithreaded_error(self):
    """See TestIamSet.test_set_multithreaded_error."""
    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stderr = self.RunGsUtil([
          '-m', 'iam', 'ch', '-r',
          '%s:legacyObjectReader' % self.user,
          'gs://%s' % self.nonexistent_bucket_name, self.bucket.uri
      ],
                              return_stderr=True,
                              expected_status=1)
      if self._use_gcloud_storage:
        self.assertIn('not found: 404.', stderr)
      else:
        self.assertIn('BucketNotFoundException', stderr)

    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                         return_stdout=True)
      object2_iam_string = self.RunGsUtil(['iam', 'get', self.object2.uri],
                                          return_stdout=True)

      self.assertEqualsPoliciesString(self.object_iam_string, object_iam_string)
      self.assertEqualsPoliciesString(self.object_iam_string,
                                      object2_iam_string)

    _Check1()
    _Check2()

  def test_assert_has(self):
    test_policy = {
        'bindings': [{
            'members': ['allUsers'],
            'role': 'roles/storage.admin'
        }, {
            'members': ['user:foo@bar.com', 'serviceAccount:bar@foo.com'],
            'role': IAM_BUCKET_READ_ROLE
        }]
    }

    self.assertHas(json.dumps(test_policy), 'allUsers', 'roles/storage.admin')
    self.assertHas(json.dumps(test_policy), 'user:foo@bar.com',
                   IAM_BUCKET_READ_ROLE)
    self.assertHasNo(json.dumps(test_policy), 'allUsers', IAM_BUCKET_READ_ROLE)
    self.assertHasNo(json.dumps(test_policy), 'user:foo@bar.com',
                     'roles/storage.admin')

  def assertHas(self, policy, member, role):
    """Asserts a member has permission for role.

    Given an IAM policy, check if the specified member is bound to the
    specified role. Does not check group inheritence -- that is, if checking
    against the [{'member': ['allUsers'], 'role': X}] policy, this function
    will still raise an exception when testing for any member other than
    'allUsers' against role X.

    This function does not invoke the TestIamPolicy endpoints to smartly check
    IAM policy resolution. This function is simply to assert the expected IAM
    policy is returned, not whether or not the IAM policy is being invoked as
    expected.

    Args:
      policy: Policy object as formatted by IamCommand._GetIam()
      member: A member string (e.g. 'user:foo@bar.com').
      role: A fully specified role (e.g. 'roles/storage.admin')

    Raises:
      AssertionError if member is not bound to role.
    """

    policy = json.loads(policy)
    bindings = dict((p['role'], p) for p in policy.get('bindings', []))
    if role in bindings:
      if member in bindings[role]['members']:
        return
    raise AssertionError('Member \'%s\' does not have permission \'%s\' in '
                         'policy %s' % (member, role, policy))

  def assertHasNo(self, policy, member, role):
    """Functions as logical compliment of TestIamCh.assertHas()."""
    try:
      self.assertHas(policy, member, role)
    except AssertionError:
      pass
    else:
      raise AssertionError('Member \'%s\' has permission \'%s\' in '
                           'policy %s' % (member, role, policy))


@SkipForS3('Tests use GS IAM model.')
@SkipForXML('XML IAM control is not supported.')
class TestIamSet(TestIamIntegration):
  """Integration tests for iam set command."""

  # TODO(iam-beta): Replace gen_binding, _patch_binding with generators from
  # iam_helper.
  def setUp(self):
    super(TestIamSet, self).setUp()

    self.public_bucket_read_binding = gen_binding(IAM_BUCKET_READ_ROLE)
    self.public_object_read_binding = gen_binding(IAM_OBJECT_READ_ROLE)
    self.project_viewer_objectviewer_with_cond_binding = gen_binding(
        IAM_OBJECT_VIEWER_ROLE,
        # Note: We use projectViewer:some-project-id here because conditions
        # cannot be applied to a binding that only has allUsers in the members
        # list; the API gives back a 400 error if you try.
        members=['projectViewer:%s' % PopulateProjectId()],
        condition={
            'title': TEST_CONDITION_TITLE,
            'description': TEST_CONDITION_DESCRIPTION,
            'expression': TEST_CONDITION_EXPR_RESOURCE_IS_OBJECT,
        })

    self.bucket = self.CreateBucket()
    self.versioned_bucket = self.CreateVersionedBucket()

    # Create a bucket to fetch its policy, used as a base for other policies.
    self.bucket_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                            return_stdout=True)
    self.old_bucket_iam_path = self.CreateTempFile(
        contents=self.bucket_iam_string.encode(UTF8))

    # Using the existing bucket's policy, make an altered policy that allows
    # allUsers to be "legacyBucketReader"s. Some tests will later apply this
    # policy.
    self.new_bucket_iam_policy = patch_binding(
        json.loads(self.bucket_iam_string), IAM_BUCKET_READ_ROLE,
        self.public_bucket_read_binding)
    self.new_bucket_iam_path = self.CreateTempFile(
        contents=json.dumps(self.new_bucket_iam_policy).encode(UTF8))

    # Using the existing bucket's policy, make an altered policy that contains
    # a binding with a condition in it. Some tests will later apply this policy.
    self.new_bucket_policy_with_conditions_policy = json.loads(
        self.bucket_iam_string)
    self.new_bucket_policy_with_conditions_policy['bindings'].append(
        self.project_viewer_objectviewer_with_cond_binding[0])
    self.new_bucket_policy_with_conditions_path = self.CreateTempFile(
        contents=json.dumps(self.new_bucket_policy_with_conditions_policy))

    # Create an object to fetch its policy, used as a base for other policies.
    self.object = self.CreateObject(contents='foobar')
    self.object_iam_string = self.RunGsUtil(['iam', 'get', self.object.uri],
                                            return_stdout=True)
    self.old_object_iam_path = self.CreateTempFile(
        contents=self.object_iam_string.encode(UTF8))

    # Using the existing object's policy, make an altered policy that allows
    # allUsers to be "legacyObjectReader"s. Some tests will later apply this
    # policy.
    self.new_object_iam_policy = patch_binding(
        json.loads(self.object_iam_string), IAM_OBJECT_READ_ROLE,
        self.public_object_read_binding)
    self.new_object_iam_path = self.CreateTempFile(
        contents=json.dumps(self.new_object_iam_policy).encode(UTF8))

  def test_seek_ahead_iam(self):
    """Ensures that the seek-ahead iterator is being used with iam commands."""

    gsutil_object = self.CreateObject(bucket_uri=self.bucket,
                                      contents=b'foobar')

    # This forces the seek-ahead iterator to be utilized.
    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '1'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(
          ['-m', 'iam', 'set', self.new_object_iam_path, gsutil_object.uri],
          return_stderr=True)
      self.assertIn('Estimated work for this command: objects: 1\n', stderr)

  def test_set_mix_of_buckets_and_objects(self):
    """Tests that failure is thrown when buckets and objects are provided."""

    stderr = self.RunGsUtil([
        'iam', 'set', self.new_object_iam_path, self.bucket.uri, self.object.uri
    ],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('CommandException', stderr)

  def test_set_file_url(self):
    """Tests that failure is thrown when a file url is provided."""
    stderr = self.RunGsUtil(
        ['iam', 'set', self.new_object_iam_path, 'file://somefile'],
        return_stderr=True,
        expected_status=1)
    self.assertIn('AttributeError', stderr)

  def test_set_invalid_iam_bucket(self):
    """Ensures invalid content returns error on input check."""
    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      inpath = self.CreateTempFile(contents=b'badIam')
      stderr = self.RunGsUtil(['iam', 'set', inpath, self.bucket.uri],
                              return_stderr=True,
                              expected_status=1)
      error_message = ('Found invalid JSON/YAML'
                       if self._use_gcloud_storage else 'ArgumentException')
      self.assertIn(error_message, stderr)

    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      # Tests that setting with a non-existent file will also return error.
      stderr = self.RunGsUtil(
          ['iam', 'set', 'nonexistent/path', self.bucket.uri],
          return_stderr=True,
          expected_status=1)
      error_message = ('No such file or directory'
                       if self._use_gcloud_storage else 'ArgumentException')
      self.assertIn(error_message, stderr)

    _Check1()
    _Check2()

  def test_get_invalid_bucket(self):
    """Ensures that invalid bucket names returns an error."""
    stderr = self.RunGsUtil(['iam', 'get', self.nonexistent_bucket_name],
                            return_stderr=True,
                            expected_status=1)
    error_message = ('AttributeError'
                     if self._use_gcloud_storage else 'CommandException')
    self.assertIn(error_message, stderr)

    stderr = self.RunGsUtil(
        ['iam', 'get', 'gs://%s' % self.nonexistent_bucket_name],
        return_stderr=True,
        expected_status=1)
    error_message = ('not found'
                     if self._use_gcloud_storage else 'BucketNotFoundException')
    self.assertIn(error_message, stderr)

    # N.B.: The call to wildcard_iterator.WildCardIterator here will invoke
    # ListBucket, which only promises eventual consistency. We use @Retry here
    # to mitigate errors due to this.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():  # pylint: disable=invalid-name
      # There are at least two buckets in the project
      # due to TestIamSet.setUp().
      stderr = self.RunGsUtil(['iam', 'get', 'gs://*'],
                              return_stderr=True,
                              expected_status=1)
      error_message = ('must match a single cloud resource'
                       if self._use_gcloud_storage else 'CommandException')
      self.assertIn(error_message, stderr)

    _Check()

  def test_set_valid_iam_bucket(self):
    """Tests setting a valid IAM on a bucket."""
    self.RunGsUtil(
        ['iam', 'set', '-e', '', self.new_bucket_iam_path, self.bucket.uri])
    set_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                    return_stdout=True)
    self.RunGsUtil(
        ['iam', 'set', '-e', '', self.old_bucket_iam_path, self.bucket.uri])
    reset_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.bucket_iam_string, reset_iam_string)
    self.assertIn(self.public_bucket_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

  @unittest.skip('Disabled until all projects whitelisted for conditions.')
  def test_set_and_get_valid_bucket_policy_with_conditions(self):
    """Tests setting and getting an IAM policy with conditions on a bucket."""
    self.RunGsUtil([
        'iam', 'set', '-e', '', self.new_bucket_policy_with_conditions_path,
        self.bucket.uri
    ])
    get_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                    return_stdout=True)
    self.assertIn(TEST_CONDITION_DESCRIPTION, get_iam_string)
    self.assertIn(TEST_CONDITION_EXPR_RESOURCE_IS_OBJECT,
                  get_iam_string.replace('\\', ''))
    self.assertIn(TEST_CONDITION_TITLE, get_iam_string)

  # Note: We only test this for buckets, since objects cannot currently have
  # conditions in their policy bindings.
  @unittest.skip('Disabled until all projects whitelisted for conditions.')
  def test_ch_fails_after_setting_conditions(self):
    """Tests that if we "set" a policy with conditions, "ch" won't patch it."""
    print()
    self.RunGsUtil([
        'iam', 'set', '-e', '', self.new_bucket_policy_with_conditions_path,
        self.bucket.uri
    ])

    # Assert that we get an error both with and without ch's `-f` option.
    # Without `-f`:
    stderr = self.RunGsUtil(
        ['iam', 'ch', 'allUsers:objectViewer', self.bucket.uri],
        return_stderr=True,
        expected_status=1)
    self.assertIn('CommandException: Could not patch IAM policy for', stderr)
    # Also make sure we print the workaround message.
    self.assertIn('The resource had conditions present', stderr)

    # With `-f`:
    stderr = self.RunGsUtil(
        ['iam', 'ch', '-f', 'allUsers:objectViewer', self.bucket.uri],
        return_stderr=True,
        expected_status=1)
    self.assertIn('CommandException: Some IAM policies could not be patched',
                  stderr)
    # Also make sure we print the workaround message.
    self.assertIn('Some resources had conditions', stderr)

  def test_set_blank_etag(self):
    """Tests setting blank etag behaves appropriately."""
    self.RunGsUtil(
        ['iam', 'set', '-e', '', self.new_bucket_iam_path, self.bucket.uri])

    set_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                    return_stdout=True)

    self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(set_iam_string)['etag'], self.old_bucket_iam_path,
        self.bucket.uri
    ])

    reset_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.bucket_iam_string, reset_iam_string)
    self.assertIn(self.public_bucket_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

  def test_set_valid_etag(self):
    """Tests setting valid etag behaves correctly."""
    get_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                    return_stdout=True)
    self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(get_iam_string)['etag'], self.new_bucket_iam_path,
        self.bucket.uri
    ])

    set_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                    return_stdout=True)
    self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(set_iam_string)['etag'], self.old_bucket_iam_path,
        self.bucket.uri
    ])

    reset_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.bucket_iam_string, reset_iam_string)
    self.assertIn(self.public_bucket_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

  def test_set_invalid_etag(self):
    """Tests setting an invalid etag format raises an error."""
    self.RunGsUtil(['iam', 'get', self.bucket.uri], return_stdout=True)
    stderr = self.RunGsUtil([
        'iam', 'set', '-e', 'some invalid etag', self.new_bucket_iam_path,
        self.bucket.uri
    ],
                            return_stderr=True,
                            expected_status=1)
    error_message = ('DecodeError'
                     if self._use_gcloud_storage else 'ArgumentException')
    self.assertIn(error_message, stderr)

  def test_set_mismatched_etag(self):
    """Tests setting mismatched etag raises an error."""
    get_iam_string = self.RunGsUtil(['iam', 'get', self.bucket.uri],
                                    return_stdout=True)
    self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(get_iam_string)['etag'], self.new_bucket_iam_path,
        self.bucket.uri
    ])
    stderr = self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(get_iam_string)['etag'], self.new_bucket_iam_path,
        self.bucket.uri
    ],
                            return_stderr=True,
                            expected_status=1)
    error_message = ('pre-conditions you specified did not hold'
                     if self._use_gcloud_storage else 'PreconditionException')
    self.assertIn(error_message, stderr)

  def _create_multiple_objects(self):
    """Creates two versioned objects and return references to all versions.

    Returns:
      A four-tuple (a, b, a*, b*) of storage_uri.BucketStorageUri instances.
    """

    old_gsutil_object = self.CreateObject(bucket_uri=self.versioned_bucket,
                                          contents=b'foo')
    old_gsutil_object2 = self.CreateObject(bucket_uri=self.versioned_bucket,
                                           contents=b'bar')
    gsutil_object = self.CreateObject(
        bucket_uri=self.versioned_bucket,
        object_name=old_gsutil_object.object_name,
        contents=b'new_foo',
        gs_idempotent_generation=urigen(old_gsutil_object))
    gsutil_object2 = self.CreateObject(
        bucket_uri=self.versioned_bucket,
        object_name=old_gsutil_object2.object_name,
        contents=b'new_bar',
        gs_idempotent_generation=urigen(old_gsutil_object2))
    return (old_gsutil_object, old_gsutil_object2, gsutil_object,
            gsutil_object2)

  def test_set_valid_iam_multiple_objects(self):
    """Tests setting a valid IAM on multiple objects."""
    (old_gsutil_object, old_gsutil_object2, gsutil_object,
     gsutil_object2) = self._create_multiple_objects()

    # Set IAM policy on newest versions of all objects.
    self.RunGsUtil([
        'iam', 'set', '-r', self.new_object_iam_path, self.versioned_bucket.uri
    ])
    set_iam_string = self.RunGsUtil(['iam', 'get', gsutil_object.uri],
                                    return_stdout=True)
    set_iam_string2 = self.RunGsUtil(['iam', 'get', gsutil_object2.uri],
                                     return_stdout=True)
    self.assertEqualsPoliciesString(set_iam_string, set_iam_string2)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

    # Check that old versions are not affected by the set IAM call.
    iam_string_old = self.RunGsUtil(
        ['iam', 'get', old_gsutil_object.version_specific_uri],
        return_stdout=True)
    iam_string_old2 = self.RunGsUtil(
        ['iam', 'get', old_gsutil_object2.version_specific_uri],
        return_stdout=True)
    self.assertEqualsPoliciesString(iam_string_old, iam_string_old2)
    self.assertEqualsPoliciesString(self.object_iam_string, iam_string_old)

  def test_set_valid_iam_multithreaded_multiple_objects(self):
    """Tests setting a valid IAM on multiple objects."""
    (old_gsutil_object, old_gsutil_object2, gsutil_object,
     gsutil_object2) = self._create_multiple_objects()

    # Set IAM policy on newest versions of all objects.
    self.RunGsUtil([
        '-m', 'iam', 'set', '-r', self.new_object_iam_path,
        self.versioned_bucket.uri
    ])
    set_iam_string = self.RunGsUtil(['iam', 'get', gsutil_object.uri],
                                    return_stdout=True)
    set_iam_string2 = self.RunGsUtil(['iam', 'get', gsutil_object2.uri],
                                     return_stdout=True)
    self.assertEqualsPoliciesString(set_iam_string, set_iam_string2)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

    # Check that old versions are not affected by the set IAM call.
    iam_string_old = self.RunGsUtil(
        ['iam', 'get', old_gsutil_object.version_specific_uri],
        return_stdout=True)
    iam_string_old2 = self.RunGsUtil(
        ['iam', 'get', old_gsutil_object2.version_specific_uri],
        return_stdout=True)
    self.assertEqualsPoliciesString(iam_string_old, iam_string_old2)
    self.assertEqualsPoliciesString(self.object_iam_string, iam_string_old)

  def test_set_valid_iam_multiple_objects_all_versions(self):
    """Tests set IAM policy on all versions of all objects."""
    (old_gsutil_object, old_gsutil_object2, gsutil_object,
     gsutil_object2) = self._create_multiple_objects()

    self.RunGsUtil([
        'iam', 'set', '-ra', self.new_object_iam_path, self.versioned_bucket.uri
    ])
    set_iam_string = self.RunGsUtil(
        ['iam', 'get', gsutil_object.version_specific_uri], return_stdout=True)
    set_iam_string2 = self.RunGsUtil(
        ['iam', 'get', gsutil_object2.version_specific_uri], return_stdout=True)
    set_iam_string_old = self.RunGsUtil(
        ['iam', 'get', old_gsutil_object.version_specific_uri],
        return_stdout=True)
    set_iam_string_old2 = self.RunGsUtil(
        ['iam', 'get', old_gsutil_object2.version_specific_uri],
        return_stdout=True)
    self.assertEqualsPoliciesString(set_iam_string, set_iam_string2)
    self.assertEqualsPoliciesString(set_iam_string, set_iam_string_old)
    self.assertEqualsPoliciesString(set_iam_string, set_iam_string_old2)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

  def test_set_error(self):
    """Tests fail-fast behavior of iam set.

    We initialize two buckets (bucket, bucket2) and attempt to set both along
    with a third, non-existent bucket in between, self.nonexistent_bucket_name.

    We want to ensure
      1.) Bucket "bucket" IAM policy has been set appropriately,
      2.) Bucket self.nonexistent_bucket_name has caused an error, and
      3.) gsutil has exited and "bucket2"'s IAM policy is unaltered.
    """

    bucket = self.CreateBucket()
    bucket2 = self.CreateBucket()

    stderr = self.RunGsUtil([
        'iam', 'set', '-e', '', self.new_bucket_iam_path, bucket.uri,
        'gs://%s' % self.nonexistent_bucket_name, bucket2.uri
    ],
                            return_stderr=True,
                            expected_status=1)

    # The program has exited due to a bucket lookup 404.
    error_message = ('not found'
                     if self._use_gcloud_storage else 'BucketNotFoundException')
    self.assertIn(error_message, stderr)
    set_iam_string = self.RunGsUtil(['iam', 'get', bucket.uri],
                                    return_stdout=True)
    set_iam_string2 = self.RunGsUtil(['iam', 'get', bucket2.uri],
                                     return_stdout=True)

    # The IAM policy has been set on Bucket "bucket".
    self.assertIn(self.public_bucket_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

    # The IAM policy for Bucket "bucket2" remains unchanged.
    self.assertEqualsPoliciesString(self.bucket_iam_string, set_iam_string2)

  def test_set_force_error(self):
    """Tests ignoring failure behavior of iam set.

    Similar to TestIamSet.test_set_error, except here we want to ensure
      1.) Bucket "bucket" IAM policy has been set appropriately,
      2.) Bucket self.nonexistent_bucket_name has caused an error, BUT
      3.) gsutil has continued and "bucket2"'s IAM policy has been set as well.
    """
    bucket = self.CreateBucket()
    bucket2 = self.CreateBucket()

    stderr = self.RunGsUtil([
        'iam', 'set', '-f', self.new_bucket_iam_path, bucket.uri,
        'gs://%s' % self.nonexistent_bucket_name, bucket2.uri
    ],
                            return_stderr=True,
                            expected_status=1)

    # The program asserts that an error has occured (due to 404).
    error_message = ('not found'
                     if self._use_gcloud_storage else 'CommandException')
    self.assertIn(error_message, stderr)

    set_iam_string = self.RunGsUtil(['iam', 'get', bucket.uri],
                                    return_stdout=True)
    set_iam_string2 = self.RunGsUtil(['iam', 'get', bucket2.uri],
                                     return_stdout=True)

    # The IAM policy has been set appropriately on Bucket "bucket".
    self.assertIn(self.public_bucket_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

    # The IAM policy has also been set on Bucket "bucket2".
    self.assertEqualsPoliciesString(set_iam_string, set_iam_string2)

  def test_set_multithreaded_error(self):
    """Tests fail-fast behavior of multithreaded iam set.

    This is testing gsutil iam set with the -m and -r flags present in
    invocation.

    N.B.: Currently, (-m, -r) behaves identically to (-m, -fr) and (-fr,).
    However, (-m, -fr) and (-fr,) behavior is not as expected due to
    name_expansion.NameExpansionIterator.next raising problematic e.g. 404
    or 403 errors. More details on this issue can be found in comments in
    commands.iam.IamCommand._SetIam.

    Thus, the following command
      gsutil -m iam set -fr <object_policy> gs://bad_bucket gs://good_bucket

    will NOT set policies on objects in gs://good_bucket due to an error when
    iterating over gs://bad_bucket.
    """

    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stderr = self.RunGsUtil([
          '-m', 'iam', 'set', '-r', self.new_object_iam_path,
          'gs://%s' % self.nonexistent_bucket_name, self.bucket.uri
      ],
                              return_stderr=True,
                              expected_status=1)
      error_message = ('not found' if self._use_gcloud_storage else
                       'BucketNotFoundException')
      self.assertIn(error_message, stderr)

    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      gsutil_object = self.CreateObject(bucket_uri=self.bucket,
                                        contents=b'foobar')
      gsutil_object2 = self.CreateObject(bucket_uri=self.bucket,
                                         contents=b'foobar')
      set_iam_string = self.RunGsUtil(['iam', 'get', gsutil_object.uri],
                                      return_stdout=True)
      set_iam_string2 = self.RunGsUtil(['iam', 'get', gsutil_object2.uri],
                                       return_stdout=True)
      self.assertEqualsPoliciesString(set_iam_string, set_iam_string2)
      self.assertEqualsPoliciesString(self.object_iam_string, set_iam_string)

    _Check1()
    _Check2()

  def test_set_valid_iam_single_unversioned_object(self):
    """Tests setting a valid IAM on an object."""
    gsutil_object = self.CreateObject(bucket_uri=self.bucket,
                                      contents=b'foobar')

    lookup_uri = gsutil_object.uri
    self.RunGsUtil(['iam', 'set', self.new_object_iam_path, lookup_uri])
    set_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                    return_stdout=True)
    self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(set_iam_string)['etag'], self.old_object_iam_path, lookup_uri
    ])
    reset_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.object_iam_string, reset_iam_string)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

  def test_set_valid_iam_single_versioned_object(self):
    """Tests setting a valid IAM on a versioned object."""
    gsutil_object = self.CreateObject(bucket_uri=self.bucket,
                                      contents=b'foobar')

    lookup_uri = gsutil_object.version_specific_uri
    self.RunGsUtil(['iam', 'set', self.new_object_iam_path, lookup_uri])
    set_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                    return_stdout=True)
    self.RunGsUtil([
        'iam', 'set', '-e',
        json.loads(set_iam_string)['etag'], self.old_object_iam_path, lookup_uri
    ])
    reset_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.object_iam_string, reset_iam_string)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

  def test_set_valid_iam_multithreaded_single_object(self):
    """Tests setting a valid IAM on a single object with multithreading."""
    gsutil_object = self.CreateObject(bucket_uri=self.bucket,
                                      contents=b'foobar')

    lookup_uri = gsutil_object.version_specific_uri
    self.RunGsUtil(
        ['-m', 'iam', 'set', '-e', '', self.new_object_iam_path, lookup_uri])
    set_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                    return_stdout=True)
    self.RunGsUtil(
        ['-m', 'iam', 'set', '-e', '', self.old_object_iam_path, lookup_uri])
    reset_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.object_iam_string, reset_iam_string)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])

    # Test multithreading on single object, specified with wildcards.
    lookup_uri = '%s*' % self.bucket.uri
    self.RunGsUtil(
        ['-m', 'iam', 'set', '-e', '', self.new_object_iam_path, lookup_uri])
    set_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                    return_stdout=True)
    self.RunGsUtil(
        ['-m', 'iam', 'set', '-e', '', self.old_object_iam_path, lookup_uri])
    reset_iam_string = self.RunGsUtil(['iam', 'get', lookup_uri],
                                      return_stdout=True)

    self.assertEqualsPoliciesString(self.object_iam_string, reset_iam_string)
    self.assertIn(self.public_object_read_binding[0],
                  json.loads(set_iam_string)['bindings'])


class TestIamShim(testcase.GsUtilUnitTestCase):

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_get_object(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('iam', ['get', 'gs://bucket/object'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage objects get-iam-policy'
             ' --format=json gs://bucket/object').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_get_bucket(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('iam', ['get', 'gs://bucket'],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets get-iam-policy'
             ' --format=json gs://bucket').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_set_object(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'iam', ['set', 'policy-file', 'gs://b/o1', 'gs://b/o2'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage objects set-iam-policy'
             ' --format=json gs://b/o1 gs://b/o2 policy-file').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_set_bucket(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'iam', ['set', 'policy-file', 'gs://b1', 'gs://b2'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets set-iam-policy'
             ' --format=json gs://b1 gs://b2 policy-file').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_set_mix_of_bucket_and_objects_if_recursive(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'iam', ['set', '-r', 'policy-file', 'gs://b1', 'gs://b2/o'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage objects set-iam-policy'
             ' --format=json --recursive gs://b1 gs://b2/o policy-file').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_raises_for_iam_set_mix_of_bucket_and_objects(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        with self.assertRaisesRegex(
            CommandException,
            'Cannot operate on a mix of buckets and objects.'):
          self.RunCommand('iam', ['set', 'policy-file', 'gs://b', 'gs://b/o'])

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_set_handles_valid_etag(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'iam', ['set', '-e', 'abc=', 'policy-file', 'gs://b'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets set-iam-policy'
             ' --format=json --etag abc= gs://b policy-file').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_translates_iam_set_handles_empty_etag(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand(
            'iam', ['set', '-e', '', 'policy-file', 'gs://b'],
            return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            ('Gcloud Storage Command: {} storage buckets set-iam-policy'
             ' --format=json --etag= gs://b policy-file').format(
                 shim_util._get_gcloud_binary_path('fake_dir')), info_lines)

  @mock.patch.object(iam.IamCommand, 'RunCommand', new=mock.Mock())
  def test_shim_warns_with_dry_run_mode_for_iam_ch(self):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('iam',
                                           ['ch', '-d', 'allUsers', 'gs://b'],
                                           return_log_handler=True)
        warning_lines = '\n'.join(mock_log_handler.messages['warning'])
        self.assertIn(
            'The shim maps iam ch commands to several gcloud storage commands,'
            ' which cannot be determined without running gcloud storage.',
            warning_lines)

  def _get_run_call(self,
                    command,
                    env=mock.ANY,
                    stdin=None,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True):
    return mock.call(command,
                     env=env,
                     input=stdin,
                     stderr=stderr,
                     stdout=stdout,
                     text=text)

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_adds_updates_and_deletes_bucket_policies(self, mock_run):
    original_policy = {
        'bindings': [{
            'role': 'preserved-role',
            'members': ['allUsers'],
        }, {
            'role': 'roles/storage.modified-role',
            'members': ['allUsers', 'user:deleted-user@example.com'],
        }, {
            'role': 'roles/storage.deleted-role',
            'members': ['allUsers'],
        }]
    }
    new_policy = {
        'bindings': [{
            'role': 'preserved-role',
            'members': ['allUsers'],
        }, {
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'allUsers'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      get_process = subprocess.CompletedProcess(
          args=[], returncode=0, stdout=json.dumps(original_policy))
      set_process = subprocess.CompletedProcess(args=[], returncode=0)
      mock_run.side_effect = [get_process, set_process]
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        self.RunCommand('iam', [
            'ch', 'allAuthenticatedUsers:modified-role', '-d',
            'user:deleted-user@example.com', '-d', 'allUsers:deleted-role',
            'gs://b'
        ])

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'buckets', 'get-iam-policy', 'gs://b/', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'buckets',
              'set-iam-policy',
              'gs://b/',
              '-',
          ],
                             stdin=json.dumps(new_policy, sort_keys=True))
      ])

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_updates_bucket_policies_for_multiple_urls(self, mock_run):
    original_policy1 = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['user:test-user1@example.com'],
        }]
    }
    original_policy2 = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['user:test-user2@example.com'],
        }]
    }
    new_policy1 = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'user:test-user1@example.com'],
        }]
    }
    new_policy2 = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'user:test-user2@example.com'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      get_process1 = subprocess.CompletedProcess(
          args=[], returncode=0, stdout=json.dumps(original_policy1))
      get_process2 = subprocess.CompletedProcess(
          args=[], returncode=0, stdout=json.dumps(original_policy2))
      set_process = subprocess.CompletedProcess(args=[], returncode=0)
      mock_run.side_effect = [
          get_process1, set_process, get_process2, set_process
      ]

      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        self.RunCommand(
            'iam',
            ['ch', 'allAuthenticatedUsers:modified-role', 'gs://b1', 'gs://b2'])

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'buckets', 'get-iam-policy', 'gs://b1/', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'buckets',
              'set-iam-policy',
              'gs://b1/',
              '-',
          ],
                             stdin=json.dumps(new_policy1, sort_keys=True)),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'buckets', 'get-iam-policy', 'gs://b2/', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'buckets',
              'set-iam-policy',
              'gs://b2/',
              '-',
          ],
                             stdin=json.dumps(new_policy2, sort_keys=True))
      ])

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_updates_object_policies(self, mock_run):
    original_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allUsers'],
        }]
    }
    new_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'allUsers'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=0,
                                               stdout=json.dumps([{
                                                   'url': 'gs://b/o',
                                                   'type': 'cloud_object'
                                               }]))
      get_process = subprocess.CompletedProcess(
          args=[], returncode=0, stdout=json.dumps(original_policy))
      set_process = subprocess.CompletedProcess(args=[], returncode=0)
      mock_run.side_effect = [ls_process, get_process, set_process]
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        self.RunCommand(
            'iam', ['ch', 'allAuthenticatedUsers:modified-role', 'gs://b/o'])

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'objects', 'get-iam-policy', 'gs://b/o', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'objects',
              'set-iam-policy',
              'gs://b/o',
              '-',
          ],
                             stdin=json.dumps(new_policy, sort_keys=True))
      ])

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_expands_urls_with_recursion_and_ignores_container_headers(
      self, mock_run):
    original_policy = {
        'bindings': [{
            'role': 'modified-role',
            'members': ['allUsers'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=0,
                                               stdout=json.dumps([{
                                                   'url': 'gs://b/dir/',
                                                   'type': 'prefix'
                                               }, {
                                                   'url': 'gs://b/dir/:',
                                                   'type': 'cloud_object'
                                               }, {
                                                   'url': 'gs://b/dir2/',
                                                   'type': 'prefix'
                                               }, {
                                                   'url': 'gs://b/dir2/o',
                                                   'type': 'cloud_object'
                                               }]))
      get_process = subprocess.CompletedProcess(
          args=[], returncode=0, stdout=json.dumps(original_policy))
      set_process = subprocess.CompletedProcess(args=[], returncode=0)
      mock_run.side_effect = [ls_process] + [get_process, set_process] * 3
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        self.RunCommand(
            'iam',
            ['ch', '-r', 'allAuthenticatedUsers:modified-role', 'gs://b'])

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', '-r', 'gs://b/'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'objects', 'get-iam-policy', 'gs://b/dir/:', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'objects',
              'set-iam-policy',
              'gs://b/dir/:',
              '-',
          ],
                             stdin=mock.ANY),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'objects', 'get-iam-policy', 'gs://b/dir2/o', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'objects',
              'set-iam-policy',
              'gs://b/dir2/o',
              '-',
          ],
                             stdin=mock.ANY)
      ])

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_raises_ls_error(self, mock_run):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=1,
                                               stderr='An error.')
      mock_run.side_effect = [ls_process]

      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        with self.assertRaisesRegex(CommandException, 'An error.'):
          self.RunCommand(
              'iam', ['ch', 'allAuthenticatedUsers:modified-role', 'gs://b/o'])
        self.assertEqual(mock_run.call_count, 1)

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_raises_get_error(self, mock_run):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=0,
                                               stdout=json.dumps([{
                                                   'url': 'gs://b/o',
                                                   'type': 'cloud_object'
                                               }]))
      get_process = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='An error.')
      mock_run.side_effect = [ls_process, get_process]

      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        with self.assertRaisesRegex(CommandException, 'An error.'):
          self.RunCommand(
              'iam', ['ch', 'allAuthenticatedUsers:modified-role', 'gs://b/o'])
        self.assertEqual(mock_run.call_count, 2)

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_raises_set_error(self, mock_run):
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=0,
                                               stdout=json.dumps([{
                                                   'url': 'gs://b/o',
                                                   'type': 'cloud_object'
                                               }]))
      get_process = subprocess.CompletedProcess(args=[],
                                                returncode=0,
                                                stdout='{"bindings": []}')
      set_process = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='An error.')
      mock_run.side_effect = [ls_process, get_process, set_process]

      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        with self.assertRaisesRegex(CommandException, 'An error.'):
          self.RunCommand(
              'iam', ['ch', 'allAuthenticatedUsers:modified-role', 'gs://b/o'])
        self.assertEqual(mock_run.call_count, 3)

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_continues_on_ls_error(self, mock_run):
    original_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allUsers'],
        }]
    }
    new_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'allUsers'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=1,
                                               stderr='An error.')
      ls_process2 = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='Another error.')
      mock_run.side_effect = [ls_process, ls_process2]

      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('iam', [
            'ch',
            '-f',
            'allAuthenticatedUsers:modified-role',
            'gs://b/o1',
            'gs://b/o2',
        ],
                                           debug=1,
                                           return_log_handler=True)

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o1'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o2'
          ]),
      ])

      error_lines = '\n'.join(mock_log_handler.messages['error'])
      self.assertIn('An error.', error_lines)
      self.assertIn('Another error.', error_lines)

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_continues_on_get_error(self, mock_run):
    original_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allUsers'],
        }]
    }
    new_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'allUsers'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=0,
                                               stdout=json.dumps([{
                                                   'url': 'gs://b/o1',
                                                   'type': 'cloud_object'
                                               }]))
      get_process = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='An error.')
      ls_process2 = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='Another error.')
      mock_run.side_effect = [ls_process, get_process, ls_process2]
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('iam', [
            'ch',
            '-f',
            'allAuthenticatedUsers:modified-role',
            'gs://b/o1',
            'gs://b/o2',
        ],
                                           debug=1,
                                           return_log_handler=True)

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o1'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'objects', 'get-iam-policy', 'gs://b/o1', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o2'
          ]),
      ])

      error_lines = '\n'.join(mock_log_handler.messages['error'])
      self.assertIn('An error.', error_lines)
      self.assertIn('Another error.', error_lines)

  @mock.patch.object(subprocess, 'run', autospec=True)
  def test_iam_ch_continues_on_set_error(self, mock_run):
    original_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allUsers'],
        }]
    }
    new_policy = {
        'bindings': [{
            'role': 'roles/storage.modified-role',
            'members': ['allAuthenticatedUsers', 'allUsers'],
        }]
    }
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True')]):
      ls_process = subprocess.CompletedProcess(args=[],
                                               returncode=0,
                                               stdout=json.dumps([{
                                                   'url': 'gs://b/o1',
                                                   'type': 'cloud_object'
                                               }]))
      get_process = subprocess.CompletedProcess(
          args=[], returncode=0, stdout=json.dumps(original_policy))
      set_process = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='An error.')
      ls_process2 = subprocess.CompletedProcess(args=[],
                                                returncode=1,
                                                stderr='Another error.')
      mock_run.side_effect = [ls_process, get_process, set_process, ls_process2]

      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('iam', [
            'ch', '-f', 'allAuthenticatedUsers:modified-role', 'gs://b/o1',
            'gs://b/o2'
        ],
                                           debug=1,
                                           return_log_handler=True)

      self.assertEqual(mock_run.call_args_list, [
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o1'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage',
              'objects', 'get-iam-policy', 'gs://b/o1', '--format=json'
          ]),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'),
              'storage',
              'objects',
              'set-iam-policy',
              'gs://b/o1',
              '-',
          ],
                             stdin=json.dumps(new_policy, sort_keys=True)),
          self._get_run_call([
              shim_util._get_gcloud_binary_path('fake_dir'), 'storage', 'ls',
              '--json', 'gs://b/o2'
          ]),
      ])

      error_lines = '\n'.join(mock_log_handler.messages['error'])
      self.assertIn('An error.', error_lines)
      self.assertIn('Another error.', error_lines)
