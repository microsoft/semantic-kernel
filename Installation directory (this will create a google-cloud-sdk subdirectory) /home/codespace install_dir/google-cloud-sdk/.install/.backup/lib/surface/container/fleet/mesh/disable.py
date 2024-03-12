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
"""The command to disable the Service Mesh Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base


class Disable(base.UpdateCommand, base.DisableCommand):
  """Disable Service Mesh Feature.

  Disable the Service Mesh Feature in a fleet.

  ## EXAMPLES

  To disable the Service Mesh Feature, run:

    $ {command}

  To delete the fleet-level default Membership configuration, run:

    $ {command} --fleet-default-member-config
  """

  feature_name = 'servicemesh'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--fleet-default-member-config',
        action='store_true',
        help="""If specified, deletes the default membership
        configuration present in your fleet.

        To delete the fleet-level default Membership configuration present in
        your fleet, run:

          $ {command} --fleet-default-member-config""",
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help=(
            'Disable this feature, even if it is currently in use. '
            'Force disablement may result in unexpected behavior.'
        ),
    )

  def Run(self, args):
    # Clear the fleet_default_member_config if the
    # fleet_default_member_config flag is set to true.
    if args.fleet_default_member_config:
      patch = self.messages.Feature(name=self.FeatureResourceName())
      self.Update(['fleet_default_member_config'], patch)
    else:
      self.Disable(force=args.force)
