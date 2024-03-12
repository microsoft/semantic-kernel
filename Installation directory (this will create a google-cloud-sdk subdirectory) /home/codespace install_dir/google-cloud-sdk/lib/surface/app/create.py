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
"""The app create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import create_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create an App Engine app within the current Google Cloud Project."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To create an app with region chosen interactively, run:

              $ {command}

          To create an app in the us-central region, run:

              $ {command} --region=us-central

          To create an app that with a user-managed service account, run:

              $ {command} --service-account=SERVICE_ACCOUNT
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--region',
        help=('The region to create the app within.  '
              'Use `gcloud app regions list` to list available regions.  '
              'If not provided, select region interactively.'))
    parser.add_argument(
        '--service-account',
        help=(
            'The app-level default service account to create the app with.  '
            'Note that you can specify a distinct service account for each App Engine version with `gcloud app deploy --service-account`. However if you do not specify a version-level service account, this default will be used. '
            'If this parameter is not provided for app creation, the app-level default will be set to be the out-of-box App Engine Default Service Account, https://cloud.google.com/appengine/docs/standard/python3/service-account outlines the limitation of that service account.'
        ))

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    if args.region:
      create_util.CreateApp(
          api_client,
          project,
          args.region,
          service_account=args.service_account)
    elif console_io.CanPrompt():
      create_util.CheckAppNotExists(api_client, project)
      create_util.CreateAppInteractively(
          api_client, project, service_account=args.service_account)
    else:
      raise create_util.UnspecifiedRegionError(
          'Prompts are disabled. Region must be specified either by the '
          '`--region` flag or interactively. Use `gcloud app regions '
          'list` to list available regions.')
    log.status.Print('Success! The app is now created. Please use '
                     '`gcloud app deploy` to deploy your first app.')
