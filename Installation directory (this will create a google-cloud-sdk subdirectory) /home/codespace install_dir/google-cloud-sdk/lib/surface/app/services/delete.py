# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""`gcloud app services delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import text
from six import moves


class Delete(base.DeleteCommand):
  """Delete services in the current project."""

  detailed_help = {
      'EXAMPLES': """\
          To delete a service (and all of its accompanying versions) in the
          current project, run:

            $ {command} service1

          To delete multiple services (and all of their accompanying versions)
          in the current project, run:

            $ {command} service1 service2
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('services', nargs='+', help='The service(s) to delete.')
    parser.add_argument(
        '--version', help='Delete a specific version of the given service(s).')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    # Why do this? It lets us know if we're missing services up front (fail
    # fast), and we get to control the error messages
    all_services = api_client.ListServices()

    services = service_util.GetMatchingServices(all_services, args.services)

    if args.version:
      console_io.PromptContinue(
          'Deleting version [{0}] of {1} [{2}].'.format(
              args.version, text.Pluralize(len(services), 'service'),
              ', '.join(moves.map(str, services))),
          cancel_on_no=True)
      versions = [version_util.Version(api_client.project, s.id, args.version)
                  for s in services]
      version_util.DeleteVersions(api_client, versions)
    else:
      console_io.PromptContinue(
          'Deleting {0} [{1}].'.format(
              text.Pluralize(len(services), 'service'),
              ', '.join(moves.map(str, services))),
          cancel_on_no=True)
      service_util.DeleteServices(api_client, services)
