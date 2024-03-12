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
"""Command to update a ETD custom module."""

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
class Update(base.Command):
  """Update an Event Threat Detection custom module.

  ## EXAMPLES

  To update an Event Threat Detection custom module with ID 123456 for
  organization 123, run:

      $ {command} 123456
          --organization=organizations/123 --enablement-state="ENABLED"
          --custom-config-file=custom_config.json
  """

  @staticmethod
  def Args(parser):
    flags.CreateModuleIdOrNameArg(
        module_type=constants.CustomModuleType.ETD
    ).AddToParser(parser)
    flags.CreateParentFlag(required=False).AddToParser(parser)
    flags.CreateValidateOnlyFlag(required=False).AddToParser(parser)
    flags.CreateUpdateFlags(
        required=True,
        module_type=constants.CustomModuleType.ETD,
        file_type='JSON',
    ).AddToParser(parser)

  def Run(self, args):
    name = parsing.GetModuleNameFromArgs(
        args, module_type=constants.CustomModuleType.ETD
    )

    validate_only = args.validate_only
    custom_config = parsing.GetConfigValueFromArgs(args.custom_config_file)
    enablement_state = parsing.GetEnablementStateFromArgs(
        args.enablement_state, module_type=constants.CustomModuleType.ETD
    )
    update_mask = parsing.CreateUpdateMaskFromArgs(args)

    if not validate_only:
      console_io.PromptContinue(
          message=(
              'Are you sure you want to update the Event Threat Detection'
              ' custom module {}?\n'.format(name)
          ),
          cancel_on_no=True,
      )
    client = clients.ETDCustomModuleClient()

    return client.Update(
        name=name,
        validate_only=validate_only,
        custom_config=custom_config,
        enablement_state=enablement_state,
        update_mask=update_mask,
    )
