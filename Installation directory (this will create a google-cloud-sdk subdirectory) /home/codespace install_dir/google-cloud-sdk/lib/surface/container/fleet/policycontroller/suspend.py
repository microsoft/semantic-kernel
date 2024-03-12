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
"""The command to suspend the Policy Controller webhooks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


class Suspend(base.UpdateCommand, command.PocoCommand):
  """Suspend Policy Controller Feature.

  Suspends the Policy Controller. This will disable all kubernetes webhooks on
  the configured cluster, thereby removing admission and mutation functionality.
  Audit functionality will remain in place.

  ## EXAMPLES

  To suspend Policy Controller, run:

    $ {command}

  To re-enable Policy Controller webhooks, use the `enable` command:

    $ {parent_command} enable
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    cmd_flags = flags.PocoFlags(parser, 'suspend')
    cmd_flags.add_memberships()

  def Run(self, args):
    specs = self.path_specs(args)
    updated_specs = {
        path: self.suspend(spec) for path, spec in specs.items()
    }
    return self.update_specs(updated_specs)

  def suspend(self, spec):
    """Sets the membership spec to SUSPENDED.

    Args:
      spec: The spec to be suspended.

    Returns:
      Updated spec, based on message api version.
    """
    spec.policycontroller.policyControllerHubConfig.installSpec = (
        self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum.INSTALL_SPEC_SUSPENDED
    )
    return spec
