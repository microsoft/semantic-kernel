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
"""Helper module for the IAM command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from collections import defaultdict
from collections import namedtuple

import six
from apitools.base.protorpclite import protojson
from gslib.exception import CommandException
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages

TYPES = set([
    'user', 'deleted:user', 'serviceAccount', 'deleted:serviceAccount', 'group',
    'deleted:group', 'domain', 'principal', 'principalSet', 'principalHierarchy'
])

DISCOURAGED_TYPES = set([
    'projectOwner',
    'projectEditor',
    'projectViewer',
])

DISCOURAGED_TYPES_MSG = (
    'Assigning roles (e.g. objectCreator, legacyBucketOwner) for project '
    'convenience groups is not supported by gsutil, as it goes against the '
    'principle of least privilege. Consider creating and using more granular '
    'groups with which to assign permissions. See '
    'https://cloud.google.com/iam/docs/using-iam-securely for more '
    'information. Assigning a role to a project group can be achieved by '
    'setting the IAM policy directly (see gsutil help iam for specifics).')

PUBLIC_MEMBERS = set([
    'allUsers',
    'allAuthenticatedUsers',
])

# These are convenience classes to handle returned results from
# BindingStringToTuple. is_grant is a boolean specifying if the
# bindings are to be granted or removed from a bucket / object.
# bindings varies by type.
# For BindingsTuple, it is a list of BindingsValueListEntry
# For BindingsDictTuple it is a list of analogous dicts, e.g.:
# {
#   'members': ['member'],
#   'role': 'role',
# }
BindingsTuple = namedtuple('BindingsTuple', ['is_grant', 'bindings'])
BindingsDictTuple = namedtuple('BindingsDictTuple', ['is_grant', 'bindings'])

# This is a special role value assigned to a specific member when all roles
# assigned to the member should be dropped in the policy. A member:DROP_ALL
# binding will be passed from BindingStringToTuple into PatchBindings.
# This role will only ever appear on client-side (i.e. user-generated). It
# will never be returned as a real role from an IAM get request. All roles
# returned by PatchBindings are guaranteed to be "real" roles, i.e. not a
# DROP_ALL role.
DROP_ALL = ''


def SerializeBindingsTuple(bindings_tuple):
  """Serializes the BindingsValueListEntry instances in a BindingsTuple.

  This is necessary when passing instances of BindingsTuple through
  Command.Apply, as apitools_messages classes are not by default pickleable.

  Args:
    bindings_tuple: A BindingsTuple instance to be serialized.

  Returns:
    A serialized BindingsTuple object.
  """
  return (bindings_tuple.is_grant,
          [protojson.encode_message(t) for t in bindings_tuple.bindings])


def DeserializeBindingsTuple(serialized_bindings_tuple):
  (is_grant, bindings) = serialized_bindings_tuple
  return BindingsTuple(is_grant=is_grant,
                       bindings=[
                           protojson.decode_message(
                               apitools_messages.Policy.BindingsValueListEntry,
                               t) for t in bindings
                       ])


def BindingsMessageToUpdateDict(bindings):
  """Reformats policy bindings metadata.

  Args:
    bindings: A list of BindingsValueListEntry instances.

  Returns:
    A {role: set(members)} dictionary.
  """

  tmp_bindings = defaultdict(set)
  for binding in bindings:
    tmp_bindings[binding.role].update(binding.members)
  return tmp_bindings


def BindingsDictToUpdateDict(bindings):
  """Reformats policy bindings metadata.

  Args:
    bindings: List of dictionaries representing BindingsValueListEntry
      instances. e.g.:
      {
        "role": "some_role",
        "members": ["allAuthenticatedUsers", ...]
      }

  Returns:
    A {role: set(members)} dictionary.
  """

  tmp_bindings = defaultdict(set)
  for binding in bindings:
    tmp_bindings[binding['role']].update(binding['members'])
  return tmp_bindings


def IsEqualBindings(a, b):
  (granted, removed) = DiffBindings(a, b)
  return not granted.bindings and not removed.bindings


def DiffBindings(old, new):
  """Computes the difference between two BindingsValueListEntry lists.

  Args:
    old: The original list of BindingValuesListEntry instances
    new: The updated list of BindingValuesListEntry instances

  Returns:
    A pair of BindingsTuple instances, one for roles granted between old and
      new, and one for roles removed between old and new.
  """
  tmp_old = BindingsMessageToUpdateDict(old)
  tmp_new = BindingsMessageToUpdateDict(new)

  granted = BindingsMessageToUpdateDict([])
  removed = BindingsMessageToUpdateDict([])

  for (role, members) in six.iteritems(tmp_old):
    removed[role].update(members.difference(tmp_new[role]))
  for (role, members) in six.iteritems(tmp_new):
    granted[role].update(members.difference(tmp_old[role]))

  granted = [
      apitools_messages.Policy.BindingsValueListEntry(role=r, members=list(m))
      for (r, m) in six.iteritems(granted)
      if m
  ]
  removed = [
      apitools_messages.Policy.BindingsValueListEntry(role=r, members=list(m))
      for (r, m) in six.iteritems(removed)
      if m
  ]

  return (BindingsTuple(True, granted), BindingsTuple(False, removed))


def PatchBindings(base, diff, is_grant):
  """Patches a diff list of BindingsValueListEntry to the base.

  Will remove duplicate members for any given role on a grant operation.

  Args:
    base (dict): A dictionary returned by BindingsMessageToUpdateDict or
      BindingsDictToUpdateDict representing a resource's current
      IAM policy.
    diff (dict): A dictionary returned by BindingsMessageToUpdateDict or
      BindingsDictToUpdateDict representing the IAM policy bindings to
      add/remove from `base`.
    is_grant (bool): True if `diff` should be added to `base`, False
      if it should be removed from `base`.

  Returns:
    A {role: set(members)} dictionary created by applying `diff` to `base`.
  """
  # Patch the diff into base
  if is_grant:
    for (role, members) in six.iteritems(diff):
      if not role:
        raise CommandException('Role must be specified for a grant request.')
      base[role].update(members)
  else:
    for role in base:
      base[role].difference_update(diff[role])
      # Drop all members with the DROP_ALL role specifed from input.
      base[role].difference_update(diff[DROP_ALL])

  return {role: members for role, members in six.iteritems(base) if members}


def BindingStringToTuple(is_grant, input_str):
  """Parses an iam ch bind string to a list of binding tuples.

  Args:
    is_grant: If true, binding is to be appended to IAM policy; else, delete
              this binding from the policy.
    input_str: A string representing a member-role binding.
               e.g. user:foo@bar.com:objectAdmin
                    user:foo@bar.com:objectAdmin,objectViewer
                    user:foo@bar.com
                    allUsers
                    deleted:user:foo@bar.com?uid=123:objectAdmin,objectViewer
                    deleted:serviceAccount:foo@bar.com?uid=123

  Raises:
    CommandException in the case of invalid input.

  Returns:
    A BindingsDictTuple instance.
  """

  if not input_str.count(':'):
    input_str += ':'

  # Allows user specified PUBLIC_MEMBERS, DISCOURAGED_TYPES, and TYPES to be
  # case insensitive.
  tokens = input_str.split(":")
  public_members = {s.lower(): s for s in PUBLIC_MEMBERS}
  types = {s.lower(): s for s in TYPES}
  discouraged_types = {s.lower(): s for s in DISCOURAGED_TYPES}
  possible_public_member_or_type = tokens[0].lower()
  possible_type = '%s:%s' % (tokens[0].lower(), tokens[1].lower())

  if possible_public_member_or_type in public_members:
    tokens[0] = public_members[possible_public_member_or_type]
  elif possible_public_member_or_type in types:
    tokens[0] = types[possible_public_member_or_type]
  elif possible_public_member_or_type in discouraged_types:
    tokens[0] = discouraged_types[possible_public_member_or_type]
  elif possible_type in types:
    (tokens[0], tokens[1]) = types[possible_type].split(':')
  input_str = ":".join(tokens)

  # We can remove project convenience members, but not add them.
  removing_discouraged_type = not is_grant and tokens[0] in DISCOURAGED_TYPES

  if input_str.count(':') == 1:
    if '%s:%s' % (tokens[0], tokens[1]) in TYPES:
      raise CommandException('Incorrect public member type for binding %s' %
                             input_str)
    elif tokens[0] in PUBLIC_MEMBERS:
      (member, roles) = tokens
    elif tokens[0] in TYPES or removing_discouraged_type:
      member = input_str
      roles = DROP_ALL
    else:
      raise CommandException('Incorrect public member type for binding %s' %
                             input_str)
  elif input_str.count(':') == 2:
    if '%s:%s' % (tokens[0], tokens[1]) in TYPES:
      # case "deleted:user:foo@bar.com?uid=1234"
      member = input_str
      roles = DROP_ALL
    elif removing_discouraged_type:
      (member_type, project_id, roles) = tokens
      member = '%s:%s' % (member_type, project_id)
    else:
      (member_type, member_id, roles) = tokens
      _check_member_type(member_type, input_str)
      member = '%s:%s' % (member_type, member_id)
  elif input_str.count(':') == 3:
    # case "deleted:user:foo@bar.com?uid=1234:objectAdmin,objectViewer"
    (member_type_p1, member_type_p2, member_id, roles) = input_str.split(':')
    member_type = '%s:%s' % (member_type_p1, member_type_p2)
    _check_member_type(member_type, input_str)
    member = '%s:%s' % (member_type, member_id)
  else:
    raise CommandException('Invalid ch format %s' % input_str)

  if is_grant and not roles:
    raise CommandException('Must specify a role to grant.')

  roles = [ResolveRole(r) for r in roles.split(',')]

  bindings = [{'role': r, 'members': [member]} for r in set(roles)]
  return BindingsDictTuple(is_grant=is_grant, bindings=bindings)


def _check_member_type(member_type, input_str):
  if member_type in DISCOURAGED_TYPES:
    raise CommandException(DISCOURAGED_TYPES_MSG)
  elif member_type not in TYPES:
    raise CommandException('Incorrect member type for binding %s' % input_str)


def ResolveRole(role):
  if not role:
    return DROP_ALL
  if 'roles/' in role:
    return role
  return 'roles/storage.%s' % role
