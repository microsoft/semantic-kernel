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
"""Command to simulate a SHA custom module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scc.manage.sha import clients
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.manage import flags
from googlecloudsdk.command_lib.scc.manage import parsing


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
class Simulate(base.Command):
  """Command to simulate a SHA custom module.

  ## EXAMPLES

  To simulate a Security Health Analytics custom module with
  ID `123456` for organization `123`, run:

    $ {command} 123456
    --organization=123
    --custom-config-from-file=custom_config.yaml
    --resource-from-file=test.yaml

  To simulate a Security Health Analytics custom module with
  ID `123456` for folder `456`, run:

    $ {command} 123456
    --folder=456
    --custom-config-from-file=custom_config.yaml
    --resource-from-file=test.yaml

  To simulate a Security Health Analytics custom module with
  ID `123456` for project `789`, run:

    $ {command} 123456
    --project=789
    --custom-config-from-file=custom_config.yaml
    --resource-from-file=test.yaml

  You can also specify the parent more generally:

    $ {command} 123456
    --parent=organizations/123
    --custom-config-from-file=custom_config.yaml
    --resource-from-file=test.yaml

  Or just specify the fully qualified module name:

    $ {command}
    organizations/123/locations/global/effectiveSecurityHealthAnalyticsCustomModules/123456
    --custom-config-from-file=custom_config.yaml
    --resource-from-file=test.yaml
  """

  @staticmethod
  def Args(parser):
    flags.CreateParentFlag(required=True).AddToParser(parser)
    flags.CreateTestResourceFlag(required=True).AddToParser(parser)
    flags.CreateCustomConfigFlag(required=True).AddToParser(parser)

  def Run(self, args):
    parent = parsing.GetParentResourceNameFromArgs(args)
    custom_config = parsing.GetCustomConfigFromArgs(
        args.custom_config_from_file
    )
    resource = parsing.GetTestResourceFromArgs(args.resource_from_file)

    client = clients.SHACustomModuleClient()

    return client.Simulate(
        parent=parent, custom_config=custom_config, resource=resource
    )
