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
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.updater import snapshots
from googlecloudsdk.core.updater import update_manager


class Add(base.SilentCommand):
  """Add a new Trusted Tester component repository.
  """
  detailed_help = {
      'DESCRIPTION': """\
          Add a new Trusted Tester component repository to the list of
          repositories used by the component manager.  This will allow you to
          install and update components found in this repository.

          If you are participating in a Trusted Tester program, you will be
          instructed on the location of repositories with additional versions of
          one or more Google Cloud CLI components.
      """,
      'EXAMPLES': """\
          To add the Trusted Tester component repository
          http://repo.location.com run:

            $ gcloud components repositories add http://repo.location.com
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        nargs='+',
        metavar='URL',
        help='One or more URLs for the component repositories you want to add.')

  def Run(self, args):
    """Runs the add command."""

    # Ensure all the repos are valid.
    for repo in args.url:
      try:
        snapshots.ComponentSnapshot.FromURLs(
            repo, command_path='components.repositories.add')
      except snapshots.Error:
        raise exceptions.InvalidArgumentException(
            'url',
            'The given repository [{repo}] could not be fetched. Check your '
            'network settings and ensure that you have entered a valid '
            'repository URL.'.format(repo=repo))

    repos = update_manager.UpdateManager.GetAdditionalRepositories()
    added = []
    existing = []
    for url in args.url:
      if url in repos:
        existing.append(url)
      else:
        added.append(url)
    repos.extend(added)

    properties.PersistProperty(
        properties.VALUES.component_manager.additional_repositories,
        ','.join(repos),
        scope=properties.Scope.INSTALLATION)

    for url in added:
      log.status.Print('Added repository: [{repo}]'.format(repo=url))
    for url in existing:
      log.status.Print(
          'Repository already added, skipping: [{repo}]'.format(repo=url))
    return added
