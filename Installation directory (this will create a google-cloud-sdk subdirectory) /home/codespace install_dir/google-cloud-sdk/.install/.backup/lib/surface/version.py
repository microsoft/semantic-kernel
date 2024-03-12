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

"""Command to print version information for Google Cloud CLI components.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import update_manager


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Version(base.Command):
  """Print version information for Google Cloud CLI components."""

  detailed_help = {
      'EXAMPLES': """
          To print the version information for each installed Google Cloud CLI
          components and print a message if updates are available, run:

            $ {command}
          """,
  }

  category = base.SDK_TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('flattened[no-pad,separator=" "]')

  def Run(self, args):
    if config.Paths().sdk_root:
      # Components are only valid if this is a built Google Cloud CLI.
      manager = update_manager.UpdateManager()
      versions = dict(manager.GetCurrentVersionsInformation())
    else:
      versions = {}
    versions['Google Cloud SDK'] = config.CLOUD_SDK_VERSION
    return versions

  def Epilog(self, resources_were_displayed):
    if config.Paths().sdk_root:
      # Components are only valid if this is a built Cloud SDK.
      manager = update_manager.UpdateManager()
      if manager.UpdatesAvailable():
        log.status.write("""\
Updates are available for some Google Cloud CLI components.  To install them,
please run:
  $ gcloud components update\n""")
