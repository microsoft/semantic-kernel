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
"""Command for listing operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


def AddFlags(parser, is_ga):
  """Helper function for adding flags dependant on the release track."""
  parser.display_info.AddFormat("""\
      table(
        name,
        operationType:label=TYPE,
        targetLink.scope():label=TARGET,
        operation_http_status():label=HTTP_STATUS,
        status,
        insertTime:label=TIMESTAMP
      )""")
  if is_ga:
    lister.AddMultiScopeListerFlags(
        parser, zonal=True, regional=True, global_=True)
  else:
    lister.AddBaseListerArgs(parser)
    parser.add_argument(
        '--zones',
        metavar='ZONE',
        help=('If arguments are provided, only resources from the given '
              'zones are shown. If no arguments are provided all zonal '
              'operations are shown.'),
        type=arg_parsers.ArgList())
    parser.add_argument(
        '--regions',
        metavar='REGION',
        help=('If arguments are provided, only resources from the given '
              'regions are shown. If no arguments are provided all regional '
              'operations are shown.'),
        type=arg_parsers.ArgList())
    parser.add_argument(
        '--global',
        action='store_true',
        help='If provided, all global resources are shown.',
        default=False)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine operations."""

  @staticmethod
  def Args(parser):
    AddFlags(parser, True)

  def NoArguments(self, args):
    """Determine if the user provided any flags indicating scope."""
    no_compute_args = (args.zones is None and args.regions is None and
                       not getattr(args, 'global'))
    return no_compute_args

  def Run(self, args):
    """Yields zonal, regional, and/or global resources."""
    compute_holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = compute_holder.client

    # This is True if the user provided no flags indicating scope.
    no_scope_flags = self.NoArguments(args)

    requests = []
    request_data = lister.ParseNamesAndRegexpFlags(args,
                                                   compute_holder.resources)

    # TODO(b/36050874): Start using aggregatedList for zones and regions when
    # the operations list API supports them.
    if no_scope_flags:
      requests.append(
          (compute_client.apitools_client.globalOperations, 'AggregatedList',
           compute_client.apitools_client.globalOperations.GetRequestType(
               'AggregatedList')(
                   filter=request_data.filter,
                   maxResults=request_data.max_results,
                   project=list(request_data.scope_set)[0].project)))
    else:
      if getattr(args, 'global'):
        requests.append(
            (compute_client.apitools_client.globalOperations, 'List',
             compute_client.apitools_client.globalOperations.GetRequestType(
                 'List')(
                     filter=request_data.filter,
                     maxResults=request_data.max_results,
                     project=list(request_data.scope_set)[0].project)))
      if args.regions is not None:
        args_region_names = [
            compute_holder.resources.Parse(  # pylint:disable=g-complex-comprehension
                region,
                params={'project': properties.VALUES.core.project.GetOrFail},
                collection='compute.regions').Name()
            for region in args.regions or []]
        # If no regions were provided by the user, fetch a list.
        errors = []
        region_names = (
            args_region_names or [res.name for res in lister.GetGlobalResources(  # pylint:disable=g-complex-comprehension
                service=compute_client.apitools_client.regions,
                project=properties.VALUES.core.project.GetOrFail(),
                filter_expr=None,
                http=compute_client.apitools_client.http,
                batch_url=compute_client.batch_url,
                errors=errors)])
        if errors:
          utils.RaiseToolException(
              errors,
              'Unable to fetch a list of regions. Specifying [--regions] may '
              'fix this issue:')
        for region_name in region_names:
          requests.append(
              (compute_client.apitools_client.regionOperations, 'List',
               compute_client.apitools_client.regionOperations.GetRequestType(
                   'List')(
                       filter=request_data.filter,
                       maxResults=request_data.max_results,
                       region=region_name,
                       project=list(request_data.scope_set)[0].project)))
      if args.zones is not None:
        args_zone_names = [
            compute_holder.resources.Parse(  # pylint:disable=g-complex-comprehension
                zone,
                params={
                    'project': properties.VALUES.core.project.GetOrFail,
                },
                collection='compute.zones').Name()
            for zone in args.zones or []]
        # If no zones were provided by the user, fetch a list.
        errors = []
        zone_names = (
            args_zone_names or [res.name for res in lister.GetGlobalResources(  # pylint:disable=g-complex-comprehension
                service=compute_client.apitools_client.zones,
                project=properties.VALUES.core.project.GetOrFail(),
                filter_expr=None,
                http=compute_client.apitools_client.http,
                batch_url=compute_client.batch_url,
                errors=errors)])
        if errors:
          utils.RaiseToolException(
              errors,
              'Unable to fetch a list of zones. Specifying [--zones] may '
              'fix this issue:')
        for zone_name in zone_names:
          requests.append(
              (compute_client.apitools_client.zoneOperations, 'List',
               compute_client.apitools_client.zoneOperations.GetRequestType(
                   'List')(
                       filter=request_data.filter,
                       maxResults=request_data.max_results,
                       zone=zone_name,
                       project=list(request_data.scope_set)[0].project)))
    errors = []
    results = list(
        request_helper.ListJson(
            requests=requests,
            http=compute_client.apitools_client.http,
            batch_url=compute_client.batch_url,
            errors=errors))

    if errors:
      utils.RaiseToolException(errors)

    return results


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListBeta(List):
  """List Compute Engine operations."""

  @staticmethod
  def Args(parser):
    AddFlags(parser, False)

List.detailed_help = base_classes.GetGlobalRegionalListerHelp('operations')
ListBeta.detailed_help = {
    'brief': 'List Compute Engine operations',
    'DESCRIPTION': """
        *{command}* displays all Compute Engine operations in a
        project.

        By default, all global, regional, and zonal operations are listed. The
        results can be narrowed by providing combinations of the --zones,
        --regions, and --global flags.

        Note: *{command}* displays operations fewer than 14 days old, up to a
        maximum of 5000.
        """,
    'EXAMPLES': """
        To list all operations in a project in table form, run:

          $ {command}

        To list the URIs of all operations in a project, run:

          $ {command} --uri

        To list all operations in zones us-central1-b and
        europe-west1-d, run:

           $ {command} --zones=us-central1-b,europe-west1-d

        To list all global operations in a project, run:

           $ {command} --global

        To list all regional operations in a project, run:

           $ {command} --regions=""

        To list all operations with names prefixed with `operation`, run:

           $ {command} --filter="name:operation"

        To list all operations in the us-central1 and europe-west1
        regions and all operations in the us-central1-a zone, run:

           $ {command} --zones=us-central1-a --regions=us-central1,europe-west1

        To list all operations with a specified target, filter on the targetLink
        field (run `{command} --format=json` to see a full, well-structured list
        of available fields). Additionally, use `scope()` which extracts the
        last part of the URL to get the required target information, and run:

           $ {command} --filter="targetLink.scope():default-12345abc"
        """,
}
