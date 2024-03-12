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
"""Triggers execution of a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import util
from googlecloudsdk.command_lib.functions.v1.call import command as command_v1
from googlecloudsdk.command_lib.functions.v2.call import command as command_v2


_DETAILED_HELP = {
    'EXAMPLES': """
        To call a function, giving it 'Hello World!' in the message field of its event
        argument (depending on your environment you might need to escape
        characters in `--data` flag value differently), run:

            $ {command} helloWorld --data='{"message": "Hello World!"}'

        Note that this method has a limited quota which cannot be increased. It is
        intended for testing and debugging and should not be used in production.

        Calls to HTTP-triggered functions are sent as HTTP POST requests. To use other
        HTTP methods, use a dedicated HTTP request tool such as cURL or wget.

        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Call(util.FunctionResourceCommand):
  """Triggers execution of a Google Cloud Function."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to execute')
    data_flag_group = parser.add_mutually_exclusive_group()
    flags.AddDataFlag(data_flag_group)

    # Flags for GCFv2
    flags.AddGen2Flag(parser, hidden=True)
    flags.AddCloudEventsFlag(data_flag_group)

  def _RunV1(self, args):
    return command_v1.Run(args, self.ReleaseTrack())

  def _RunV2(self, args):
    return command_v2.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CallBeta(Call):
  """Triggers execution of a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register beta (and implicitly alpha) flags for this command."""
    Call.Args(parser)

    # Flags for beta (and implicitly alpha)
    flags.AddGcloudHttpTimeoutFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CallAlpha(CallBeta):
  """Triggers execution of a Google Cloud Function."""
