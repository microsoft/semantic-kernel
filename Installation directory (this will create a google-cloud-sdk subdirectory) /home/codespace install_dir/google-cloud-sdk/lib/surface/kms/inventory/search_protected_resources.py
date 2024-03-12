# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Searches the protected resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kmsinventory import inventory
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args
from googlecloudsdk.command_lib.resource_manager import completers

DETAILED_HELP = {
    'DESCRIPTION': """
         *{command}* returns a list of the resources a key is protecting
         within the specified organization.
       """,
    'EXAMPLES': """
         To view the protected resources for the key `puppy` and organization
         number `1234` run:

           $ {command} --keyname=puppy --scope=1234
       """,
}


RESOURCE_TYPE_HELP = """\
A list of resource types that this request searches for. If empty, it will
search all the [trackable resource types](https://cloud.google.com/kms/docs/view-key-usage#tracked-resource-types).

Regular expressions are also supported. For example:

  * ``compute.googleapis.com.*'' snapshots resources whose type
    starts with ``compute.googleapis.com''.
  * ``.*Image'' snapshots resources whose type ends with
    ``Image''.
  * ``.*Image.*'' snapshots resources whose type contains
    ``Image''.

See [RE2](https://github.com/google/re2/wiki/Syntax) for all supported
regular expression syntax. If the regular expression does not match any
supported resource type, an ``INVALID_ARGUMENT'' error will be returned.
"""


class SearchProtectedResources(base.ListCommand):
  """Searches the resources protected by a key."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyResourceArgForKMS(parser, True, '--keyname')
    parser.add_argument(
        '--scope',
        metavar='ORGANIZATION_ID',
        completer=completers.OrganizationCompleter,
        required=True,
        help='Organization ID.')
    parser.add_argument(
        '--resource-types',
        metavar='RESOURCE_TYPES',
        type=arg_parsers.ArgList(),
        help=RESOURCE_TYPE_HELP,
    )

  def Run(self, args):
    key_name = args.keyname
    org = args.scope
    resource_types = args.resource_types
    if not resource_types:
      resource_types = []
    return inventory.SearchProtectedResources(
        scope=org, key_name=key_name, resource_types=resource_types, args=args
    )
