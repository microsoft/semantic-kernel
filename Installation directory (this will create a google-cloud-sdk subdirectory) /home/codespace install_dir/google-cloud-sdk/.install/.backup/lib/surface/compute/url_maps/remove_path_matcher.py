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

"""Command for removing a path matcher from a URL map."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils


def _DetailedHelp():
  return {
      'brief':
          'Remove a path matcher from a URL map.',
      'DESCRIPTION': """
*{command}* is used to remove a path matcher from a URL
map. When a path matcher is removed, all host rules that
refer to the path matcher are also removed.
""",
      'EXAMPLES': """
To remove the path matcher named ``MY-MATCHER'' from the URL map named
``MY-URL-MAP'', you can use this command:

  $ {command} MY-URL-MAP --path-matcher-name=MY-MATCHER
""",
  }


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


def _Modify(args, existing):
  """Returns a modified URL map message."""
  replacement = encoding.CopyProtoMessage(existing)

  # Removes the path matcher.
  new_path_matchers = []
  path_matcher_found = False
  for path_matcher in existing.pathMatchers:
    if path_matcher.name == args.path_matcher_name:
      path_matcher_found = True
    else:
      new_path_matchers.append(path_matcher)

  if not path_matcher_found:
    raise compute_exceptions.ArgumentError(
        'No path matcher with the name [{0}] was found.'.format(
            args.path_matcher_name))

  replacement.pathMatchers = new_path_matchers

  # Removes all host rules that refer to the path matcher.
  new_host_rules = []
  for host_rule in existing.hostRules:
    if host_rule.pathMatcher != args.path_matcher_name:
      new_host_rules.append(host_rule)
  replacement.hostRules = new_host_rules

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


def _Run(args, holder, url_map_arg):
  """Issues requests necessary to remove path matcher on URL maps."""
  client = holder.client

  url_map_ref = url_map_arg.ResolveAsResource(
      args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
  if url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
    get_request = _GetRegionalGetRequest(client, url_map_ref)
  else:
    get_request = _GetGetRequest(client, url_map_ref)

  url_map = client.MakeRequests([get_request])[0]
  modified_url_map = _Modify(args, url_map)

  if url_maps_utils.IsRegionalUrlMapRef(url_map_ref):
    set_request = _GetRegionalSetRequest(client, url_map_ref, modified_url_map)
  else:
    set_request = _GetSetRequest(client, url_map_ref, modified_url_map)

  return client.MakeRequests([set_request])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class RemovePathMatcher(base.UpdateCommand):
  """Remove a path matcher from a URL map."""

  detailed_help = _DetailedHelp()
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser)

    parser.add_argument(
        '--path-matcher-name',
        required=True,
        help='The name of the path matcher to remove.')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.URL_MAP_ARG)
