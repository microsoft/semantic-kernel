# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""ai-platform models create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import constants
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

_REGION_FLAG_HELPTEXT = """\
Google Cloud region of the regional endpoint to use for this command.

If you specify this flag, do not specify `--regions`.

If you specify `--region=global`, the model will be deployed to 'us-central1'
by default using the global endpoint. Please use `--regions` only if you want
to change the region where the model will be deployed against the global
endpoint.

If both flags are unspecified and you don't set ``ai_platform/region'', you will
be prompted for region of the regional endpoint.

Learn more about regional endpoints and see a list of available regions:
 https://cloud.google.com/ai-platform/prediction/docs/regional-endpoints
"""


def _AddCreateArgs(parser,
                   support_console_logging=False):
  """Get arguments for the `ai-platform models create` command."""
  flags.GetModelName().AddToParser(parser)
  flags.GetDescriptionFlag('model').AddToParser(parser)
  region_group = parser.add_mutually_exclusive_group()
  region_group.add_argument(
      '--region',
      choices=constants.SUPPORTED_REGIONS_WITH_GLOBAL,
      help=_REGION_FLAG_HELPTEXT)
  region_group.add_argument(
      '--regions',
      metavar='REGION',
      type=arg_parsers.ArgList(min_length=1),
      help="""\
The Google Cloud region where the model will be deployed (currently only a
single region is supported) against the global endpoint.

If you specify this flag, do not specify `--region`.

Defaults to 'us-central1' while using the global endpoint.
""")
  parser.add_argument(
      '--enable-logging',
      action='store_true',
      help='If set, enables StackDriver Logging for online prediction. These '
           'logs are like standard server access logs, containing information '
           'such as timestamps and latency for each request.')
  if support_console_logging:
    parser.add_argument(
        '--enable-console-logging',
        action='store_true',
        help='If set, enables StackDriver Logging of stderr and stdout streams '
             'for online prediction. These logs are more verbose than the '
             'standard access logs and can be helpful for debugging.')
  labels_util.AddCreateLabelsFlags(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a new AI Platform model."""

  @staticmethod
  def Args(parser):
    _AddCreateArgs(parser)

  def _Run(self, args, support_console_logging=False):
    region, model_regions = models_util.GetModelRegion(args)
    with endpoint_util.MlEndpointOverrides(region=region):
      models_client = models.ModelsClient()
      labels = models_util.ParseCreateLabels(models_client, args)
      enable_console_logging = (
          support_console_logging and args.enable_console_logging)
      model = models_util.Create(
          models_client,
          args.model,
          model_regions,
          enable_logging=args.enable_logging,
          enable_console_logging=enable_console_logging,
          labels=labels,
          description=args.description)
      log.CreatedResource(model.name, kind='ai platform model')

  def Run(self, args):
    self._Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreateBeta(Create):
  """Create a new AI Platform model."""

  @staticmethod
  def Args(parser):
    _AddCreateArgs(parser, support_console_logging=True)

  def Run(self, args):
    self._Run(args, support_console_logging=True)
