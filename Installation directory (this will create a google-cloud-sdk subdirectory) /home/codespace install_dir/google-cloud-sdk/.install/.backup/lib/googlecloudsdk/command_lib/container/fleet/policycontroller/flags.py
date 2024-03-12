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
"""Functions to add standardized flags in PoCo commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from os import path

from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.container.fleet.policycontroller import protos
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.policycontroller import constants
from googlecloudsdk.command_lib.container.fleet.policycontroller import exceptions
from googlecloudsdk.command_lib.export import util
from googlecloudsdk.core.console import console_io

DEFAULT_BUNDLE_NAME = 'policy-essentials-v2022'


def fleet_default_cfg_flag():
  return base.Argument(
      '--fleet-default-member-config',
      type=str,
      help="""The path to a policy-controller.yaml configuration
        file. If specified, this configuration will become the default Policy
        Controller configuration for all memberships in your fleet. It can be
        overridden with a membership-specific configuration by using the
        the `Update` command.

        To enable the Policy Controller Feature with a fleet-level default
        membership configuration, run:

          $ {command} --fleet-default-member-config=/path/to/policy-controller.yaml
      """,
  )


def no_fleet_default_cfg_flag(include_no: bool = False):
  """Flag for unsetting fleet default configuration."""
  flag = '--{}fleet-default-member-config'.format('no-' if include_no else '')
  return base.Argument(
      flag,
      action='store_true',
      help="""Removes the fleet default configuration for policy controller.
      Memberships configured with the fleet default will maintain their current
      configuration.

          $ {} {}
      """.format('{command}', flag),
  )


def fleet_default_cfg_group():
  """Flag group for accepting a Fleet Default Configuration file."""
  config_group = base.ArgumentGroup(
      'Flags for setting Fleet Default Configuration files.', mutex=True
  )
  config_group.AddArgument(fleet_default_cfg_flag())
  config_group.AddArgument(no_fleet_default_cfg_flag(True))
  return config_group


def origin_flag():
  """Builds flag for setting configuration to the fleet default."""
  return base.Argument(
      '--origin',
      choices=['FLEET'],
      type=str,
      help="""If --origin=FLEET will set the configuration of the membership to
      the fleet default.
      """,
  )


class PocoFlags:
  """Handle common flags for Poco Commands.

  Use this class to keep command flags that touch similar configuration options
  on the Policy Controller feature in sync across commands.
  """

  def __init__(
      self,
      parser: parser_arguments.ArgumentInterceptor,
      command: str,
  ):
    """Constructor.

    Args:
      parser: The argparse parser to add flags to.
      command: The command using this flag utility. i.e. 'enable'.
    """
    self._parser = parser
    self._display_name = command

  @property
  def parser(self):  # pylint: disable=invalid-name
    return self._parser

  @property
  def display_name(self):
    return self._display_name

  def add_audit_interval(self):
    """Adds handling for audit interval configuration changes."""
    self.parser.add_argument(
        '--audit-interval',
        type=int,
        help='How often Policy Controller will audit resources, in seconds.',
    )

  def add_constraint_violation_limit(self):
    """Adds handling for constraint violation limit configuration changes."""
    self.parser.add_argument(
        '--constraint-violation-limit',
        type=int,
        help=(
            'The number of violations stored on the constraint resource. Must'
            ' be greater than 0.'
        ),
    )

  def add_exemptable_namespaces(self):
    """Adds handling for configuring exemptable namespaces."""
    group = self.parser.add_argument_group(
        'Exemptable Namespace flags.', mutex=True
    )
    group.add_argument(
        '--exemptable-namespaces',
        type=str,
        help=(
            'Namespaces that Policy Controller should ignore, separated by'
            ' commas if multiple are supplied.'
        ),
    )
    group.add_argument(
        '--clear-exemptable-namespaces',
        action='store_true',
        help=(
            'Removes any namespace exemptions, enabling Policy Controller on'
            ' all namespaces. Setting this flag will overwrite'
            ' currently exempted namespaces, not append.'
        ),
    )

  def add_log_denies_enabled(self):
    """Adds handling for log denies enablement."""
    group = self.parser.add_group('Log Denies flags.', mutex=True)
    group.add_argument(
        '--no-log-denies',
        action='store_true',
        help='If set, disable all log denies.',
    )
    group.add_argument(
        '--log-denies',
        action='store_true',
        help=(
            'If set, log all denies and dry run failures. (To disable, use'
            ' --no-log-denies)'
        ),
    )

  def add_memberships(self):
    """Adds handling for single, multiple or all memberships."""
    group = self.parser.add_argument_group('Membership flags.', mutex=True)
    resources.AddMembershipResourceArg(
        group,
        plural=True,
        membership_help=(
            'The membership names to act on, separated by commas if multiple '
            'are supplied. Ignored if --all-memberships is supplied; if '
            'neither is supplied, a prompt will appear with all available '
            'memberships.'
        ),
    )

    group.add_argument(
        '--all-memberships',
        action='store_true',
        help=(
            'If supplied, apply to all Policy Controllers memberships in the'
            ' fleet.'
        ),
        default=False,
    )

  def add_monitoring(self):
    """Adds handling for monitoring configuration changes."""
    group = self.parser.add_argument_group('Monitoring flags.', mutex=True)
    group.add_argument(
        '--monitoring',
        type=str,
        help=(
            'Monitoring backend options Policy Controller should export metrics'
            ' to, separated by commas if multiple are supplied.  Setting this'
            ' flag will overwrite currently enabled backends, not append.'
            ' Options: {}'.format(', '.join(constants.MONITORING_BACKENDS))
        ),
    )
    group.add_argument(
        '--no-monitoring',
        action='store_true',
        help=(
            'Include this flag to disable the monitoring configuration of'
            ' Policy Controller.'
        ),
    )

  def add_mutation(self):
    """Adds handling for mutation enablement."""
    group = self.parser.add_group('Mutation flags.', mutex=True)
    group.add_argument(
        '--no-mutation', action='store_true', help='Disables mutation support.'
    )
    group.add_argument(
        '--mutation',
        action='store_true',
        help=(
            'If set, enable support for mutation. (To disable, use'
            ' --no-mutation)'
        ),
    )

  def add_no_default_bundles(self):
    self.parser.add_argument(
        '--no-default-bundles',
        action='store_true',
        help='If set, skip installing the default bundle of policy-essentials.',
    )

  def add_referential_rules(self):
    """Adds handling for referential rules enablement."""
    group = self.parser.add_group('Referential Rules flags.', mutex=True)
    group.add_argument(
        '--no-referential-rules',
        action='store_true',
        help='Disables referential rules support.',
    )
    group.add_argument(
        '--referential-rules',
        action='store_true',
        help=(
            'If set, enable support for referential constraints. (To disable,'
            ' use --no-referential-rules)'
        ),
    )

  def add_version(self):
    """Adds handling for version flag."""
    self.parser.add_argument(
        '--version',
        type=str,
        help=(
            'The version of Policy Controller to install; defaults to latest'
            ' version.'
        ),
    )


class PocoFlagParser:
  """Converts PocoFlag arguments to internal representations.

  hub_cfg references the PolicyControllerHubConfig object in:
  third_party/py/googlecloudsdk/generated_clients/apis/gkehub/v1alpha/gkehub_v1alpha_messages.py
  """

  def __init__(self, args: parser_extensions.Namespace, msgs):
    self.args = args
    self.messages = msgs

  def update_audit_interval(
      self, hub_cfg: messages.Message
  ) -> messages.Message:
    if self.args.audit_interval:
      hub_cfg.auditIntervalSeconds = self.args.audit_interval
    return hub_cfg

  def update_constraint_violation_limit(
      self, hub_cfg: messages.Message
  ) -> messages.Message:
    if self.args.constraint_violation_limit:
      hub_cfg.constraintViolationLimit = self.args.constraint_violation_limit
    return hub_cfg

  def update_exemptable_namespaces(
      self, hub_cfg: messages.Message
  ) -> messages.Message:
    if self.args.clear_exemptable_namespaces:
      namespaces = []
      hub_cfg.exemptableNamespaces = namespaces
    if self.args.exemptable_namespaces:
      namespaces = self.args.exemptable_namespaces.split(',')
      hub_cfg.exemptableNamespaces = namespaces
    return hub_cfg

  def update_log_denies(self, hub_cfg: messages.Message) -> messages.Message:
    if self.args.log_denies:
      hub_cfg.logDeniesEnabled = True
    if self.args.no_log_denies:
      hub_cfg.logDeniesEnabled = False
    return hub_cfg

  def update_mutation(self, hub_cfg: messages.Message) -> messages.Message:
    if self.args.mutation:
      hub_cfg.mutationEnabled = True
    if self.args.no_mutation:
      hub_cfg.mutationEnabled = False
    return hub_cfg

  def update_referential_rules(
      self, hub_cfg: messages.Message
  ) -> messages.Message:
    if self.args.referential_rules:
      hub_cfg.referentialRulesEnabled = True
    if self.args.no_referential_rules:
      hub_cfg.referentialRulesEnabled = False
    return hub_cfg

  @property
  def monitoring_backend_cfg(self) -> messages.Message:
    return self.messages.PolicyControllerMonitoringConfig

  @property
  def monitoring_backend_enum(self) -> messages.Message:
    return self.monitoring_backend_cfg.BackendsValueListEntryValuesEnum

  def _get_monitoring_enum(self, backend) -> messages.Message:
    internal_name = constants.MONITORING_BACKENDS.get(backend)
    if internal_name is None or not hasattr(
        self.monitoring_backend_enum,
        constants.MONITORING_BACKENDS[backend],
    ):
      raise exceptions.InvalidMonitoringBackendError(
          'No such monitoring backend: {}'.format(backend)
      )
    else:
      return getattr(
          self.monitoring_backend_enum,
          constants.MONITORING_BACKENDS[backend],
      )

  def update_monitoring(self, hub_cfg: messages.Message) -> messages.Message:
    """Sets or removes monitoring backends based on args."""
    if self.args.no_monitoring:
      config = self.messages.PolicyControllerMonitoringConfig(backends=[])
      hub_cfg.monitoring = config

    if self.args.monitoring:
      backends = [
          self._get_monitoring_enum(backend)
          for backend in self.args.monitoring.split(',')
      ]
      config = self.messages.PolicyControllerMonitoringConfig(backends=backends)
      hub_cfg.monitoring = config

    return hub_cfg

  @property
  def bundle_message(self) -> messages.Message:
    """Returns an reference to the BundlesValue class for this API channel."""
    return self.messages.PolicyControllerPolicyContentSpec.BundlesValue

  def update_default_bundles(
      self, hub_cfg: messages.Message
  ) -> messages.Message:
    """Sets default bundles based on args.

    This function assumes that the hub config is being initialized for the first
    time.

    Args:
      hub_cfg: A 'PolicyControllerHubConfig' proto message.

    Returns:
      A modified hub_config, adding the default bundle; or unmodified if the
      --no-default-bundles flag is specified.
    """
    if self.args.no_default_bundles:
      return hub_cfg

    policy_content_spec = self._get_policy_content(hub_cfg)
    bundles = protos.additional_properties_to_dict(
        policy_content_spec.bundles
    )
    bundles[DEFAULT_BUNDLE_NAME] = (
        self.messages.PolicyControllerBundleInstallSpec()
    )
    policy_content_spec.bundles = protos.set_additional_properties(
        self.bundle_message(), bundles
    )
    hub_cfg.policyContent = policy_content_spec
    return hub_cfg

  def is_feature_update(self) -> bool:
    return (
        self.args.fleet_default_member_config
        or self.args.no_fleet_default_member_config
    )

  def load_fleet_default_cfg(self) -> messages.Message:
    if self.args.fleet_default_member_config:
      config_path = path.expanduser(self.args.fleet_default_member_config)
      data = console_io.ReadFromFileOrStdin(
          config_path, binary=False
      )
      return util.Import(self.messages.PolicyControllerMembershipSpec, data)

  @property
  def template_lib_cfg(self) -> messages.Message:
    return self.messages.PolicyControllerTemplateLibraryConfig

  @property
  def template_lib_enum(self) -> messages.Message:
    return self.template_lib_cfg.InstallationValueValuesEnum

  def _get_policy_content(self, poco_cfg: messages.Message) -> messages.Message:
    """Get or create new PolicyControllerPolicyContentSpec."""
    if poco_cfg.policyContent is None:
      return self.messages.PolicyControllerPolicyContentSpec()
    return poco_cfg.policyContent

  def update_version(self, poco: messages.Message) -> messages.Message:
    if self.args.version:
      poco.version = self.args.version
    return poco

  def use_default_cfg(self) -> bool:
    return self.args.origin and self.args.origin == 'FLEET'

  def set_default_cfg(
      self, feature: messages.Message, membership: messages.Message
  ) -> messages.Message:
    """Sets membership to the default fleet configuration.

    Args:
      feature: The feature spec for the project.
      membership: The membership spec being updated.

    Returns:
      Updated MembershipFeatureSpec.
    Raises:
      MissingFleetDefaultMemberConfig: If none exists on the feature.
    """
    if feature.fleetDefaultMemberConfig is None:
      # Use second entity token of the feature's uri path (project name).
      project = feature.name.split('/')[1]
      msg = (
          'No fleet default member config specified for project {}. Use'
          " '... enable --fleet-default-member-config=config.yaml'."
      )
      raise exceptions.MissingFleetDefaultMemberConfig(msg.format(project))
    self.set_origin_fleet(membership)
    membership.policycontroller = (
        feature.fleetDefaultMemberConfig.policycontroller
    )

  def set_origin_fleet(self, membership: messages.Message) -> messages.Message:
    membership.origin = self.messages.Origin(
        type=self.messages.Origin.TypeValueValuesEnum.FLEET
    )
