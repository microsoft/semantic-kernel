# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Code that's shared between multiple url-maps subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import operation_utils
from googlecloudsdk.command_lib.compute import scope as compute_scope


def ResolveUrlMapDefaultService(args, backend_service_arg, url_map_ref,
                                resources):
  """Parses the backend service that is pointed to by a URL map from args.

  This function handles parsing a regional/global backend service that is
  pointed to by a regional/global URL map.

  Args:
    args: The arguments provided to the url-maps command
    backend_service_arg: The ResourceArgument specification for the
                         backend service argument.
    url_map_ref: The resource reference to the URL MAP. This is returned by
                 parsing the URL map arguments provided.
    resources: ComputeApiHolder resources.

  Returns:
    Backend service reference parsed from args.
  """

  if not compute_scope.IsSpecifiedForFlag(args, 'default_service'):
    if IsRegionalUrlMapRef(url_map_ref):
      args.default_service_region = url_map_ref.region
    else:
      args.global_default_service = args.default_service

  return backend_service_arg.ResolveAsResource(args, resources)


def IsRegionalUrlMapRef(url_map_ref):
  """Returns True if the URL Map reference is regional."""

  return url_map_ref.Collection() == 'compute.regionUrlMaps'


def IsGlobalUrlMapRef(url_map_ref):
  """Returns True if the URL Map reference is global."""

  return url_map_ref.Collection() == 'compute.urlMaps'


def SendGetRequest(client, url_map_ref):
  """Send Url Maps get request."""
  if url_map_ref.Collection() == 'compute.regionUrlMaps':
    return client.apitools_client.regionUrlMaps.Get(
        client.messages.ComputeRegionUrlMapsGetRequest(**url_map_ref.AsDict()))
  return client.apitools_client.urlMaps.Get(
      client.messages.ComputeUrlMapsGetRequest(**url_map_ref.AsDict()))


def WaitForOperation(resources, service, operation, url_map_ref, message):
  """Waits for the URL map operation to finish.

  Args:
    resources: The resource parser.
    service: apitools.base.py.base_api.BaseApiService, the service representing
      the target of the operation.
    operation: The operation to wait for.
    url_map_ref: The URL map reference.
    message: The message to show.

  Returns:
    The operation result.
  """
  if url_map_ref.Collection() == 'compute.regionUrlMaps':
    collection = operation_utils.GetRegionalOperationsCollection()
  else:
    collection = operation_utils.GetGlobalOperationsCollection()

  return operation_utils.WaitForOperation(resources, service, operation,
                                          collection, url_map_ref, message)
