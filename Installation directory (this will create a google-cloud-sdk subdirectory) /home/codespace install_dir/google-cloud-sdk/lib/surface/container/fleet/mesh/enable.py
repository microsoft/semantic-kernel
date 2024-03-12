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
"""The command to enable Service Mesh Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.mesh import utils


class Enable(base.EnableCommand):
  """Enable Service Mesh Feature.

  Enable the Service Mesh Feature in a fleet.

  ## EXAMPLES

  To enable the Service Mesh Feature, run:

    $ {command}

  To enable the Service Mesh Feature with a fleet-level default Membership
  configuration, run:

    $ {command} --fleet-default-member-config=/path/to/service-mesh.yaml
  """

  feature_name = 'servicemesh'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--fleet-default-member-config',
        type=str,
        help="""The path to a service-mesh.yaml configuration file.

        To enable the Service Mesh Feature with a fleet-level default
        membership configuration, run:

          $ {command} --fleet-default-member-config=/path/to/service-mesh.yaml""",
    )

  def Run(self, args):
    empty_feature = self.messages.Feature()

    # Run enable with an empty feature if the fleet_default_member_config
    # is not specified
    if not args.fleet_default_member_config:
      return self.Enable(empty_feature)

    # Load config YAML file.
    loaded_config = file_parsers.YamlConfigFile(
        file_path=args.fleet_default_member_config,
        item_type=utils.FleetDefaultMemberConfigObject,
    )

    # Create new service mesh feature spec.
    member_config = utils.ParseFleetDefaultMemberConfig(
        loaded_config, self.messages
    )

    # Create a feature object that has a default fleet member config
    feature = self.messages.Feature(
        fleetDefaultMemberConfig=self.messages.CommonFleetDefaultMemberConfigSpec(
            mesh=member_config
        )
    )

    return self.Enable(feature)
