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
"""Command to display status of Kuberun Applications."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from googlecloudsdk.api_lib.kuberun import application_status
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import status_printer

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To get the status of the application in environment ``ENV'', run:

            $ {command} --environment ENV
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetStatus(kuberun_command.KubeRunCommand, base.ListCommand):
  """Get status of the application."""

  detailed_help = _DETAILED_HELP
  flags = [flags.EnvironmentFlag()]

  @classmethod
  def Args(cls, parser):
    super(GetStatus, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    status_printer.ApplicationStatusPrinter.Register(parser)

  def Command(self):
    return ['applications', 'get-status']

  def SuccessResult(self, out, args):
    if out:
      results = json.loads(out)
      for entry in results:
        entry['status'] = application_status.ApplicationStatus.FromJSON(
            entry['status'])
      return results
    return []
