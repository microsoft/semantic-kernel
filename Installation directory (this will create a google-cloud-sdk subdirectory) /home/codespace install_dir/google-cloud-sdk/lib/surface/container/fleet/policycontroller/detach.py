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
"""The command to detach the Policy Controller webhooks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


class Detach(base.UpdateCommand, command.PocoCommand):
  """Detach Policy Controller Feature.

  Detaches Policy Controller. This will halt all administration of the Policy
  Controller installation by the GKE Fleet. It will not uninstall it from the
  cluster. To re-attach Policy Controller, use the `enable` command.


  ## EXAMPLES

  To detach Policy Controller, run:

    $ {command}

  To re-attach Policy Controller, use the `enable` command:

    $ {parent_command} enable
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = flags.PocoFlags(parser, 'detach')
    cmd_flags.add_memberships()

  def Run(self, args):
    specs = self.path_specs(args)
    updated_specs = {path: self.detach(spec) for path, spec in specs.items()}
    return self.update_specs(updated_specs)

  def detach(self, spec):
    """Sets the membership spec to DETACHED.

    Args:
      spec: The spec to be detached.

    Returns:
      Updated spec, based on the message api version.
    """
    spec.policycontroller.policyControllerHubConfig.installSpec = (
        self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum.INSTALL_SPEC_DETACHED
    )
    return spec
