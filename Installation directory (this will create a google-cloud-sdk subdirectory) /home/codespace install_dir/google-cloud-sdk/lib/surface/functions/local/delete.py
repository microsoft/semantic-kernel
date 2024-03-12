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
"""Delete a locally deployed Google Cloud Function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions.local import flags as local_flags
from googlecloudsdk.command_lib.functions.local import util
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': """
        `{command}` Delete a locally deployed Google Cloud Function.
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete a locally deployed Google Cloud Function."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    local_flags.AddDeploymentNameFlag(parser)

  def Run(self, args):
    util.ValidateDependencies()
    name = args.NAME[0]
    if not util.ContainerExists(name):
      raise util.ContainerNotFoundException(
          'The container ' + name + ' does not exist.')
    util.RemoveDockerContainer(name)
    log.status.Print('The container ' + name + ' has been deleted.')
