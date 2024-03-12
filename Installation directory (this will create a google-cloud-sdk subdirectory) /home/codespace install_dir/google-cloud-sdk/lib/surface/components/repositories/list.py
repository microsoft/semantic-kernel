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

"""The command to list installed/available gcloud components."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.updater import update_manager


def TransformLastUpdate(r):
  try:
    snapshot = snapshots.ComponentSnapshot.FromURLs(
        r, command_path='components.repositories.list')
    return snapshot.sdk_definition.LastUpdatedString()
  except (AttributeError, TypeError, snapshots.URLFetchError):
    return 'Unknown'


_COMPONENTS_REPOSITORIES_TRANSFORMS = {
    'last_update': TransformLastUpdate,
}


class List(base.ListCommand):
  """List any Trusted Tester component repositories you have registered.
  """
  detailed_help = {
      'DESCRIPTION': """
          List all Trusted Tester component repositories that are registered
          with the component manager.  If you have additional repositories, the
          component manager will look at them to discover additional components
          to install, or different versions of existing components that are
          available.
      """,
      'EXAMPLES': """
          To list all Trusted Tester component repositories that are registered
          with the component manager, run:

            $ {command}
      """
  }

  @staticmethod
  def Args(parser):
    """Adds/removes args for this command."""
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat("""
          table(
            .:label=REPOSITORY,
            last_update():label=LAST_UPDATE
          )
    """)
    parser.display_info.AddTransforms(_COMPONENTS_REPOSITORIES_TRANSFORMS)

  def Run(self, args):
    """Runs the list command."""
    repos = update_manager.UpdateManager.GetAdditionalRepositories()
    return repos if repos else []

  def Epilog(self, resources_were_displayed):
    if not resources_were_displayed:
      log.status.write(
          'You have no registered component repositories.  To add one, run:\n'
          '  $ gcloud components repositories add URL\n\n')
