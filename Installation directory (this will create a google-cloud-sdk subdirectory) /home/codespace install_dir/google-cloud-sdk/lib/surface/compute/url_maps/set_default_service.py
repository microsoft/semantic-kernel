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

"""Command for changing the default service of a URL map."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_bucket_flags
from googlecloudsdk.command_lib.compute.backend_services import flags as backend_service_flags
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils
from googlecloudsdk.core import log


def _DetailedHelp():
  return {
      'brief':
          'Change the default service or default bucket of a URL map.',
      'DESCRIPTION':
          """\
      *{command}* is used to change the default service or default
      bucket of a URL map. The default service or default bucket is
      used for any requests for which there is no mapping in the
      URL map.
      """,
  }


def _Args(parser):
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      '--default-service',
      help=('A backend service that will be used for requests for which this '
            'URL map has no mappings.'))
  group.add_argument(
      '--default-backend-bucket',
      help=('A backend bucket that will be used for requests for which this '
            'URL map has no mappings.'))


def _GetGetRequest(client, url_map_ref):
  """Returns the request for the existing URL map resource."""
  return (client.apitools_client.urlMaps, 'Get',
          client.messages.ComputeUrlMapsGetRequest(
              urlMap=url_map_ref.Name(), project=url_map_ref.project))


def _GetSetRequest(client, url_map_ref, replacement):
  return (client.apitools_client.urlMaps, 'Update',
          client.messages.ComputeUrlMapsUpdateRequest(
              urlMap=url_map_ref.Name(),
              urlMapResource=replacement,
              project=url_map_ref.project))


def _Modify(resources, args, url_map, url_map_ref, backend_bucket_arg,
            backend_service_arg):
  """Returns a modified URL map message."""
  replacement = encoding.CopyProtoMessage(url_map)

  if args.default_service:
    default_backend_uri = url_maps_utils.ResolveUrlMapDefaultService(
        args, backend_service_arg, url_map_ref, resources).SelfLink()
  else:
    default_backend_uri = backend_bucket_arg.ResolveAsResource(
        args, resources).SelfLink()

  replacement.defaultService = default_backend_uri

  return replacement


def _GetRegionalGetRequest(client, url_map_ref):
  """Returns the request to get an existing regional URL map resource."""
  return (client.apitools_client.regionUrlMaps, 'Get',
          client.messages.ComputeRegionUrlMapsGetRequest(
              urlMap=url_map_ref.Name(),
              project=url_map_ref.project,
              region=url_map_ref.region))


def _GetRegionalSetRequest(client, url_map_ref, replacement):
  """Returns the request to update an existing regional URL map resource."""
  return (client.apitools_client.regionUrlMaps, 'Update',
          client.messages.ComputeRegionUrlMapsUpdateRequest(
              urlMap=url_map_ref.Name(),
              urlMapResource=replacement,
              project=url_map_ref.project,
              region=url_map_ref.region))


def _Run(args, holder, backend_bucket_arg, backend_service_arg, url_map_arg):
  """Issues requests necessary to set the default service of URL maps."""
  client = holder.client

  url_map_ref = url_map_arg.ResolveAsResource(
      args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  if url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
    get_request = _GetRegionalGetRequest(client, url_map_ref)
  else:
    get_request = _GetGetRequest(client, url_map_ref)

  old_url_map = client.MakeRequests([get_request])

  modified_url_map = _Modify(holder.resources, args, old_url_map[0],
                             url_map_ref, backend_bucket_arg,
                             backend_service_arg)

  # If existing object is equal to the proposed object or if
  # _Modify() returns None, then there is no work to be done, so we
  # print the resource and return.
  if old_url_map[0] == modified_url_map:
    log.status.Print('No change requested; skipping update for [{0}].'.format(
        old_url_map[0].name))
    return old_url_map

  if url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
    set_request = _GetRegionalSetRequest(client, url_map_ref, modified_url_map)
  else:
    set_request = _GetSetRequest(client, url_map_ref, modified_url_map)

  return client.MakeRequests([set_request])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class SetDefaultService(base.UpdateCommand):
  """Change the default service or default bucket of a URL map."""

  detailed_help = _DetailedHelp()
  BACKEND_BUCKET_ARG = None
  BACKEND_SERVICE_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKEND_BUCKET_ARG = (
        backend_bucket_flags.BackendBucketArgumentForUrlMap(required=False))
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap(required=False))
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.BACKEND_BUCKET_ARG, self.BACKEND_SERVICE_ARG,
                self.URL_MAP_ARG)
