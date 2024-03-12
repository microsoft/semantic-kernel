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
"""Command for creating URL maps."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.backend_buckets import flags as backend_bucket_flags
from googlecloudsdk.command_lib.compute.backend_services import flags as backend_service_flags
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils


def _DetailedHelp():
  return {
      'brief':
          'Create a URL map.',
      'DESCRIPTION':
          """
      *{command}* is used to create URL maps which map HTTP and
      HTTPS request URLs to backend services and backend buckets.
      Mappings are done using a longest-match strategy.

      There are two components to a mapping: a host rule and a path
      matcher. A host rule maps one or more hosts to a path
      matcher. A path matcher maps request paths to backend
      services or backend buckets. For example, a host rule can map
      the hosts ``*.google.com'' and ``google.com'' to a path
      matcher called ``www''. The ``www'' path matcher in turn can
      map the path ``/search/*'' to the search backend service, the
      path ``/static/*'' to the static backend bucket  and everything
      else to a default backend service or default backend bucket.

      Host rules and patch matchers can be added to the URL map
      after the map is created by using `gcloud compute url-maps edit`
      or by using `gcloud compute url-maps add-path-matcher`
      and `gcloud compute url-maps add-host-rule`.
      """,
      'EXAMPLES':
          """
        To create a global URL map with a default service, run:

        $ {command} URL_MAP_NAME --default-service=BACKEND_SERVICE_NAME

        To create a regional URL map with a default service, run:

        $ {command} URL_MAP_NAME --default-service=BACKEND_SERVICE_NAME --region=REGION_NAME

        To create a global URL map with a default backend bucket, run:

        $ {command} URL_MAP_NAME --default-backend-bucket=BACKEND_BUCKET_NAME
      """,
  }


def _Args(parser):
  """Common arguments to create commands for each release track."""
  parser.add_argument(
      '--description', help='An optional, textual description for the URL map.')

  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      '--default-service',
      help=('A backend service that will be used for requests for which this '
            'URL map has no mappings. Exactly one of --default-service or '
            '--default-backend-bucket is required.'))
  group.add_argument(
      '--default-backend-bucket',
      help=('A backend bucket that will be used for requests for which this '
            'URL map has no mappings. Exactly one of --default-service or '
            '--default-backend-bucket is required.'))
  parser.display_info.AddCacheUpdater(flags.UrlMapsCompleter)


def _MakeGlobalRequest(args, url_map_ref, default_backend_uri, client):
  request = client.messages.ComputeUrlMapsInsertRequest(
      project=url_map_ref.project,
      urlMap=client.messages.UrlMap(
          defaultService=default_backend_uri,
          description=args.description,
          name=url_map_ref.Name()))
  return client.MakeRequests([(client.apitools_client.urlMaps, 'Insert',
                               request)])


def _MakeRegionalRequest(args, url_map_ref, default_backend_uri, client):
  request = client.messages.ComputeRegionUrlMapsInsertRequest(
      project=url_map_ref.project,
      urlMap=client.messages.UrlMap(
          defaultService=default_backend_uri,
          description=args.description,
          name=url_map_ref.Name()),
      region=url_map_ref.region)
  return client.MakeRequests([(client.apitools_client.regionUrlMaps, 'Insert',
                               request)])


def _Run(args, holder, backend_bucket_arg, backend_service_arg, url_map_arg):
  """Issues requests necessary to create a Url Map."""
  client = holder.client

  url_map_ref = url_map_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  if args.default_service:
    default_backend_uri = url_maps_utils.ResolveUrlMapDefaultService(
        args, backend_service_arg, url_map_ref, holder.resources).SelfLink()
  else:
    default_backend_uri = backend_bucket_arg.ResolveAsResource(
        args, holder.resources).SelfLink()

  if url_maps_utils.IsGlobalUrlMapRef(url_map_ref):
    return _MakeGlobalRequest(args, url_map_ref, default_backend_uri, client)
  elif url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
    return _MakeRegionalRequest(args, url_map_ref, default_backend_uri, client)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a URL map."""

  detailed_help = _DetailedHelp()
  BACKEND_BUCKET_ARG = None
  BACKEND_SERVICE_ARG = None
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
    cls.BACKEND_BUCKET_ARG = (
        backend_bucket_flags.BackendBucketArgumentForUrlMap(required=False))
    cls.BACKEND_SERVICE_ARG = (
        backend_service_flags.BackendServiceArgumentForUrlMap(required=False))
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser, operation_type='create')
    _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.BACKEND_BUCKET_ARG, self.BACKEND_SERVICE_ARG,
                self.URL_MAP_ARG)
