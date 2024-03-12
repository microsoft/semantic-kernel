# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Command for deleting backend services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags


class Delete(base.DeleteCommand):
  """Delete backend services.

    *{command}* deletes one or more backend services.
  """

  _BACKEND_SERVICE_ARG = flags.GLOBAL_REGIONAL_MULTI_BACKEND_SERVICE_ARG

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self._BACKEND_SERVICE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=backend_services_utils.GetDefaultScope())
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      backend_service = client.BackendService(
          ref, compute_client=holder.client)
      requests.extend(backend_service.Delete(only_generate_request=True))

    errors = []
    resources = holder.client.MakeRequests(requests, errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources
