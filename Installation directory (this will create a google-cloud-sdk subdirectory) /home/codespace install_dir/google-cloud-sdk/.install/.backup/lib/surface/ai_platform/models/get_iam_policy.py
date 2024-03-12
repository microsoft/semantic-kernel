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
"""Fetch the IAM policy for a model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.command_lib.ml_engine import region_util


def _AddGetIamPolicyArgs(parser):
  flags.GetModelResourceArg(
      positional=True, required=True,
      verb='to set IAM policy for').AddToParser(parser)
  flags.GetRegionArg(include_global=True).AddToParser(parser)
  base.URI_FLAG.RemoveFromParser(parser)


def _Run(args):
  region = region_util.GetRegion(args)
  with endpoint_util.MlEndpointOverrides(region=region):
    return models_util.GetIamPolicy(models.ModelsClient(), args.model)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class GetIamPolicyBeta(base.ListCommand):
  """Get the IAM policy for a model.

  Gets the IAM policy for the given model.

  Returns an empty policy if the resource does not have a policy set.

  ## EXAMPLES

  The following command gets the IAM policy for the model `my_model`:

    $ {command} my_model
  """

  @staticmethod
  def Args(parser):
    _AddGetIamPolicyArgs(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a model.

  Gets the IAM policy for the given model.

  Returns an empty policy if the resource does not have a policy set.

  ## EXAMPLES

  The following command gets the IAM policy for the model `my_model`:

    $ {command} my_model
  """

  @staticmethod
  def Args(parser):
    _AddGetIamPolicyArgs(parser)

  def Run(self, args):
    return _Run(args)
