# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Commonly used display formats."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.secrets import args as secrets_args

_LOCATION_TABLE = """
table(
  name.basename():label=NAME,
  displayName:label=LOCATION
)
"""

_SECRET_DATA = """
value[terminator="",private](
  payload.data.decode(base64).decode(utf8)
)
"""

_SECRET_TABLE = """
table(
  name.basename():label=NAME,
  createTime.date():label=CREATED,
  policy_transform():label=REPLICATION_POLICY,
  locations_transform():label=LOCATIONS
)
"""

_REGIONAL_SECRET_TABLE = """
table(
  name.basename():label=NAME,
  createTime.date():label=CREATED
)
"""

_VERSION_TABLE = """
table(
  name.basename():label=NAME,
  state.enum(secrets.StateVersionJobState).color('destroyed', 'disabled', 'enabled', 'unknown'):label=STATE,
  createTime.date():label=CREATED,
  destroyTime.date(undefined='-'):label=DESTROYED
)
"""

_VERSION_STATE_TRANSFORMS = {
    'secrets.StateVersionJobState::enum': {
        'STATE_UNSPECIFIED': 'unknown',
        'ENABLED': 'enabled',
        'DISABLED': 'disabled',
        'DESTROYED': 'destroyed',
    }
}


def _TransformReplicationPolicy(r):
  if 'replication' not in r:
    return 'ERROR'
  if 'automatic' in r['replication']:
    return 'automatic'
  if 'userManaged' in r['replication']:
    return 'user_managed'
  return 'ERROR'


def _TransformLocations(r):
  if 'replication' not in r:
    return 'ERROR'
  if 'automatic' in r['replication']:
    return '-'
  if 'userManaged' in r['replication'] and 'replicas' in r['replication'][
      'userManaged']:
    locations = []
    for replica in r['replication']['userManaged']['replicas']:
      locations.append(replica['location'])
    return ','.join(locations)
  return 'ERROR'

_SECRET_TRANSFORMS = {
    'policy_transform': _TransformReplicationPolicy,
    'locations_transform': _TransformLocations
}


def UseLocationTable(parser):
  parser.display_info.AddFormat(_LOCATION_TABLE)
  parser.display_info.AddUriFunc(
      lambda r: secrets_args.ParseLocationRef(r.name).SelfLink())


def UseSecretTable(parser):
  parser.display_info.AddFormat(_SECRET_TABLE)
  parser.display_info.AddTransforms(_SECRET_TRANSFORMS)
  parser.display_info.AddUriFunc(
      lambda r: secrets_args.ParseSecretRef(r.name).SelfLink())


def SecretTableUsingArgument(args):
  """Table format to display global secrets.

  Args:
    args: arguments interceptor
  """
  args.GetDisplayInfo().AddFormat(_SECRET_TABLE)
  args.GetDisplayInfo().AddTransforms(_SECRET_TRANSFORMS)
  args.GetDisplayInfo().AddUriFunc(
      lambda r: secrets_args.ParseSecretRef(r.name).SelfLink()
  )


def RegionalSecretTableUsingArgument(args):
  """Table format to display regional secrets.

  Args:
    args: arguments interceptor
  """
  args.GetDisplayInfo().AddFormat(_REGIONAL_SECRET_TABLE)
  args.GetDisplayInfo().AddTransforms(_SECRET_TRANSFORMS)
  args.GetDisplayInfo().AddUriFunc(
      lambda r: secrets_args.ParseRegionalSecretRef(r.name).SelfLink()
  )


def UseSecretData(parser):
  parser.display_info.AddFormat(_SECRET_DATA)


def UseVersionTable(parser):
  parser.display_info.AddFormat(_VERSION_TABLE)
  parser.display_info.AddTransforms(_VERSION_STATE_TRANSFORMS)
  parser.display_info.AddUriFunc(
      lambda r: secrets_args.ParseVersionRef(r.name).SelfLink())
