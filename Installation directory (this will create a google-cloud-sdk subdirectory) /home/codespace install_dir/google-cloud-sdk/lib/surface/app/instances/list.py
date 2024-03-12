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
"""The `app instances list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.calliope import base

APPENGINE_PATH_START = 'https://appengine.googleapis.com/{0}/'.format(
    appengine_api_client.AppengineApiClient.ApiVersion())


def _GetUri(resource):
  # TODO(b/29539463): Use parser when instances collection adds simple URIs
  # and a Get method
  try:
    return APPENGINE_PATH_START + resource.instance.name
  except AttributeError:
    return APPENGINE_PATH_START + resource['instance']['name']


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List the instances affiliated with the current App Engine project."""

  detailed_help = {
      'EXAMPLES': """\
          To list all App Engine instances, run:

              $ {command}

          To list all App Engine instances for a given service, run:

              $ {command} -s myservice

          To list all App Engine instances for a given version, run:

              $ {command} -v v1
          """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('--service', '-s',
                        help=('If specified, only list instances belonging to '
                              'the given service.'))
    parser.add_argument('--version', '-v',
                        help=('If specified, only list instances belonging to '
                              'the given version.'))
    parser.display_info.AddFormat("""
          table(
            service:sort=1,
            version:sort=2,
            id:sort=3,
            instance.vmStatus.yesno(no="N/A"),
            instance.vmLiveness,
            instance.vmDebugEnabled.yesno(yes="YES", no=""):label=DEBUG_MODE
          )
    """)
    parser.display_info.AddUriFunc(_GetUri)
    # TODO(b/29539463) Resources of this API are not parsable.
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    return api_client.GetAllInstances(args.service, args.version)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List the instances affiliated with the current App Engine project."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--service',
        '-s',
        help=('If specified, only list instances belonging to '
              'the given service.'))
    parser.add_argument(
        '--version',
        '-v',
        help=('If specified, only list instances belonging to '
              'the given version.'))
    parser.display_info.AddFormat("""
          table(
            service:sort=1,
            version:sort=2,
            id:sort=3,
            instance.vmStatus.yesno(no="N/A"),
            instance.vmLiveness,
            instance.vmDebugEnabled.yesno(yes="YES", no=""):label=DEBUG_MODE
          )
    """)
    parser.display_info.AddUriFunc(_GetUri)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())
    return api_client.GetAllInstances(args.service, args.version)
