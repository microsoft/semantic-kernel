# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to describe the operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import operations as apis
from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To describe a specific apphub operation with the name `my-operation`, run:

          $ {command} my-operation
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGA(base.DescribeCommand):
  """Describe an Apphub operation (long-running operation)."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeOperationFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = apis.OperationsClient(release_track=base.ReleaseTrack.GA)
    op_ref = api_lib_utils.GetOperationRef(args)
    return client.Describe(operation=op_ref.RelativeName())


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(base.DescribeCommand):
  """Describe an Apphub operation (long-running operation)."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeOperationFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = apis.OperationsClient(release_track=base.ReleaseTrack.ALPHA)
    op_ref = api_lib_utils.GetOperationRef(args)
    return client.Describe(operation=op_ref.RelativeName())
