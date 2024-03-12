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
"""ai-platform models delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.api_lib.ml_engine import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.command_lib.ml_engine import region_util


def _AddDeleteArgs(parser):
  flags.GetModelName().AddToParser(parser)
  flags.GetRegionArg(include_global=True).AddToParser(parser)


def _Run(args):
  region = region_util.GetRegion(args)
  with endpoint_util.MlEndpointOverrides(region=region):
    models_client = models.ModelsClient()
    operations_client = operations.OperationsClient()
    return models_util.Delete(models_client, operations_client, args.model)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  r"""Delete an existing AI Platform model.

  ## EXAMPLES

  To delete all models matching the regular expression `vision[0-9]+`, run:

      $ {parent_command} list --uri \
            --filter 'name ~ vision[0-9]+' |
            xargs -n 1 {command}
  """

  @staticmethod
  def Args(parser):
    _AddDeleteArgs(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class DeleteBeta(Delete):
  r"""Delete an existing AI Platform model.

  ## EXAMPLES

  To delete all models matching the regular expression `vision[0-9]+`, run:

      $ {parent_command} list --uri \
            --filter 'name ~ vision[0-9]+' |
            xargs -n 1 {command}
  """

  @staticmethod
  def Args(parser):
    _AddDeleteArgs(parser)

  def Run(self, args):
    return _Run(args)
