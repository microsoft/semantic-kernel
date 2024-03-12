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
"""Stream-logs command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Log(base.Command):
  """Stream the logs for a build."""
  detailed_help = {
      'DESCRIPTION': 'Stream the logs for a build.',
      'EXAMPLES': ("""
            To stream logs for in progress build `123-456-789`:

                $ {command} --stream `123-456-789`

            To display logs for a completed build `098-765-432`:

                $ {command} `098-765-432`
            """),
  }

  _support_gcl = False

  @staticmethod
  def Args(parser):
    flags.AddRegionFlag(parser)
    flags.AddBuildArg(parser, intro='The build whose logs shall be printed.')
    parser.add_argument(
        '--stream',
        help=('If a build is ongoing, stream the logs to stdout until '
              'the build completes.'),
        action='store_true')

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

    build_ref = resources.REGISTRY.Parse(
        args.build,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
            'locationsId': build_region,
        },
        collection='cloudbuild.projects.locations.builds')

    logger = cb_logs.CloudBuildClient(client, messages, self._support_gcl)
    if args.stream:
      if not self._support_gcl:
        log.status.Print(
            '\ngcloud builds log --stream only displays logs from Cloud'
            ' Storage. To view logs from Cloud Logging, run:\ngcloud beta'
            ' builds log --stream\n')
      logger.Stream(build_ref)
      return

    # Just print out what's available now.
    logger.PrintLog(build_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class LogBeta(Log):
  """Stream the logs for a build."""

  _support_gcl = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class LogAlpha(LogBeta):
  """Stream the logs for a build."""

  _support_gcl = True

