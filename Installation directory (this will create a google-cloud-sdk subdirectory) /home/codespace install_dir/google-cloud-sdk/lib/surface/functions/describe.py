# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Displays details of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.functions.v1 import util as api_util_v1
from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.api_lib.functions.v2 import util as api_util_v2
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import util
from googlecloudsdk.command_lib.functions.v1 import decorator
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _PrintV2StateMessages(state_messages):
  log.critical('Function has the following conditions:')
  for state_message_string in api_util_v2.GetStateMessagesStrings(
      state_messages
  ):
    log.status.Print('  ' + state_message_string)
  log.status.Print('')  # newline


def _ValidateArgs(args):
  """Validate arguments."""
  if (
      args.IsSpecified('v2')
      and properties.VALUES.functions.gen2.IsExplicitlySet()
  ):
    if args.v2 and not flags.ShouldUseGen2():
      log.warning(
          'Conflicting flags "--v2" and "--no-gen2" specified, Cloud Functions'
          ' v2 APIs will be used.'
      )
    if not args.v2 and flags.ShouldUseGen2():
      log.warning(
          'Conflicting flags "--no-v2" and "--gen2" specified, Cloud Functions'
          ' v2 APIs will be used.'
      )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(util.FunctionResourceCommand, base.DescribeCommand):
  """Display details of a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to describe')
    flags.AddGen2Flag(parser, hidden=True, allow_v2=True)
    flags.AddV2Flag(parser)

  def _RunV1(self, args):
    client = api_util_v1.GetApiClientInstance()
    function = client.projects_locations_functions.Get(
        client.MESSAGES_MODULE.CloudfunctionsProjectsLocationsFunctionsGetRequest(
            name=args.CONCEPTS.name.Parse().RelativeName()
        )
    )

    if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      v2_function = self._v2_function or self._RunV2(args)
      return decorator.decorate_v1_function_with_v2_api_info(
          function, v2_function
      )

    # To facilitate testing, convert to dict for consistency with alpha track.
    return encoding.MessageToDict(function)

  def _RunV2(self, args):
    client = client_v2.FunctionsClient(self.ReleaseTrack())
    function = self._v2_function or client.GetFunction(
        args.CONCEPTS.name.Parse().RelativeName(), raise_if_not_found=True
    )
    if function.stateMessages:
      _PrintV2StateMessages(function.stateMessages)
    return function

  def Run(self, args):
    _ValidateArgs(args)

    if args.v2:
      return self._RunV2(args)

    return util.FunctionResourceCommand.Run(self, args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Display details of a Google Cloud Function."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeBeta):
  """Display details of a Google Cloud Function."""
