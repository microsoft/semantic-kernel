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
"""Command to validate an ETD custom module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc.manage.etd import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.manage import flags
from googlecloudsdk.command_lib.scc.manage import parsing


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class Validate(base.Command):
  """Command to validate an ETD custom module.

  ## EXAMPLES

  To validate an Event Threat Detection custom module 'config.json' with a
  module type 'CONFIGURABLE_BAD_IP', run:

    $ {command}
      --organization=organizations/252600681248
      --custom-config-file=config.json
      --module-type=CONFIGURABLE_BAD_IP

  You can also specify the parent more generally:

    $ {command}
      --parent=organizations/252600681248
      --custom-config-file=config.json
      --module-type=CONFIGURABLE_BAD_IP
  """

  @staticmethod
  def Args(parser):
    flags.CreateParentFlag(required=True).AddToParser(parser)
    flags.CreateEtdCustomConfigFilePathFlag(required=True).AddToParser(parser)
    flags.CreateModuleTypeFlag(required=True).AddToParser(parser)

  def Run(self, args):
    parent = parsing.GetParentResourceNameFromArgs(args)
    custom_config = parsing.ParseJSONFile(args.custom_config_file)
    module_type = args.module_type

    client = clients.ETDCustomModuleClient()

    return client.Validate(
        parent=parent, custom_config_json=custom_config, module_type=module_type
    )
