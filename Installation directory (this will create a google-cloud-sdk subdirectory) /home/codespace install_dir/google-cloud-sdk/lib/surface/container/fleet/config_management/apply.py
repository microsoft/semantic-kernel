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
"""The command to update Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet.config_management import utils
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.command_lib.container.fleet.policycontroller import constants
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml

# Pull out the example text so the example command can be one line without the
# py linter complaining. The docgen tool properly breaks it into multiple lines.
EXAMPLES = r"""
    To apply a YAML config file to a membership, prepare
    [apply-spec.yaml](https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields#example_gcloud_apply_spec) then run:

      $ {command} --membership=MEMBERSHIP_NAME --config=APPLY-SPEC.YAML --version=VERSION
"""


class Apply(base.UpdateCommand):
  """Update a Config Management Feature Spec.

  Update a user-specified config file to a ConfigManagement Custom Resource.
  The config file should be a .yaml file, all eligible fields are listed in
  https://cloud.google.com/anthos-config-management/docs/reference/gcloud-apply-fields
  """

  detailed_help = {'EXAMPLES': EXAMPLES}

  feature_name = 'configmanagement'

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(parser)
    parser.add_argument(
        '--config',
        type=str,
        help='The path to config-management.yaml.',
        required=True,
    )
    parser.add_argument(
        '--version', type=str, help='The version of ACM to install.'
    )

  def Run(self, args):
    utils.enable_poco_api_if_disabled(self.Project())

    # check static yaml fields before query membership
    try:
      loaded_cm = yaml.load_path(args.config)
    except yaml.Error as e:
      raise exceptions.Error(
          'Invalid config yaml file {}'.format(args.config), e
      )
    _validate_meta(loaded_cm)

    membership = base.ParseMembership(
        args, prompt=True, autoselect=True, search=True
    )

    config_sync = _parse_config_sync(loaded_cm, self.messages)
    policy_controller = _parse_policy_controller(loaded_cm, self.messages)
    hierarchy_controller_config = _parse_hierarchy_controller_config(
        loaded_cm, self.messages
    )
    version = (
        self._get_backfill_version(membership)
        if not args.version
        else args.version
    )
    cluster = loaded_cm.get('spec', {}).get('cluster', '')
    spec = self.messages.MembershipFeatureSpec(
        configmanagement=self.messages.ConfigManagementMembershipSpec(
            version=version,
            cluster=cluster,
            configSync=config_sync,
            policyController=policy_controller,
            hierarchyController=hierarchy_controller_config,
        )
    )
    spec_map = {membership: spec}

    # UpdateFeature uses patch method to update membership_configs map,
    # there's no need to get the existing feature spec
    patch = self.messages.Feature(
        membershipSpecs=self.hubclient.ToMembershipSpecs(spec_map)
    )
    self.Update(['membership_specs'], patch)

  def _get_backfill_version(self, membership):
    """Get the value the version field in FeatureSpec should be set to.

    Args:
      membership: The full membership  name whose Spec will be backfilled.

    Returns:
      version: A string denoting the version field in MembershipConfig
    Raises: Error, if retrieving FeatureSpec of FeatureState fails
    """
    f = self.GetFeature()
    return utils.get_backfill_version_from_feature(f, membership)


def _validate_meta(configmanagement):
  """Validate the parsed configmanagement yaml.

  Args:
    configmanagement: The dict loaded from yaml.
  """
  if not isinstance(configmanagement, dict):
    raise exceptions.Error('Invalid ConfigManagement template.')
  if configmanagement.get('applySpecVersion') != 1:
    raise exceptions.Error(
        'Only "applySpecVersion: 1" is supported. To use a later version,'
        'please fetch the config by running\n'
        'gcloud container fleet config-management fetch-for-apply'
    )

  if 'spec' not in configmanagement:
    raise exceptions.Error('Missing required field .spec')
  spec = configmanagement['spec']
  legal_fields = {
      utils.CONFIG_SYNC,
      utils.POLICY_CONTROLLER,
      utils.HNC,
      utils.CLUSTER,
  }
  for field in spec:
    if field not in legal_fields:
      raise exceptions.Error(
          'Please remove illegal field .spec.{}'.format(field)
      )


def _parse_config_sync(configmanagement, msg):
  """Load ConfigSync configuration with the parsed configmanagement yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    config_sync: The ConfigSync configuration holds configmanagement.spec.git
    or configmanagement.spec.oci being used in MembershipConfigs
  Raises: Error, if required fields are missing from .spec or unsupported fields
    are included in .spec
  """

  if (
      'spec' not in configmanagement
      or utils.CONFIG_SYNC not in configmanagement['spec']
  ):
    return None
  spec_source = configmanagement['spec'][utils.CONFIG_SYNC]
  for field in spec_source:
    if (
        field
        not in yaml.load(utils.APPLY_SPEC_VERSION_1)['spec'][utils.CONFIG_SYNC]
    ):
      raise exceptions.Error(
          'The field .spec.{}.{}'.format(utils.CONFIG_SYNC, field)
          + ' is unrecognized in this applySpecVersion. Please remove.'
      )

  config_sync = msg.ConfigManagementConfigSync()
  # missing `enabled: true` will enable configSync
  config_sync.enabled = True
  if 'enabled' in spec_source:
    config_sync.enabled = spec_source['enabled']
  # Default to use sourceType 'git' if not specified
  source_type = spec_source.get('sourceType', 'git')
  if source_type == 'oci':
    config_sync.oci = _parse_oci_config(spec_source, msg)
  else:
    config_sync.git = _parse_git_config(spec_source, msg)
  if 'sourceFormat' in spec_source:
    config_sync.sourceFormat = spec_source['sourceFormat']
  if 'preventDrift' in spec_source:
    config_sync.preventDrift = spec_source['preventDrift']
  if 'metricsGcpServiceAccountEmail' in spec_source:
    config_sync.metricsGcpServiceAccountEmail = spec_source[
        'metricsGcpServiceAccountEmail'
    ]

  return config_sync


def _parse_git_config(spec_source, msg):
  """Load GitConfig with the parsed config_sync yaml.

  Args:
    spec_source: The config_sync dict loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    git_config: The GitConfig configuration being used in MembershipConfigs
  """

  git_config = msg.ConfigManagementGitConfig()
  if 'syncWait' in spec_source:
    git_config.syncWaitSecs = spec_source['syncWait']
  for field in [
      'policyDir',
      'secretType',
      'syncBranch',
      'syncRepo',
      'syncRev',
      'httpsProxy',
      'gcpServiceAccountEmail',
  ]:
    if field in spec_source:
      setattr(git_config, field, spec_source[field])
  return git_config


def _parse_oci_config(spec_source, msg):
  """Load OciConfig with the parsed config_sync yaml.

  Args:
    spec_source: The config_sync dict loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    oci_config: The OciConfig being used in MembershipConfigs
  """

  oci_config = msg.ConfigManagementOciConfig()
  if 'syncWait' in spec_source:
    oci_config.syncWaitSecs = spec_source['syncWait']
  for field in [
      'policyDir',
      'secretType',
      'syncRepo',
      'gcpServiceAccountEmail',
  ]:
    if field in spec_source:
      setattr(oci_config, field, spec_source[field])
  return oci_config


def _parse_policy_controller(configmanagement, msg):
  """Load PolicyController with the parsed config-management.yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    policy_controller: The Policy Controller configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.policyController
  Raises: Error, if Policy Controller `enabled` is missing or not a boolean
  """

  if (
      'spec' not in configmanagement
      or 'policyController' not in configmanagement['spec']
  ):
    return None

  spec_policy_controller = configmanagement['spec']['policyController']
  # Required field
  if (
      configmanagement['spec']['policyController'] is None
      or 'enabled' not in spec_policy_controller
  ):
    raise exceptions.Error(
        'Missing required field .spec.policyController.enabled'
    )
  enabled = spec_policy_controller['enabled']
  if not isinstance(enabled, bool):
    raise exceptions.Error(
        'policyController.enabled should be `true` or `false`'
    )

  policy_controller = msg.ConfigManagementPolicyController()
  # When the policyController is set to be enabled, policy_controller will
  # be filled with the valid fields set in spec_policy_controller, which
  # were mapped from the config-management.yaml
  for field in spec_policy_controller:
    if field not in [
        'enabled',
        'templateLibraryInstalled',
        'auditIntervalSeconds',
        'referentialRulesEnabled',
        'exemptableNamespaces',
        'logDeniesEnabled',
        'mutationEnabled',
        'monitoring',
    ]:
      raise exceptions.Error(
          'Please remove illegal field .spec.policyController.{}'.format(field)
      )
    if field == 'monitoring':
      monitoring = _build_monitoring_msg(spec_policy_controller[field], msg)
      setattr(policy_controller, field, monitoring)
    else:
      setattr(policy_controller, field, spec_policy_controller[field])

  return policy_controller


def _parse_hierarchy_controller_config(configmanagement, msg):
  """Load HierarchyController with the parsed config-management.yaml.

  Args:
    configmanagement: dict, The data loaded from the config-management.yaml
      given by user.
    msg: The Hub messages package.

  Returns:
    hierarchy_controller: The Hierarchy Controller configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.hierarchyController
  Raises: Error, if Hierarchy Controller `enabled` set to false but also has
    other fields present in the config
  """

  if (
      'spec' not in configmanagement
      or 'hierarchyController' not in configmanagement['spec']
  ):
    return None

  spec = configmanagement['spec']['hierarchyController']
  # Required field
  if spec is None or 'enabled' not in spec:
    raise exceptions.Error(
        'Missing required field .spec.hierarchyController.enabled'
    )
  enabled = spec['enabled']
  if not isinstance(enabled, bool):
    raise exceptions.Error(
        'hierarchyController.enabled should be `true` or `false`'
    )

  config_proto = msg.ConfigManagementHierarchyControllerConfig()
  # When the hierarchyController is set to be enabled, hierarchy_controller will
  # be filled with the valid fields set in spec, which
  # were mapped from the config-management.yaml
  for field in spec:
    if field not in [
        'enabled',
        'enablePodTreeLabels',
        'enableHierarchicalResourceQuota',
    ]:
      raise exceptions.Error(
          'Please remove illegal field .spec.hierarchyController{}'.format(
              field
          )
      )
    setattr(config_proto, field, spec[field])

  return config_proto


def _build_monitoring_msg(spec_monitoring, msg):
  """Build PolicyControllerMonitoring message from the parsed spec.

  Args:
    spec_monitoring: dict, The monitoring data loaded from the
      config-management.yaml given by user.
    msg: The Hub messages package.

  Returns:
    monitoring: The Policy Controller Monitoring configuration for
    MembershipConfigs, filled in the data parsed from
    configmanagement.spec.policyController.monitoring
  Raises: Error, if Policy Controller Monitoring Backend is not recognized
  """
  backends = spec_monitoring.get('backends', [])
  if not backends:
    return None

  # n.b. Policy Controller is the source of truth for supported backends.
  converter = constants.monitoring_backend_converter(msg)

  def convert(backend):
    result = converter.get(backend.lower())
    if not result:
      raise exceptions.Error(
          'policyController.monitoring.backend {} is not recognized'.format(
              backend
          )
      )
    return result

  monitoring_backends = [convert(backend) for backend in backends]
  monitoring = msg.ConfigManagementPolicyControllerMonitoring()
  monitoring.backends = monitoring_backends
  return monitoring
