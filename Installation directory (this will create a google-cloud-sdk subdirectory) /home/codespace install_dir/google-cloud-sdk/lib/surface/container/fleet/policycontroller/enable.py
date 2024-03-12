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
"""The command to enable Policy Controller Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


class Enable(base.UpdateCommand, base.EnableCommand, command.PocoCommand):
  """Enable Policy Controller Feature.

  Enables the Policy Controller Feature in a fleet.

  ## EXAMPLES

  To enable the Policy Controller Feature, run:

    $ {command}
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    top_group = parser.add_argument_group(mutex=True)
    flags.fleet_default_cfg_group().AddToParser(top_group)

    modal_group = top_group.add_argument_group(mutex=False)
    membership_group = modal_group.add_argument_group(mutex=True)
    scope_flags = flags.PocoFlags(modal_group, 'enable')
    config_group = membership_group.add_argument_group(mutex=False)
    manual_flags = flags.PocoFlags(config_group, 'config')

    # Scope Flags
    scope_flags.add_memberships()

    # Configuration Flags
    manual_flags.add_audit_interval()
    manual_flags.add_constraint_violation_limit()
    manual_flags.add_exemptable_namespaces()
    manual_flags.add_log_denies_enabled()
    manual_flags.add_monitoring()
    manual_flags.add_mutation()
    manual_flags.add_no_default_bundles()
    manual_flags.add_referential_rules()
    manual_flags.add_version()

  def Run(self, args):
    parser = flags.PocoFlagParser(args, self.messages)
    if parser.is_feature_update():
      self._configure_feature(parser)
    else:  # Otherwise we are updating memberships.
      specs = self.path_specs(args, True)
      updated_specs = {p: self.enable(s, parser) for p, s in specs.items()}
      self.update_specs(updated_specs)

  def _configure_feature(self, parser):
    default_cfg = parser.load_fleet_default_cfg()
    if default_cfg is None:
      # The remove case has been selected
      self.update_fleet_default(None)
    else:
      self.update_fleet_default(default_cfg)

  def _get_hub_config(self, spec: messages.Message) -> messages.Message:
    if spec.policyControllerHubConfig is None:
      return self.messages.PolicyControllerHubConfig()
    return spec.policyControllerHubConfig

  def _get_policycontroller(self, spec: messages.Message) -> messages.Message:
    if spec.policycontroller is None:
      return self.messages.PolicyControllerMembershipSpec()
    return spec.policycontroller

  def enable(self, spec, parser):
    pc = self._get_policycontroller(spec)
    hub_cfg = self._get_hub_config(pc)
    hub_cfg = parser.update_audit_interval(hub_cfg)
    hub_cfg = parser.update_constraint_violation_limit(hub_cfg)
    hub_cfg = parser.update_exemptable_namespaces(hub_cfg)
    hub_cfg = parser.update_log_denies(hub_cfg)
    hub_cfg = parser.update_mutation(hub_cfg)
    hub_cfg = parser.update_monitoring(hub_cfg)
    hub_cfg = parser.update_referential_rules(hub_cfg)
    hub_cfg.installSpec = (
        self.messages.PolicyControllerHubConfig.InstallSpecValueValuesEnum.INSTALL_SPEC_ENABLED
    )
    # If this is a first installation, attempt to inject default bundle.
    if spec.policycontroller is None:
      hub_cfg = parser.update_default_bundles(hub_cfg)
    pc.policyControllerHubConfig = hub_cfg
    pc = parser.update_version(pc)
    spec.policycontroller = pc
    return spec
