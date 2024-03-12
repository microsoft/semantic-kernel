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
"""The command to update Policy Controller Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import command
from googlecloudsdk.command_lib.container.fleet.policycontroller import flags


class Update(base.UpdateCommand, command.PocoCommand):
  """Updates the configuration of Policy Controller Feature.

  Updates the configuration of the Policy Controller installation
  ## EXAMPLES

  To change the installed version, run:

    $ {command} --version=VERSION

  To modify the audit interval to 120 seconds, run:

    $ {command} --audit-interval=120
  """

  feature_name = 'policycontroller'

  @classmethod
  def Args(cls, parser):
    modal_group = parser.add_argument_group(mutex=False)
    membership_group = modal_group.add_argument_group(mutex=True)
    scope_flags = flags.PocoFlags(modal_group, 'update')
    config_group = membership_group.add_argument_group(mutex=False)
    manual_flags = flags.PocoFlags(config_group, 'update')

    # Scope Flags
    scope_flags.add_memberships()

    # Configuration Flags
    manual_flags.add_audit_interval()
    manual_flags.add_constraint_violation_limit()
    manual_flags.add_exemptable_namespaces()
    manual_flags.add_log_denies_enabled()
    manual_flags.add_monitoring()
    manual_flags.add_mutation()
    manual_flags.add_referential_rules()
    manual_flags.add_version()

    # Configuration origin flag
    flags.origin_flag().AddToParser(membership_group)

  def Run(self, args):
    parser = flags.PocoFlagParser(args, self.messages)
    specs = self.path_specs(args)
    updated_specs = {path: self.update(s, parser) for path, s in specs.items()}
    return self.update_specs(updated_specs)

  def feature_cache(self, refresh: bool = False):
    """Gets and caches the current feature for this object."""
    cache = getattr(self, '__feature_cache', None)
    if cache is None or refresh:
      cache = self.GetFeature()
      setattr(self, '__feature_cache', cache)
    return cache

  def update(self, spec: messages.Message, parser: flags.PocoFlagParser):
    if parser.use_default_cfg():
      parser.set_default_cfg(self.feature_cache(), spec)
    else:
      pc = spec.policycontroller
      pc = parser.update_version(pc)

      hub_cfg = pc.policyControllerHubConfig
      hub_cfg = parser.update_audit_interval(hub_cfg)
      hub_cfg = parser.update_constraint_violation_limit(hub_cfg)
      hub_cfg = parser.update_exemptable_namespaces(hub_cfg)
      hub_cfg = parser.update_log_denies(hub_cfg)
      hub_cfg = parser.update_mutation(hub_cfg)
      hub_cfg = parser.update_monitoring(hub_cfg)
      hub_cfg = parser.update_referential_rules(hub_cfg)

      pc.policyControllerHubConfig = hub_cfg
      spec.policycontroller = pc
    return spec
