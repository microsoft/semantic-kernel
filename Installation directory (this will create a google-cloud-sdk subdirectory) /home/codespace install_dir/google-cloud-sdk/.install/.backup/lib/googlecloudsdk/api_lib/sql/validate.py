# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Common sql utility functions for validating."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.api_lib.sql import instances as api_util

from googlecloudsdk.calliope import exceptions


def ValidateInstanceName(instance_name):
  if ':' in instance_name:
    name_components = instance_name.split(':')
    possible_project = name_components[0]
    possible_instance = name_components[-1]
    raise sql_exceptions.ArgumentError("""\
Instance names cannot contain the ':' character. If you meant to indicate the
project for [{instance}], use only '{instance}' for the argument, and either add
'--project {project}' to the command line or first run
  $ gcloud config set project {project}
""".format(project=possible_project, instance=possible_instance))


def ValidateURI(uri, recovery_only):
  if (uri is None or not uri) and (not recovery_only):
    raise sql_exceptions.ArgumentError("""\
missing URI arg, please include URI arg or set the recovery-only flag if you meant to bring database online only
""")


def ValidateInstanceLocation(args):
  """Construct a Cloud SQL instance from command line args.

  Args:
    args: argparse.Namespace, The CLI arg namespace.

  Raises:
    RequiredArgumentException: Zone is required.
    ConflictingArgumentsException: Zones in arguments belong to different
    regions.
  """

  if args.IsSpecified('secondary_zone') and not args.IsSpecified('zone'):
    raise exceptions.RequiredArgumentException(
        '--zone', '`--zone` is required if --secondary-zone is used '
        'while creating an instance.')

  if args.IsSpecified('secondary_zone') and args.IsSpecified('zone'):
    if args.zone == args.secondary_zone:
      raise exceptions.ConflictingArgumentsException(
          'Zones in arguments --zone and --secondary-zone are identical.')

    region_from_zone = api_util.GetRegionFromZone(args.zone)
    region_from_secondary_zone = api_util.GetRegionFromZone(
        args.secondary_zone)
    if region_from_zone != region_from_secondary_zone:
      raise exceptions.ConflictingArgumentsException(
          'Zones in arguments --zone and --secondary-zone '
          'belong to different regions.')
