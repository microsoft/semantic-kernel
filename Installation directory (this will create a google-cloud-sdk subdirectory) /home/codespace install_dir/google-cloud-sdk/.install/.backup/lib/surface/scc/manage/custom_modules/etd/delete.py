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
"""Command to delete a ETD custom module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc.manage.etd import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.manage import constants
from googlecloudsdk.command_lib.scc.manage import flags
from googlecloudsdk.command_lib.scc.manage import parsing
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an Event Threat Detection custom module.

  Delete a Event Threat Detection custom module. User specifies the custom
  module as well as the parent of the module to delete. A validation_only flag
  is optional. When set to true only validations (including IAM checks) will
  done for the request (module will not be deleted).

  ## EXAMPLES

  To delete an Event Threat Detection custom module with ID
  `123456` for organization `123`, run:

    $ {command} 123456 --organization=123

  To delete a Event Threat Detection custom module with ID
  `123456` for folder `456`, run:

    $ {command} 123456 --folder=456

  To delete a Event Threat Detection custom module with ID
  `123456` for project `789`, run:

    $ {command} 123456 --project=789

  You can also specify the parent more generally:

    $ {command} 123456 --parent=organizations/123

  Or just specify the fully qualified module name:

    $ {command}
    organizations/123/locations/global/eventThreatDetectionCustomModules/123456
  """

  @staticmethod
  def Args(parser):
    flags.CreateModuleIdOrNameArg(
        module_type=constants.CustomModuleType.ETD
    ).AddToParser(parser)
    flags.CreateParentFlag(required=False).AddToParser(parser)
    flags.CreateValidateOnlyFlag(required=False).AddToParser(parser)

  def Run(self, args):
    name = parsing.GetModuleNameFromArgs(
        args, module_type=constants.CustomModuleType.ETD
    )

    validate_only = args.validate_only

    if not validate_only:
      console_io.PromptContinue(
          message=(
              'Are you sure you want to delete the Event Threat Detection'
              ' custom module {}?\n'.format(name)
          ),
          cancel_on_no=True,
      )

    client = clients.ETDCustomModuleClient()

    return client.Delete(name=name, validate_only=validate_only)
