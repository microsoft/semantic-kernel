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

"""'types describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import dm_base
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
@dm_base.UseDmApi(dm_base.DmApiVersion.V2BETA)
class Describe(base.DescribeCommand, dm_base.DmCommand):
  """Describe a type."""

  detailed_help = {
      'EXAMPLES': """\
          To display information about a type provider type

            $ {command} NAME --provider=PROVIDER

          If you want to see information for a composite type you can use

            $ {command} NAME --provider=composite --format="yaml[json-decode] (composite_type)"
          """,
  }

  @staticmethod
  def Args(parser):
    """Called by calliope to gather arguments for this command.

    Args:
      parser: argparse parser for specifying command line arguments
    """
    parser.add_argument('name', help='Type name.')
    parser.add_argument('--provider',
                        help='Type provider name or its self-link.',
                        required=True)
    parser.display_info.AddFormat('yaml[json-decode](type_info)')

  def Run(self, args):
    """Runs 'types describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested TypeInfo.

    Raises:
      HttpException: An http error response was received while executing the api
          request.
      InvalidArgumentException: The requested type provider type could not
          be found.
    """
    type_provider_ref = self.resources.Parse(
        args.provider,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='deploymentmanager.typeProviders')
    request = self.messages.DeploymentmanagerTypeProvidersGetTypeRequest(
        project=type_provider_ref.project,
        type=args.name,
        typeProvider=type_provider_ref.typeProvider)
    type_message = self.client.typeProviders.GetType(request)

    composite_type_message = 'This is not a composite type.'
    if type_provider_ref.typeProvider == 'composite':
      composite_request = (self.messages.
                           DeploymentmanagerCompositeTypesGetRequest(
                               project=type_provider_ref.project,
                               compositeType=args.name))
      composite_type_message = self.client.compositeTypes.Get(composite_request)

    log.status.Print('You can reference this type in Deployment Manager with '
                     '[{0}/{1}:{2}]'.format(type_provider_ref.project,
                                            type_provider_ref.typeProvider,
                                            args.name))
    return {'type_info': type_message,
            'composite_type': composite_type_message}
