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
"""`gcloud service-directory endpoints delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import endpoints
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import resource_args
from googlecloudsdk.core import log

_RESOURCE_TYPE = 'endpoint'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Deletes an endpoint."""

  detailed_help = {
      'EXAMPLES':
          """\
          To delete a Service Directory endpoint, run:

            $ {command} my-endpoint --service=my-service --namespace=my-namespace --location=us-east1
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddEndpointResourceArg(parser, 'to delete.')

  def Run(self, args):
    client = endpoints.EndpointsClient(self.GetReleaseTrack())
    endpoint_ref = args.CONCEPTS.endpoint.Parse()

    result = client.Delete(endpoint_ref)
    log.DeletedResource(endpoint_ref.endpointsId, _RESOURCE_TYPE)

    return result

  def GetReleaseTrack(self):
    return base.ReleaseTrack.GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeleteBeta(Delete):
  """Deletes an endpoint."""

  def GetReleaseTrack(self):
    return base.ReleaseTrack.BETA
