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
"""`gcloud alpha scc settings services modules describe-explicit` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc.settings import flags
from googlecloudsdk.command_lib.scc.settings import utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeExplicit(base.DescribeCommand):
  """Display module settings of Security Command Center(SCC)."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Describe explicit module settings of Security Command Center(SCC).
      """,
      'EXAMPLES':
          """\
        To describe the explict 'OPEN_FIREWALL' module setting in service 'SECURITY_HEALTH_ANALYTICS' of project "12345", run:

          $ {command} --project=12345 --service=SECURITY_HEALTH_ANALYTICS --module=OPEN_FIREWALL
      """
  }

  @staticmethod
  def Args(parser):
    flags.ExtractRequiredFlags(parser)
    flags.AddServiceArgument(parser)
    flags.AddModuleArgument(parser)

  def Run(self, args):
    """Call corresponding APIs based on the flag."""
    response = utils.SettingsClient().DescribeServiceExplicit(args)
    configs = response.modules.additionalProperties if response.modules else []
    state = [
        p.value.moduleEnablementState for p in configs if p.key == args.module
    ]
    if state:
      return state[0]
    else:
      log.status.Print(
          'No setting found for module {}. The module may not exist or no explicit setting is set.'
          .format(args.module))
      return None
