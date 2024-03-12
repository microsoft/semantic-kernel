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
"""Command for adding layer7 ddos defense threshold config to security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import flags
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils


class AddLayer7DdosDefenseThresholdConfigHelper(object):
  r"""Add a layer7 ddos defense threshold config to a Compute Engine security policy.

  *{command}* is used to add layer7 ddos defense threshold configs to security policies.

  ## EXAMPLES

  To add a layer7 ddos defense threshold config run the following command:

    $ {command} NAME \
       --threshold-config-name=my-threshold-config-name \
       --auto-deploy-load-threshold=0.7 \
       --auto-deploy-confidence-threshold=0.8 \
       --auto-deploy-impacted-baseline-threshold=0.1 \
       --auto-deploy-expiration-sec=4800
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser, support_granularity_config):
    """Adds the arguments for the command."""
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='update')
    parser.add_argument(
        '--threshold-config-name',
        required=True,
        help='The name for the threshold config.',
    )
    parser.add_argument(
        '--auto-deploy-load-threshold',
        type=float,
        required=False,
        help=(
            "The threshold on backend's load, over which auto-deploy takes"
            ' action.'
        ),
    )
    parser.add_argument(
        '--auto-deploy-confidence-threshold',
        type=float,
        required=False,
        help=(
            'The threshold of the confidence of an identified attack, over'
            ' which auto-deploy takes action.'
        ),
    )
    parser.add_argument(
        '--auto-deploy-impacted-baseline-threshold',
        type=float,
        required=False,
        help=(
            'The threshold on the estimated impact to the baseline traffic of a'
            ' suggested mitigation, below which auto-deploy takes action.'
        ),
    )
    parser.add_argument(
        '--auto-deploy-expiration-sec',
        type=int,
        required=False,
        help='The duration of actions, if any, taken by auto-deploy.',
    )
    if support_granularity_config:
      parser.add_argument(
          '--detection-load-threshold',
          type=float,
          required=False,
          help=(
              "The threshold on backend's load, over which adaptive protection"
              ' detects an attack.'
          ),
      )
      parser.add_argument(
          '--detection-absolute-qps',
          type=float,
          required=False,
          help=(
              'The absolute QPS of the incoming traffic, over which adaptive'
              ' protection detects an attack.'
          ),
      )
      parser.add_argument(
          '--detection-relative-to-baseline-qps',
          type=float,
          required=False,
          help=(
              'The QPS of the incoming traffic relative to the average baseline'
              ' QPS, over which adaptive protection detects an attack.'
          ),
      )
      parser.add_argument(
          '--traffic-granularity-configs',
          type=arg_parsers.ArgList(
              max_length=2,
              custom_delim_char=';',
              element_type=arg_parsers.ArgDict(
                  min_length=2,
                  max_length=3,
                  spec={
                      'type': str,
                      'value': str,
                      'enableEachUniqueValue': bool,
                  },
                  required_keys=['type'],
              ),
          ),
          required=False,
          metavar='type=TYPE[,value=VALUE][,enableEachUniqueValue=ENABLE_EACH_UNIQUE_VALUE];...',
          help=(
              'Specify up to 2 configs matching a specifc type/value of'
              ' traffic.'
          ),
      )

  @classmethod
  def Run(cls, release_track, args, support_granularity_config):
    """Runs the command."""
    holder = base_classes.ComputeApiHolder(release_track)
    ref = cls.SECURITY_POLICY_ARG.ResolveAsResource(args, holder.resources)
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
        or not adaptive_protection_config.layer7DdosDefenseConfig.enable
    ):
      raise exceptions.InvalidArgumentException(
          '--threshold-config-name',
          'Must enable adaptive protection layer 7 ddos defense before adding a'
          ' threshold config',
      )

    threshold_config = (
        security_policies_utils.CreateLayer7DdosDefenseThresholdConfig(
            holder.client,
            args,
            support_granularity_config=support_granularity_config,
        )
    )
    adaptive_protection_config.layer7DdosDefenseConfig.thresholdConfigs.append(
        threshold_config
    )

    updated_security_policy = holder.client.messages.SecurityPolicy(
        adaptiveProtectionConfig=adaptive_protection_config,
        fingerprint=existing_security_policy.fingerprint,
    )

    return security_policy.Patch(security_policy=updated_security_policy)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddLayer7DdosDefenseThresholdConfigGA(base.UpdateCommand):
  r"""Add a layer7 ddos defense threshold config to a Compute Engine security policy.

  *{command}* is used to add layer7 ddos defense threshold configs to security policies.

  ## EXAMPLES

  To add a layer7 ddos defense threshold config, run the following command:

    $ {command} NAME \
       --threshold-config-name=my-threshold-config-name \
       --auto-deploy-load-threshold=0.7 \
       --auto-deploy-confidence-threshold=0.8 \
       --auto-deploy-impacted-baseline-threshold=0.1 \
       --auto-deploy-expiration-sec=4800
  """

  _support_granularity_config = False

  @classmethod
  def Args(cls, parser):
    AddLayer7DdosDefenseThresholdConfigHelper.Args(
        parser, support_granularity_config=cls._support_granularity_config
    )

  def Run(self, args):
    return AddLayer7DdosDefenseThresholdConfigHelper.Run(
        self.ReleaseTrack(),
        args,
        support_granularity_config=self._support_granularity_config,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class AddLayer7DdosDefenseThresholdConfigBeta(base.UpdateCommand):
  r"""Add a layer7 ddos defense threshold config to a Compute Engine security policy.

  *{command}* is used to add layer7 ddos defense threshold configs to security policies.

  ## EXAMPLES

  To add a layer7 ddos defense threshold config run the following command:

    $ {command} NAME \
       --threshold-config-name=my-threshold-config-name \
       --auto-deploy-load-threshold=0.7 \
       --auto-deploy-confidence-threshold=0.8 \
       --auto-deploy-impacted-baseline-threshold=0.1 \
       --auto-deploy-expiration-sec=4800
       --detection-load-threshold=0.4
       --detection-absolute-qps=1000
       --detection-relative-to-baseline-qps=2.0
       --traffic-granularity-configs=type=HTTP_HEADER_HOST,value=www.my-test-host.com;type=HTTP_PATH,enableEachUniqueValue=true
  """

  _support_granularity_config = True

  @classmethod
  def Args(cls, parser):
    AddLayer7DdosDefenseThresholdConfigHelper.Args(
        parser, support_granularity_config=cls._support_granularity_config
    )

  def Run(self, args):
    return AddLayer7DdosDefenseThresholdConfigHelper.Run(
        self.ReleaseTrack(),
        args,
        support_granularity_config=self._support_granularity_config,
    )
