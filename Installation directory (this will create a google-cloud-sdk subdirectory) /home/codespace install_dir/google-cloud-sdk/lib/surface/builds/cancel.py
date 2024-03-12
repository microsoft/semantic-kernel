# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Cancel build command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six


class Cancel(base.Command):
  """Cancel an ongoing build."""

  detailed_help = {
      'DESCRIPTION':
          'Cancel an ongoing build.',
      'EXAMPLES': ("""
            To cancel a build `123-456-789`:

                $ {command} '123-456-789'

            You may also cancel multiple builds at the same time:

                $ {command} '123-456-789', '987-654-321'
            """),
  }

  @staticmethod
  def Args(parser):
    flags.AddRegionFlag(parser)
    parser.add_argument(
        'builds',
        completer=flags.BuildsCompleter,
        nargs='+',  # Accept multiple builds.
        help='IDs of builds to cancel')
    parser.display_info.AddFormat(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    build_region = args.region or cloudbuild_util.DEFAULT_REGION

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    cancelled = []
    for build in args.builds:
      build_ref = resources.REGISTRY.Parse(
          build,
          params={
              'projectsId': properties.VALUES.core.project.GetOrFail,
              'locationsId': build_region,
              'buildsId': build,
          },
          collection='cloudbuild.projects.locations.builds')
      cancelled_build = client.projects_locations_builds.Cancel(
          messages.CancelBuildRequest(
              name=build_ref.RelativeName(),
              projectId=build_ref.projectsId,
              id=build_ref.buildsId,
          ))
      log.status.write('Cancelled [{r}].\n'.format(r=six.text_type(build_ref)))
      cancelled.append(cancelled_build)
    return cancelled
