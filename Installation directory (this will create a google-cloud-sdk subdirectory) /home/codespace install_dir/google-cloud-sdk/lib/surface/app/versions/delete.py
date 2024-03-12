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

"""The Delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import text


class VersionsDeleteError(exceptions.Error):
  """Errors occurring when deleting versions."""
  pass


class Delete(base.DeleteCommand):
  """Delete a specified version.

  You cannot delete a version of a service that is currently receiving traffic.
  """

  detailed_help = {
      'EXAMPLES': """\
          To delete a specific version of a specific service, run:

            $ {command} --service=myService v1

          To delete a named version across all services, run:

            $ {command} v1

          To delete multiple versions of a specific service, run:

            $ {command} --service=myService v1 v2

          To delete multiple named versions across all services, run:

            $ {command} v1 v2
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('versions', nargs='+', help=(
        'The versions to delete (optionally filtered by the --service flag).'))
    parser.add_argument('--service', '-s',
                        help=('If specified, only delete versions from the '
                              'given service.'))

  def Run(self, args):
    client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())

    services = client.ListServices()

    # If a service is supplied, only list versions for that service
    if args.service:
      services = [s for s in services if s.id == args.service]

    all_versions = client.ListVersions(services)
    # Sort versions to make behavior deterministic enough for unit testing.
    versions = sorted(version_util.GetMatchingVersions(all_versions,
                                                       args.versions,
                                                       args.service), key=str)

    services_to_delete = []
    for service in sorted(services):
      service_versions = len(
          [v for v in all_versions if v.service == service.id])
      versions_to_delete = len([v for v in versions if v.service == service.id])
      if service_versions == versions_to_delete and service_versions > 0:
        if service.id == 'default':
          raise VersionsDeleteError(
              'The default service (module) may not be deleted, and must '
              'comprise at least one version.'
          )
        else:
          services_to_delete.append(service)
        for version in copy.copy(versions):
          if version.service == service.id:
            versions.remove(version)

    for version in versions:
      if version.traffic_split:
        # TODO(b/32869800): collect info on all versions before raising.
        raise VersionsDeleteError(
            'Version [{version}] is currently serving {allocation:.2f}% of '
            'traffic for service [{service}].\n\n'
            'Please move all traffic away via one of the following methods:\n'
            ' - deploying a new version with the `--promote` argument\n'
            ' - running `gcloud app services set-traffic`\n'
            ' - running `gcloud app versions migrate`'.format(
                version=version.id,
                allocation=version.traffic_split * 100,
                service=version.service))

    if services_to_delete:
      word = text.Pluralize(len(services_to_delete), 'service')
      log.warning(
          'Requested deletion of all existing versions for the following {0}:'
          .format(word))
      resource_printer.Print(services_to_delete, 'list', out=log.status)
      console_io.PromptContinue(prompt_string=(
          '\nYou cannot delete all versions of a service. Would you like to '
          'delete the entire {0} instead?').format(word), cancel_on_no=True)
      service_util.DeleteServices(client, services_to_delete)

    if versions:
      fmt = 'list[title="Deleting the following versions:"]'
      resource_printer.Print(versions, fmt, out=log.status)
      console_io.PromptContinue(cancel_on_no=True)
    else:
      if not services_to_delete:
        log.warning('No matching versions found.')

    version_util.DeleteVersions(client, versions)
