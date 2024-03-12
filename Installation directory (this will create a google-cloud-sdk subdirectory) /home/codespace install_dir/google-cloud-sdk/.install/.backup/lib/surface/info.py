# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A command that prints out information about your gcloud environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.diagnostics import network_diagnostics
from googlecloudsdk.core.diagnostics import property_diagnostics


def _RunDiagnostics(ignore_hidden_property_allowlist):
  passed_network = network_diagnostics.NetworkDiagnostic().RunChecks()
  passed_props = property_diagnostics.PropertyDiagnostic(
      ignore_hidden_property_allowlist).RunChecks()
  return passed_network and passed_props


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Info(base.Command):
  """Display information about the current gcloud environment."""

  detailed_help = {
      'EXAMPLES': """
          To display information about the current gcloud environment including
          the Google Cloud account, project and directory paths for
          logs, run:

            $ {command}

          To check network connectivity and hidden properties, run:

            $ {command} --run-diagnostics

          To print the contents of the most recent log file, run:

            $ {command} --show-log
          """,
  }

  category = base.SDK_TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    mode = parser.add_group(mutex=True)
    mode.add_argument(
        '--show-log',
        action='store_true',
        help='Print the contents of the last log file.')
    diagnostics = mode.add_group()
    diagnostics.add_argument(
        '--run-diagnostics',
        action='store_true',
        help='Run diagnostics on your installation of the Google Cloud CLI.')
    diagnostics.add_argument(
        '--ignore-hidden-property-allowlist',
        action='store_true',
        hidden=True,
        help='Ignore the hidden property allowlist.')
    parser.add_argument(
        '--anonymize',
        action='store_true',
        help='Minimize any personal identifiable information. '
             'Use it when sharing output with others.')

  def Run(self, args):
    if args.run_diagnostics:
      passed = _RunDiagnostics(args.ignore_hidden_property_allowlist)
      if passed:
        return None
      else:
        raise exceptions.Error('Some of the checks in diagnostics failed.')
    return info_holder.InfoHolder(
        anonymizer=info_holder.Anonymizer() if args.anonymize else None)

  def Display(self, args, info):
    if not info:
      return
    if not args.show_log:
      log.Print(info)
    elif info.logs.last_log:
      log.Print('\nContents of log file: [{0}]\n'
                '==========================================================\n'
                '{1}\n\n'
                .format(info.logs.last_log, info.logs.LastLogContents()))
