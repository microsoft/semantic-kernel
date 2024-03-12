# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""Command for removing layer7 ddos defense threshold config from security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class RemoveLayer7DdosDefenseThresholdConfig(base.UpdateCommand):
  r"""Remove a layer7 ddos defense threshold config from a Compute Engine security policy.

  *{command}* is used to remove layer7 ddos defense threshold configs from security policies.

  ## EXAMPLES

  To remove a layer7 ddos defense threshold config run the following command:

    $ {command} NAME \
       --threshold-config-name=my-threshold-config-name
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='update')
    parser.add_argument(
        '--threshold-config-name',
        required=True,
        help='The name for the threshold config.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(args, holder.resources)
    security_policy = client.SecurityPolicy(
        ref=ref, compute_client=holder.client
    )
    existing_security_policy = security_policy.Describe()[0]

    adaptive_protection_config = (
        existing_security_policy.adaptiveProtectionConfig
    )
    if (
        adaptive_protection_config is None
        or adaptive_protection_config.layer7DdosDefenseConfig is None
        or not adaptive_protection_config.layer7DdosDefenseConfig.thresholdConfigs
    ):
      raise exceptions.InvalidArgumentException(
          '--threshold-config-name',
          "There's no existing layer 7 ddos defense threshold config to remove",
      )

    existing_threshold_configs = (
        adaptive_protection_config.layer7DdosDefenseConfig.thresholdConfigs
    )
    new_threshold_configs = [
        threshold_config
        for threshold_config in existing_threshold_configs
        if threshold_config.name != args.threshold_config_name
    ]

    if len(existing_threshold_configs) == len(new_threshold_configs):
      raise exceptions.InvalidArgumentException(
          '--threshold-config-name',
          'layer 7 ddos defense threshold config "%s" does not exist in this'
          ' policy.'
          % args.threshold_config_name,
      )

    adaptive_protection_config.layer7DdosDefenseConfig.thresholdConfigs = (
        new_threshold_configs
    )

    updated_security_policy = holder.client.messages.SecurityPolicy(
        adaptiveProtectionConfig=adaptive_protection_config,
        fingerprint=existing_security_policy.fingerprint,
    )

    return security_policy.Patch(security_policy=updated_security_policy)
