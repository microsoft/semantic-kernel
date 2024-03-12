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

"""Deletes a Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import util
from googlecloudsdk.command_lib.functions.v1.delete import command as command_v1
from googlecloudsdk.command_lib.functions.v2.delete import command as command_v2


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand, util.FunctionResourceCommand):
  """Delete a Google Cloud Function."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddFunctionResourceArg(parser, 'to delete')
    parser.display_info.AddCacheUpdater(None)

    flags.AddGen2Flag(parser, hidden=True)

  def _RunV1(self, args):
    return command_v1.Run(args)

  def _RunV2(self, args):
    return command_v2.Run(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Delete a Google Cloud Function."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DeleteAlpha(DeleteBeta):
  """Delete a Google Cloud Function."""
