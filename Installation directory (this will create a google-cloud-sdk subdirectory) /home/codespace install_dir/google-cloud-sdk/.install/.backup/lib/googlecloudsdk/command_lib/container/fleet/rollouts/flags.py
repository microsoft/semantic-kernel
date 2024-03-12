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
"""Functions to add flags in rollout commands."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from typing import Iterator

from apitools.base.protorpclite import messages
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import resources as fleet_resources
from googlecloudsdk.core import resources
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as fleet_messages

_BINAUTHZ_GKE_POLICY_REGEX = (
    'projects/([^/]+)/platforms/gke/policies/([a-zA-Z0-9_-]+)'
)


# TODO(b/312311133): Deduplicate shared code between fleet and rollout commands.
class RolloutFlags:
  """Add flags to the fleet rollout command surface."""

  def __init__(
      self,
      parser: parser_arguments.ArgumentInterceptor,
      release_track: base.ReleaseTrack = base.ReleaseTrack.ALPHA,
  ):
    self._parser = parser
    self._release_track = release_track

  @property
  def parser(self):
    return self._parser

  @property
  def release_track(self):
    return self._release_track

  def AddAsync(self):
    base.ASYNC_FLAG.AddToParser(self.parser)

  def AddDisplayName(self):
    self.parser.add_argument(
        '--display-name',
        type=str,
        help=textwrap.dedent("""\
            Display name of the rollout to be created (optional). 4-30
            characters, alphanumeric and [ \'"!-] only.
        """),
    )

  def AddLabels(self):
    self.parser.add_argument(
        '--labels',
        help='Labels for the rollout.',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
    )

  def AddManagedRolloutConfig(self):
    managed_rollout_config_group = self.parser.add_group(
        help='Configurations for the Rollout. Waves are assigned automatically.'
    )
    self._AddSoakDuration(managed_rollout_config_group)

  def _AddSoakDuration(
      self, managed_rollout_config_group: parser_arguments.ArgumentInterceptor
  ):
    managed_rollout_config_group.add_argument(
        '--soak-duration',
        help=textwrap.dedent("""\
          Soak time before starting the next wave. e.g. `4h`, `2d6h`.

          See $ gcloud topic datetimes for information on duration formats."""),
        type=arg_parsers.Duration(),
    )

  def AddRolloutResourceArg(self):
    fleet_resources.AddRolloutResourceArg(
        parser=self.parser,
        api_version=util.VERSION_MAP[self.release_track],
    )

  def AddFeatureUpdate(self):
    feature_update_mutex_group = self.parser.add_mutually_exclusive_group(
        help='Feature config to use for Rollout.',
    )

    self._AddSecurityPostureConfig(feature_update_mutex_group)
    self._AddBinaryAuthorizationConfig(feature_update_mutex_group)

  def _AddSecurityPostureConfig(
      self, feature_update_mutex_group: parser_arguments.ArgumentInterceptor
  ):
    security_posture_config_group = feature_update_mutex_group.add_group(
        help='Security posture config.',
    )
    self._AddSecurityPostureMode(security_posture_config_group)
    self._AddWorkloadVulnerabilityScanningMode(security_posture_config_group)

  def _AddSecurityPostureMode(
      self, security_posture_config_group: parser_arguments.ArgumentInterceptor
  ):
    security_posture_config_group.add_argument(
        '--security-posture',
        choices=['disabled', 'standard'],
        default=None,
        help=textwrap.dedent("""\
          To apply standard security posture to clusters in the fleet,

            $ {command} --security-posture=standard

          """),
    )

  def _AddWorkloadVulnerabilityScanningMode(
      self, security_posture_config_group: parser_arguments.ArgumentInterceptor
  ):
    security_posture_config_group.add_argument(
        '--workload-vulnerability-scanning',
        choices=['disabled', 'standard', 'enterprise'],
        default=None,
        help=textwrap.dedent("""\
            To apply standard vulnerability scanning to clusters in the fleet,

              $ {command} --workload-vulnerability-scanning=standard

            """),
    )

  def _AddBinaryAuthorizationConfig(
      self, feature_update_mutex_group: parser_arguments.ArgumentInterceptor
  ):
    binary_authorization_config_group = feature_update_mutex_group.add_group(
        help='Binary Authorization config.',
    )
    self._AddBinauthzEvaluationMode(binary_authorization_config_group)
    self._AddBinauthzPolicyBindings(binary_authorization_config_group)

  def _AddBinauthzEvaluationMode(
      self,
      binary_authorization_config_group: parser_arguments.ArgumentInterceptor,
  ):
    binary_authorization_config_group.add_argument(
        '--binauthz-evaluation-mode',
        choices=['disabled', 'policy-bindings'],
        # Convert values to lower case before checking against the list of
        # options. This allows users to pass evaluation mode in enum form.
        type=lambda x: x.replace('_', '-').lower(),
        default=None,
        help=textwrap.dedent("""\
          Configure binary authorization mode for clusters to onboard the fleet,

            $ {command} --binauthz-evaluation-mode=policy-bindings

          """),
    )

  def _AddBinauthzPolicyBindings(
      self,
      binary_authorization_config_group: parser_arguments.ArgumentInterceptor,
  ):
    platform_policy_type = arg_parsers.RegexpValidator(
        _BINAUTHZ_GKE_POLICY_REGEX,
        'GKE policy resource names have the following format: '
        '`projects/{project_number}/platforms/gke/policies/{policy_id}`',
    )
    binary_authorization_config_group.add_argument(
        '--binauthz-policy-bindings',
        default=None,
        action='append',
        metavar='name=BINAUTHZ_POLICY',
        help=textwrap.dedent("""\
          The relative resource name of the Binary Authorization policy to audit
          and/or enforce. GKE policies have the following format:
          `projects/{project_number}/platforms/gke/policies/{policy_id}`."""),
        type=arg_parsers.ArgDict(
            spec={
                'name': platform_policy_type,
            },
            required_keys=['name'],
            max_length=1,
        ),
    )


class RolloutFlagParser:
  """Parse flags during fleet rollout command runtime."""

  def __init__(
      self, args: parser_extensions.Namespace, release_track: base.ReleaseTrack
  ):
    self.args = args
    self.release_track = release_track
    self.messages = util.GetMessagesModule(release_track)

  def IsEmpty(self, message: messages.Message) -> bool:
    """Determines if a message is empty.

    Args:
      message: A message to check the emptiness.

    Returns:
      A bool indictating if the message is equivalent to a newly initialized
      empty message instance.
    """
    return message == type(message)()

  def TrimEmpty(self, message: messages.Message):
    """Trim empty messages to avoid cluttered request."""
    # TODO(b/289929895): Trim child fields at the parent level.
    if not self.IsEmpty(message):
      return message
    return None

  def Rollout(self) -> fleet_messages.Rollout:
    rollout = fleet_messages.Rollout()
    rollout.name = util.RolloutName(self.args)
    rollout.displayName = self._DisplayName()
    rollout.labels = self._Labels()
    rollout.managedRolloutConfig = self._ManagedRolloutConfig()
    rollout.feature = self._FeatureUpdate()
    return rollout

  def _DisplayName(self) -> str:
    return self.args.display_name

  def _Labels(self) -> fleet_messages.Rollout.LabelsValue:
    """Parses --labels."""
    if '--labels' not in self.args.GetSpecifiedArgs():
      return None

    labels = self.args.labels
    labels_value = fleet_messages.Rollout.LabelsValue()
    for key, value in labels.items():
      labels_value.additionalProperties.append(
          fleet_messages.Rollout.LabelsValue.AdditionalProperty(
              key=key, value=value
          )
      )
    return labels_value

  def _ManagedRolloutConfig(self) -> fleet_messages.ManagedRolloutConfig:
    managed_rollout_config = fleet_messages.ManagedRolloutConfig()
    managed_rollout_config.soakDuration = self._SoakDuration()
    return self.TrimEmpty(managed_rollout_config)

  def _SoakDuration(self) -> str:
    """Parses --soak-duration.

    Accepts ISO 8601 durations format. To read more,
    https://cloud.google.com/sdk/gcloud/reference/topic/

    Returns:
      str, in standard duration format, in unit of seconds.
    """
    if '--soak-duration' not in self.args.GetSpecifiedArgs():
      return None
    return '{}s'.format(self.args.soak_duration)

  def _FeatureUpdate(self) -> fleet_messages.FeatureUpdate:
    """Constructs message FeatureUpdate."""
    feature_update = fleet_messages.FeatureUpdate()
    feature_update.securityPostureConfig = self._SecurityPostureConfig()
    feature_update.binaryAuthorizationConfig = self._BinaryAuthorzationConfig()
    return self.TrimEmpty(feature_update)

  def _SecurityPostureConfig(self) -> fleet_messages.SecurityPostureConfig:
    security_posture_config = fleet_messages.SecurityPostureConfig()
    security_posture_config.mode = self._SecurityPostureMode()
    security_posture_config.vulnerabilityMode = (
        self._VulnerabilityModeValueValuesEnum()
    )
    return self.TrimEmpty(security_posture_config)

  def _SecurityPostureMode(
      self,
  ) -> fleet_messages.SecurityPostureConfig.ModeValueValuesEnum:
    """Parses --security-posture."""
    if '--security-posture' not in self.args.GetSpecifiedArgs():
      return None

    enum_type = fleet_messages.SecurityPostureConfig.ModeValueValuesEnum
    mapping = {
        'disabled': enum_type.DISABLED,
        'standard': enum_type.BASIC,
    }
    return mapping[self.args.security_posture]

  def _VulnerabilityModeValueValuesEnum(
      self,
  ) -> fleet_messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum:
    """Parses --workload-vulnerability-scanning."""
    if '--workload-vulnerability-scanning' not in self.args.GetSpecifiedArgs():
      return None

    enum_type = (
        self.messages.SecurityPostureConfig.VulnerabilityModeValueValuesEnum
    )
    mapping = {
        'disabled': enum_type.VULNERABILITY_DISABLED,
        'standard': enum_type.VULNERABILITY_BASIC,
        'enterprise': enum_type.VULNERABILITY_ENTERPRISE,
    }
    return mapping[self.args.workload_vulnerability_scanning]

  def _BinaryAuthorzationConfig(
      self,
  ) -> fleet_messages.BinaryAuthorizationConfig:
    binary_authorization_config = fleet_messages.BinaryAuthorizationConfig()
    binary_authorization_config.evaluationMode = self._EvaluationMode()
    binary_authorization_config.policyBindings = list(self._PolicyBindings())
    return self.TrimEmpty(binary_authorization_config)

  def _EvaluationMode(
      self,
  ) -> fleet_messages.BinaryAuthorizationConfig.EvaluationModeValueValuesEnum:
    """Parses --binauthz-evaluation-mode."""
    if '--binauthz-evaluation-mode' not in self.args.GetSpecifiedArgs():
      return None

    enum_type = (
        self.messages.BinaryAuthorizationConfig.EvaluationModeValueValuesEnum
    )
    mapping = {
        'disabled': enum_type.DISABLED,
        'policy-bindings': enum_type.POLICY_BINDINGS,
    }
    return mapping[self.args.binauthz_evaluation_mode]

  def _PolicyBindings(self) -> Iterator[fleet_messages.PolicyBinding]:
    """Parses --binauthz-policy-bindings."""
    if '--binauthz-policy-bindings' not in self.args.GetSpecifiedArgs():
      return []

    policy_bindings = self.args.binauthz_policy_bindings

    return (
        fleet_messages.PolicyBinding(name=binding['name'])
        for binding in policy_bindings
    )

  def OperationRef(self) -> resources.Resource:
    """Parses resource argument operation."""
    return self.args.CONCEPTS.operation.Parse()

  def Project(self) -> str:
    return self.args.project

  def Location(self) -> str:
    return self.args.location

  def Async(self) -> bool:
    """Parses --async flag.

    The internal representation of --async is set to args.async_, defined in
    calliope/base.py file.

    Returns:
      bool, True if specified, False if unspecified.
    """
    return self.args.async_
