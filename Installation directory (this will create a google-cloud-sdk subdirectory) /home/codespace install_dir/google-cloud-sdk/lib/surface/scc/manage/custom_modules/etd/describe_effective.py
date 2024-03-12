# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to get a ETD effective custom module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc.manage.etd import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.manage import constants
from googlecloudsdk.command_lib.scc.manage import flags
from googlecloudsdk.command_lib.scc.manage import parsing


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class DescribeEffective(base.DescribeCommand):
  """Get the effective details of a Event Threat Detection effective custom module.

  Get the effective details of a Event Threat Detection effective custom module.
  It retrieves a custom module with its effective enablement state.

  ## EXAMPLES

  To get the effective details of a Event Threat Detection custom module with ID
  `123456` for organization `123`, run:

    $ {command} 123456 --organization=123

  To get the effective details of a Event Threat Detection custom module with ID
  `123456` for folder `456`, run:

    $ {command} 123456 --folder=456

  To get the effective details of a Event Threat Detection custom module with ID
  `123456` for project `789`, run:

    $ {command} 123456 --project=789

  You can also specify the parent more generally:

    $ {command} 123456 --parent=organizations/123

  Or just specify the fully qualified module name:

    $ {command}
    organizations/123/locations/global/effectiveEventThreatDetectionCustomModules/123456
  """

  @staticmethod
  def Args(parser):
    flags.CreateModuleIdOrNameArg(
        module_type=constants.CustomModuleType.EFFECTIVE_ETD
        ).AddToParser(parser)
    flags.CreateParentFlag(required=False).AddToParser(parser)

  def Run(self, args):
    name = parsing.GetModuleNameFromArgs(
        args, module_type=constants.CustomModuleType.EFFECTIVE_ETD
    )

    client = clients.EffectiveETDCustomModuleClient()

    return client.Get(name)
