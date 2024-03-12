# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""`gcloud service-directory endpoints create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import endpoints
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import flags
from googlecloudsdk.command_lib.service_directory import resource_args
from googlecloudsdk.command_lib.service_directory import util
from googlecloudsdk.core import log

_RESOURCE_TYPE = 'endpoint'
_ENDPOINT_LIMIT = 512


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Creates an endpoint."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Service Directory endpoint, run:

            $ {command} my-endpoint --service=my-service --namespace=my-namespace --location=us-east1 --address=1.2.3.4 --port=5 --annotations=a=b,c=d  --network=projects/123456789/locations/global/networks/default
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddEndpointResourceArg(
        parser,
        """to create. The endpoint id must be 1-63 characters long and match
        the regular expression `[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?` which means
        the first character must be a lowercase letter, and all following
        characters must be a dash, lowercase letter, or digit, except the last
        character, which cannot be a dash.""")
    flags.AddAddressFlag(parser)
    flags.AddPortFlag(parser)
    flags.AddAnnotationsFlag(parser, _RESOURCE_TYPE, _ENDPOINT_LIMIT)
    flags.AddNetworkFlag(parser)

  def Run(self, args):
    client = endpoints.EndpointsClient()
    endpoint_ref = args.CONCEPTS.endpoint.Parse()
    annotations = util.ParseAnnotationsArg(args.annotations, _RESOURCE_TYPE)

    result = client.Create(endpoint_ref, args.address, args.port, annotations,
                           args.network)
    log.CreatedResource(endpoint_ref.endpointsId, _RESOURCE_TYPE)

    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Creates an endpoint."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Service Directory endpoint, run:

            $ {command} my-endpoint --service=my-service --namespace=my-namespace --location=us-east1 --address=1.2.3.4 --port=5 --metadata=a=b,c=d --network=projects/123456789/locations/global/networks/default
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddEndpointResourceArg(
        parser,
        """to create. The endpoint id must be 1-63 characters long and match
        the regular expression `[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?` which means
        the first character must be a lowercase letter, and all following
        characters must be a dash, lowercase letter, or digit, except the last
        character, which cannot be a dash.""")
    flags.AddAddressFlag(parser)
    flags.AddPortFlag(parser)
    flags.AddMetadataFlag(parser, _RESOURCE_TYPE, _ENDPOINT_LIMIT)
    flags.AddNetworkFlag(parser)

  def Run(self, args):
    client = endpoints.EndpointsClientBeta()
    endpoint_ref = args.CONCEPTS.endpoint.Parse()
    metadata = util.ParseMetadataArg(args.metadata, _RESOURCE_TYPE)

    result = client.Create(endpoint_ref, args.address, args.port, metadata,
                           args.network)
    log.CreatedResource(endpoint_ref.endpointsId, _RESOURCE_TYPE)

    return result
