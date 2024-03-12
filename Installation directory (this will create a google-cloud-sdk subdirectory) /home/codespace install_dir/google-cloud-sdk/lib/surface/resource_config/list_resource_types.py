# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for listing all resources supported by bulk-export."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags as declarative_flags
from googlecloudsdk.command_lib.util.declarative.clients import declarative_client_base
from googlecloudsdk.command_lib.util.declarative.clients import kcc_client

try:
  # Python 3.3 and above.
  collections_abc = collections.abc
except AttributeError:
  collections_abc = collections


_DETAILED_HELP = {
    'EXAMPLES':
        """
    To list all exportable resource types, run:

      $ {command}

    To list all exportable resource types in yaml format, run:

      $ {command} --format=yaml

    To list all exportable resource types in project `my-project` in json format, run:

      $ {command} --format=json --project=my-project
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListResources(base.DeclarativeCommand):
  """List all resources supported by bulk-export."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    declarative_flags.AddListResourcesFlags(parser)
    parser.display_info.AddFormat(declarative_client_base.RESOURCE_LIST_FORMAT)

  def Run(self, args):
    client = kcc_client.KccClient()
    output = client.ListResources(project=args.project,
                                  organization=args.organization,
                                  folder=args.folder)
    return output
