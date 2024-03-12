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
"""Command to list available Kuberun Development Kits."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import devkit
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import kuberun_command

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all available Development Kits, run:

            $ {command}
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommand, base.ListCommand):
  """Lists available Development Kits."""

  detailed_help = _DETAILED_HELP
  flags = []

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    columns = ['id', 'name', 'description', 'version']
    parser.display_info.AddFormat('table({})'.format(','.join(columns)))

  def Command(self):
    return ['devkits', 'list']

  def SuccessResult(self, out, args):
    if out:
      json_list = json.loads(out)
      return [devkit.DevKit.FromJSON(x) for x in json_list]
    else:
      return []
