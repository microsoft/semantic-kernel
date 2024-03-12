# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""`gcloud app services update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.api_lib.app import service_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
import six


class IngressSettingError(exceptions.Error):
  """Errors occurring when setting ingress settings."""
  pass


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Update(base.Command):
  """Update service-level settings.

  Update ingress traffic settings for an app.
  """

  detailed_help = {
      'EXAMPLES': """To update ingress traffic settings for """
                  """the default service, run:

              $ {command} default --ingress=internal-only
                  """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('services', nargs='*', help=('The services to modify.'))
    parser.add_argument(
        '--ingress',
        choices=['all', 'internal-only', 'internal-and-cloud-load-balancing'],
        default='all',
        required=True,
        help='Control what traffic can reach the app.')

  def Run(self, args):
    api_client = appengine_api_client.GetApiClientForTrack(self.ReleaseTrack())

    all_services = api_client.ListServices()
    services = service_util.GetMatchingServices(all_services, args.services)

    errors = {}
    for service in services:
      ingress_traffic_allowed = (
          api_client.messages.NetworkSettings
          .IngressTrafficAllowedValueValuesEnum.INGRESS_TRAFFIC_ALLOWED_ALL)
      if args.ingress == 'internal-only':
        ingress_traffic_allowed = (
            api_client.messages.NetworkSettings
            .IngressTrafficAllowedValueValuesEnum
            .INGRESS_TRAFFIC_ALLOWED_INTERNAL_ONLY)
      elif args.ingress == 'internal-and-cloud-load-balancing':
        ingress_traffic_allowed = (
            api_client.messages.NetworkSettings
            .IngressTrafficAllowedValueValuesEnum
            .INGRESS_TRAFFIC_ALLOWED_INTERNAL_AND_LB)
      try:
        operations_util.CallAndCollectOpErrors(
            api_client.SetIngressTrafficAllowed, service.id,
            ingress_traffic_allowed)
      except operations_util.MiscOperationError as err:
        errors[service.id] = six.text_type(err)
    if errors:
      combined_error_msg = 'Error updating service(s): '
      for service, error_msg in errors.items():
        combined_error_msg += '\n- %s\n  %s' % (service, error_msg)
      raise IngressSettingError(combined_error_msg + '\n\n')
