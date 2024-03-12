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
"""Command to add IAM policy binding for a model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import models
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.command_lib.ml_engine import region_util


def _AddIamPolicyBindingFlags(parser, add_condition=False):
  flags.GetModelName().AddToParser(parser)
  flags.GetRegionArg(include_global=True).AddToParser(parser)
  iam_util.AddArgsForAddIamPolicyBinding(
      parser, flags.MlEngineIamRolesCompleter, add_condition=add_condition)


def _Run(args):
  region = region_util.GetRegion(args)
  with endpoint_util.MlEndpointOverrides(region=region):
    return models_util.AddIamPolicyBinding(models.ModelsClient(), args.model,
                                           args.member, args.role)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddIamPolicyBinding(base.Command):
  """Add IAM policy binding to a model."""

  detailed_help = iam_util.GetDetailedHelpForAddIamPolicyBinding(
      'model', 'my_model', role='roles/ml.admin', condition=False)

  @staticmethod
  def Args(parser):
    _AddIamPolicyBindingFlags(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddIamPolicyBindingBeta(AddIamPolicyBinding):
  """Add IAM policy binding to a model."""

  detailed_help = iam_util.GetDetailedHelpForAddIamPolicyBinding(
      'model', 'my_model', role='roles/ml.admin', condition=False)

  @staticmethod
  def Args(parser):
    _AddIamPolicyBindingFlags(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBindingAlpha(base.Command):
  """Adds IAM policy binding to a model.

  Adds a policy binding to the IAM policy of a ML engine model, given a model ID
  and the binding. One binding consists of a member, a role, and an optional
  condition.
  """
  detailed_help = iam_util.GetDetailedHelpForAddIamPolicyBinding(
      'model', 'my_model', role='roles/ml.admin', condition=True)

  @staticmethod
  def Args(parser):
    _AddIamPolicyBindingFlags(parser, add_condition=True)

  def Run(self, args):
    region = region_util.GetRegion(args)
    with endpoint_util.MlEndpointOverrides(region=region):
      condition = iam_util.ValidateAndExtractCondition(args)
      iam_util.ValidateMutexConditionAndPrimitiveRoles(condition, args.role)
      return models_util.AddIamPolicyBindingWithCondition(
          models.ModelsClient(),
          args.model,
          args.member,
          args.role,
          condition)
