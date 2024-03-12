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
"""`gcloud service-directory services update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import services
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import flags
from googlecloudsdk.command_lib.service_directory import resource_args
from googlecloudsdk.command_lib.service_directory import util
from googlecloudsdk.core import log

_RESOURCE_TYPE = 'service'
_SERVICE_LIMIT = 2000


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Updates a service."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Service Directory service, run:

            $ {command} my-service --namespace=my-namespace --location=us-east1 --annotations=a=b,c=d
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddServiceResourceArg(parser, 'to update.')
    flags.AddAnnotationsFlag(parser, _RESOURCE_TYPE, _SERVICE_LIMIT)

  def Run(self, args):
    client = services.ServicesClient()
    service_ref = args.CONCEPTS.service.Parse()
    annotations = util.ParseAnnotationsArg(args.annotations, _RESOURCE_TYPE)

    result = client.Update(service_ref, annotations)
    log.UpdatedResource(service_ref.servicesId, _RESOURCE_TYPE)

    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Updates a service."""

  detailed_help = {
      'EXAMPLES':
          """\
          To update a Service Directory service, run:

            $ {command} my-service --namespace=my-namespace --location=us-east1 --metadata=a=b,c=d
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddServiceResourceArg(parser, 'to update.')
    flags.AddMetadataFlag(parser, _RESOURCE_TYPE, _SERVICE_LIMIT)

  def Run(self, args):
    client = services.ServicesClientBeta()
    service_ref = args.CONCEPTS.service.Parse()
    metadata = util.ParseMetadataArg(args.metadata, _RESOURCE_TYPE)

    result = client.Update(service_ref, metadata)
    log.UpdatedResource(service_ref.servicesId, _RESOURCE_TYPE)

    return result
