# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""`gcloud alpha scc settings describe-explicit` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.settings import flags
from googlecloudsdk.command_lib.scc.settings import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeExplicit(base.DescribeCommand):
  """Display settings of Security Command Center(SCC)."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Describe settings of Security Command Center(SCC).
      """,
      'EXAMPLES':
          """\
        To describe effective settings of organization id="12345", run:

          $ {command} --organization=12345
      """
  }

  @staticmethod
  def Args(parser):
    flags.AddOrganizationFlag(parser, 'ORGANIZATION_ID')

  def Run(self, args):
    """Call corresponding APIs based on the flag."""
    return utils.SettingsClient().DescribeExplicit(args)
