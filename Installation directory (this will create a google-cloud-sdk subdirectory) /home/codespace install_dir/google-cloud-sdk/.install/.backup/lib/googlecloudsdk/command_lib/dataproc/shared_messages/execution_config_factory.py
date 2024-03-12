# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Factory for ExecutionConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc.shared_messages import authentication_config_factory as acf
import six


class ExecutionConfigFactory(object):
  """Factory for ExecutionConfig message.

  Add ExecutionConfig related arguments to argument parser and create
  ExecutionConfig message from parsed arguments.
  """

  def __init__(self, dataproc, authentication_config_factory_override=None):
    """Factory class for ExecutionConfig message.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      authentication_config_factory_override: Override the default
        AuthenticationConfigFactory instance. This is a keyword argument.
    """
    self.dataproc = dataproc

    self.authentication_config_factory = (
        authentication_config_factory_override
        or acf.AuthenticationConfigFactory(self.dataproc)
    )

  def GetMessage(self, args):
    """Builds an ExecutionConfig instance.

    Build a ExecutionConfig instance according to user settings.
    Returns None if all fileds are None.

    Args:
      args: Parsed arguments.

    Returns:
      ExecutionConfig: A ExecutionConfig instance. None if all fields are
      None.
    """
    kwargs = {}

    if args.tags:
      kwargs['networkTags'] = args.tags

    if args.network:
      kwargs['networkUri'] = args.network

    if args.subnet:
      kwargs['subnetworkUri'] = args.subnet

    if args.performance_tier:
      kwargs['performanceTier'] = (
          self.dataproc.messages.ExecutionConfig.PerformanceTierValueValuesEnum(
              args.performance_tier.upper()
          )
      )

    if args.service_account:
      kwargs['serviceAccount'] = args.service_account

    if args.kms_key:
      kwargs['kmsKey'] = args.kms_key

    if hasattr(args, 'max_idle') and args.max_idle:
      # ExecutionConfig message expects duration in seconds
      kwargs['idleTtl'] = six.text_type(args.max_idle) + 's'

    if args.ttl:
      # ExecutionConfig message expects duration in seconds
      kwargs['ttl'] = six.text_type(args.ttl) + 's'

    if args.staging_bucket:
      kwargs['stagingBucket'] = args.staging_bucket

    authentication_config = self.authentication_config_factory.GetMessage(args)
    if authentication_config:
      kwargs['authenticationConfig'] = authentication_config

    if not kwargs:
      return None

    return self.dataproc.messages.ExecutionConfig(**kwargs)


# Supported performance tier choices.
_PERFORMANCE_TIER = ['economy', 'standard', 'high']


def AddArguments(parser):
  """Adds ExecutionConfig related arguments to parser."""
  base.ChoiceArgument(
      '--performance-tier',
      hidden=True,  # Not supported yet.
      choices=_PERFORMANCE_TIER,
      help_str=(
          'Performance tier for a batch/session job performance. '
          'The default performance level is STANDARD.')).AddToParser(parser)

  parser.add_argument(
      '--service-account',
      help='The IAM service account to be used for a batch/session job.')

  network_group = parser.add_mutually_exclusive_group()
  network_group.add_argument(
      '--network', help='Network URI to connect network to.')
  network_group.add_argument(
      '--subnet',
      help=('Subnetwork URI to connect network to. Subnet must have Private '
            'Google Access enabled.'))

  parser.add_argument(
      '--tags',
      type=arg_parsers.ArgList(),
      metavar='TAGS',
      default=[],
      help='Network tags for traffic control.')

  parser.add_argument('--kms-key', help='Cloud KMS key to use for encryption.')

  parser.add_argument(
      '--staging-bucket',
      help="""\
      The Cloud Storage bucket to use to store job dependencies, config files,
      and job driver console output. If not specified, the default [staging bucket]
      (https://cloud.google.com/dataproc-serverless/docs/concepts/buckets) is used.
      """,
  )

  parser.add_argument(
      '--ttl',
      type=arg_parsers.Duration(),
      help="""
      The duration after the workload will be unconditionally terminated,
      for example, '20m' or '1h'. Run
      [gcloud topic datetimes](https://cloud.google.com/sdk/gcloud/reference/topic/datetimes)
      for information on duration formats.""",
  )
