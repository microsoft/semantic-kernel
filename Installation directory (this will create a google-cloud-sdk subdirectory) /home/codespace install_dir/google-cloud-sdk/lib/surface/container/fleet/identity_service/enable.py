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
"""The command to enable Identity Service Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.identity_service import utils

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = """\
    To enable the Identity Service Feature, run:

    $ {command}

    To enable the Identity Service Feature with a fleet-level default membership configuration, run:

    $ {command} --fleet-default-member-config=/path/to/identity-service.yaml
"""


class Enable(base.EnableCommand):
  """Enable the Identity Service Feature.

  This command enables the Identity Service Feature in a fleet.
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'identityservice'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--fleet-default-member-config',
        type=str,
        help="""The path to an identity-service.yaml identity configuration
        file. If specified, this configuration would be the default Identity
        Service configuration for all memberships in your fleet. It could be
        overridden with a membership-specific configuration by using the
        the `Apply` command with the `--config` argument.

        To enable the Identity Service Feature with a fleet-level default
        membership configuration, run:

          $ {command} --fleet-default-member-config=/path/to/identity-service.yaml""",
    )

  def Run(self, args):
    if not args.fleet_default_member_config:
      return self.Enable(self.messages.Feature())

    # Load config YAML file.
    loaded_config = file_parsers.YamlConfigFile(
        file_path=args.fleet_default_member_config,
        item_type=file_parsers.LoginConfigObject)

    # Create new identity service feature spec.
    member_config = utils.parse_config(loaded_config, self.messages)

    # Create a feature object that has a default fleet identity service config
    feature = self.messages.Feature(
        fleetDefaultMemberConfig=self.messages
        .CommonFleetDefaultMemberConfigSpec(identityservice=member_config))

    return self.Enable(feature)
