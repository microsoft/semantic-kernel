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
"""Facilities for getting a list of Cloud resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.compute import filter_scope_rewriter
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.resource import resource_projector
import six


def _ConvertProtobufsToDicts(resources):
  for resource in resources:
    if resource is None:
      continue

    yield resource_projector.MakeSerializable(resource)


def ProcessResults(resources, field_selector, sort_key_fn=None,
                   reverse_sort=False, limit=None):
  """Process the results from the list query.

  Args:
    resources: The list of returned resources.
    field_selector: Select the primary key for sorting.
    sort_key_fn: Sort the key using this comparison function.
    reverse_sort: Sort the resources in reverse order.
    limit: Limit the number of resourses returned.
  Yields:
    The resource.
  """
  resources = _ConvertProtobufsToDicts(resources)
  if sort_key_fn:
    resources = sorted(resources, key=sort_key_fn, reverse=reverse_sort)

  if limit:
    resources = itertools.islice(resources, limit)
  for resource in resources:
    if field_selector:
      yield field_selector.Apply(resource)
    else:
      yield resource


def FormatListRequests(service, project, scopes, scope_name,
                       filter_expr):
  """Helper for generating list requests."""
  requests = []

  if scopes:
    for scope in scopes:
      request = service.GetRequestType('List')(
          filter=filter_expr,
          project=project,
          maxResults=constants.MAX_RESULTS_PER_PAGE)
      setattr(request, scope_name, scope)
      requests.append((service, 'List', request))

  elif not scope_name:
    requests.append((
        service,
        'List',
        service.GetRequestType('List')(
            filter=filter_expr,
            project=project,
            maxResults=constants.MAX_RESULTS_PER_PAGE)))

  else:
    requests.append((
        service,
        'AggregatedList',
        service.GetRequestType('AggregatedList')(
            filter=filter_expr,
            project=project,
            maxResults=constants.MAX_RESULTS_PER_PAGE)))

  return requests


def _GetResources(service, project, scopes, scope_name,
                  filter_expr, http, batch_url, errors, make_requests):
  """Helper for the Get{Zonal,Regional,Global}Resources functions."""
  requests = FormatListRequests(service, project, scopes, scope_name,
                                filter_expr)

  return make_requests(
      requests=requests,
      http=http,
      batch_url=batch_url,
      errors=errors)


def GetZonalResources(service, project, requested_zones,
                      filter_expr, http, batch_url, errors):
  """Lists resources that are scoped by zone.

  Args:
    service: An apitools service object.
    project: The Compute Engine project name for which listing should be
      performed.
    requested_zones: A list of zone names that can be used to control
      the scope of the list call.
    filter_expr: A filter to pass to the list API calls.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A generator that yields JSON-serializable dicts representing the results.
  """
  return _GetResources(
      service=service,
      project=project,
      scopes=requested_zones,
      scope_name='zone',
      filter_expr=filter_expr,
      http=http,
      batch_url=batch_url,
      errors=errors,
      make_requests=request_helper.MakeRequests)


def GetZonalResourcesDicts(service, project, requested_zones, filter_expr, http,
                           batch_url, errors):
  """Lists resources that are scoped by zone and returns them as dicts.

  It has the same functionality as GetZonalResouces but skips translating
  JSON to messages saving lot of CPU cycles.

  Args:
    service: An apitools service object.
    project: The Compute Engine project name for which listing should be
      performed.
    requested_zones: A list of zone names that can be used to control
      the scope of the list call.
    filter_expr: A filter to pass to the list API calls.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A list of dicts representing the results.
  """
  return _GetResources(
      service=service,
      project=project,
      scopes=requested_zones,
      scope_name='zone',
      filter_expr=filter_expr,
      http=http,
      batch_url=batch_url,
      errors=errors,
      make_requests=request_helper.ListJson)


def GetRegionalResources(service, project, requested_regions,
                         filter_expr, http, batch_url, errors):
  """Lists resources that are scoped by region.

  Args:
    service: An apitools service object.
    project: The Compute Engine project name for which listing should be
      performed.
    requested_regions: A list of region names that can be used to
      control the scope of the list call.
    filter_expr: A filter to pass to the list API calls.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A generator that yields JSON-serializable dicts representing the results.
  """
  return _GetResources(
      service=service,
      project=project,
      scopes=requested_regions,
      scope_name='region',
      filter_expr=filter_expr,
      http=http,
      batch_url=batch_url,
      errors=errors,
      make_requests=request_helper.MakeRequests)


def GetRegionalResourcesDicts(service, project, requested_regions, filter_expr,
                              http, batch_url, errors):
  """Lists resources that are scoped by region and returns them as dicts.

  Args:
    service: An apitools service object.
    project: The Compute Engine project name for which listing should be
      performed.
    requested_regions: A list of region names that can be used to
      control the scope of the list call.
    filter_expr: A filter to pass to the list API calls.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A list of dicts representing the results.
  """
  return _GetResources(
      service=service,
      project=project,
      scopes=requested_regions,
      scope_name='region',
      filter_expr=filter_expr,
      http=http,
      batch_url=batch_url,
      errors=errors,
      make_requests=request_helper.ListJson)


def GetGlobalResources(service, project, filter_expr, http,
                       batch_url, errors):
  """Lists resources in the global scope.

  Args:
    service: An apitools service object.
    project: The Compute Engine project name for which listing should be
      performed.
    filter_expr: A filter to pass to the list API calls.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A generator that yields JSON-serializable dicts representing the results.
  """
  return _GetResources(
      service=service,
      project=project,
      scopes=None,
      scope_name=None,
      filter_expr=filter_expr,
      http=http,
      batch_url=batch_url,
      errors=errors,
      make_requests=request_helper.MakeRequests)


def GetGlobalResourcesDicts(service, project, filter_expr, http, batch_url,
                            errors):
  """Lists resources in the global scope and returns them as dicts.

  Args:
    service: An apitools service object.
    project: The Compute Engine project name for which listing should be
      performed.
    filter_expr: A filter to pass to the list API calls.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors.

  Returns:
    A list of dicts representing the results.
  """
  return _GetResources(
      service=service,
      project=project,
      scopes=None,
      scope_name=None,
      filter_expr=filter_expr,
      http=http,
      batch_url=batch_url,
      errors=errors,
      make_requests=request_helper.ListJson)


def _GroupByProject(locations):
  """Group locations by project field."""
  result = {}
  for location in locations or []:
    if location.project not in result:
      result[location.project] = []
    result[location.project].append(location)
  return result


# This is designed as separate global function to simplify mocking in test lib.
def Invoke(frontend, implementation):
  """Applies implementation on frontend."""
  return implementation(frontend)


def ComposeSyncImplementation(generator, executor):

  def Implementation(frontend):
    return executor(generator(frontend), frontend)

  return Implementation


class GlobalScope(set):
  pass


class ZoneSet(set):
  pass


class RegionSet(set):
  pass


class AllScopes(object):
  """Holds information about wildcard use of list command."""

  def __init__(self, projects, zonal, regional):
    self.projects = projects
    self.zonal = zonal
    self.regional = regional

  def __eq__(self, other):
    if not isinstance(other, AllScopes):
      return False  # AllScopes is not suited for inheritance
    return (self.projects == other.projects and self.zonal == other.zonal and
            self.regional == other.regional)

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash(self.projects) ^ hash(self.zonal) ^ hash(self.regional)

  def __repr__(self):
    return 'AllScopes(projects={}, zonal={}, regional={})'.format(
        repr(self.projects), repr(self.zonal), repr(self.regional))


class ListException(exceptions.Error):
  """Base exception for lister exceptions."""


# TODO(b/38256601) - Drop these flags
def AddBaseListerArgs(parser, hidden=False):
  """Add arguments defined by base_classes.BaseLister."""
  parser.add_argument(
      'names',
      action=actions.DeprecationAction(
          'names',
          show_message=bool,
          warn='Argument `NAME` is deprecated. '
          'Use `--filter="name=( \'NAME\' ... )"` instead.'),
      metavar='NAME',
      nargs='*',
      default=[],
      completer=compute_completers.InstancesCompleter,
      hidden=hidden,
      help=('If provided, show details for the specified names and/or URIs of '
            'resources.'))

  parser.add_argument(
      '--regexp',
      '-r',
      hidden=hidden,
      action=actions.DeprecationAction(
          'regexp',
          warn='Flag `--regexp` is deprecated. '
          'Use `--filter="name~\'REGEXP\'"` instead.'),
      help="""\
        Regular expression to filter the names of the results  on. Any names
        that do not match the entire regular expression will be filtered out.\
        """)


def AddZonalListerArgs(parser, hidden=False):
  """Add arguments defined by base_classes.ZonalLister."""
  AddBaseListerArgs(parser, hidden)
  parser.add_argument(
      '--zones',
      metavar='ZONE',
      help='If provided, only resources from the given zones are queried.',
      hidden=hidden,
      type=arg_parsers.ArgList(min_length=1),
      completer=compute_completers.ZonesCompleter,
      default=[])


def AddRegionsArg(parser, hidden=False):
  """Add arguments used by regional list command.

  These arguments are added by this function:
  - names
  - --regexp
  - --regions

  Args:
    parser: argparse.Parser, The parser that this function will add arguments to
    hidden: bool, If the flags should be hidden.
  """
  AddBaseListerArgs(parser, hidden=hidden)
  parser.add_argument(
      '--regions',
      metavar='REGION',
      hidden=hidden,
      help='If provided, only resources from the given regions are queried.',
      type=arg_parsers.ArgList(min_length=1),
      default=[])


def AddMultiScopeListerFlags(parser, zonal=False, regional=False,
                             global_=False):
  """Adds name, --regexp and scope flags as necessary."""
  AddBaseListerArgs(parser)

  scope = parser.add_mutually_exclusive_group()
  if zonal:
    scope.add_argument(
        '--zones',
        metavar='ZONE',
        help=('If provided, only zonal resources are shown. '
              'If arguments are provided, only resources from the given '
              'zones are shown.'),
        type=arg_parsers.ArgList())
  if regional:
    scope.add_argument(
        '--regions',
        metavar='REGION',
        help=('If provided, only regional resources are shown. '
              'If arguments are provided, only resources from the given '
              'regions are shown.'),
        type=arg_parsers.ArgList())
  if global_:
    scope.add_argument(
        '--global',
        action='store_true',
        help='If provided, only global resources are shown.',
        default=False)


class _Frontend(object):
  """Example of conforming Frontend implementation."""

  def __init__(self, filter_expr=None, maxResults=None, scopeSet=None):
    self._filter_expr = filter_expr
    self._max_results = maxResults
    self._scope_set = scopeSet

  @property
  def filter(self):
    return self._filter_expr

  @property
  def max_results(self):
    return self._max_results

  @property
  def scope_set(self):
    return self._scope_set


def _GetListCommandFrontendPrototype(args, message=None):
  """Make Frontend suitable for ListCommand argument namespace.

  Generated filter is a pair (client-side filter, server-side filter).

  Args:
    args: The argument namespace of ListCommand.
    message: The response resource proto message for the request.

  Returns:
    Frontend initialized with information from ListCommand argument namespace.
    Both client-side and server-side filter is returned.
  """
  filter_expr = flags.RewriteFilter(args, message=message)
  max_results = int(args.page_size) if args.page_size else None
  local_filter, _ = filter_expr
  if args.limit and (max_results is None or max_results > args.limit):
    max_results = args.limit
  if not local_filter:
    # If we are not applying a client-side filter, don't limit batch size.
    max_results = None
  return _Frontend(filter_expr=filter_expr, maxResults=max_results)


def _GetBaseListerFrontendPrototype(args, message=None):
  """Make Frontend suitable for BaseLister argument namespace.

  Generated client-side filter is stored to args.filter. Generated server-side
  filter is None. Client-side filter should be processed using
  flags.RewriteFilter before use to take advantage of possible server-side
  filtering.

  Args:
    args: The argument namespace of BaseLister.
    message: The resource proto message.

  Returns:
    Frontend initialized with information from BaseLister argument namespace.
    Server-side filter is None.
  """
  frontend = _GetListCommandFrontendPrototype(args, message=message)
  filter_args = []
  default = args.filter  # must preserve '' and None for default processing
  if args.filter:
    filter_args.append('('+args.filter+')')
  if getattr(args, 'regexp', None):
    filter_args.append(
        '(name ~ "^{}$")'.format(resource_expr_rewrite.BackendBase()
                                 .Quote(args.regexp)))
  if getattr(args, 'names', None):
    name_regexp = ' '.join([
        resource_expr_rewrite.BackendBase().Quote(name) for name in args.names
        if not name.startswith('https://')
    ])
    selflink_regexp = ' '.join([
        resource_expr_rewrite.BackendBase().Quote(name) for name in args.names
        if name.startswith('https://')
    ])
    if not selflink_regexp:
      filter_args.append('(name =({}))'.format(name_regexp))
    elif not name_regexp:
      filter_args.append('(selfLink =({}))'.format(selflink_regexp))
    else:
      filter_args.append('((name =({})) OR (selfLink =({})))'.format(
          name_regexp, selflink_regexp))
  # Refine args.filter specification to reuse gcloud filtering logic
  # for filtering based on instance names
  args.filter = ' AND '.join(filter_args) or default

  return _Frontend(None, frontend.max_results, frontend.scope_set)


def _TranslateZonesFlag(args, resources, message=None):
  """Translates --zones flag into filter expression and scope set."""
  default = args.filter  # must preserve '' and None for default processing
  scope_set = ZoneSet([
      resources.Parse(  # pylint: disable=g-complex-comprehension
          z,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='compute.zones') for z in args.zones
  ])
  # Refine args.filter specification to reuse gcloud filtering logic
  # for filtering based on zones
  filter_arg = '({}) AND '.format(args.filter) if args.filter else ''
  # How to escape '*' in zone and what are special characters for
  # simple pattern?
  zone_regexp = ' '.join([zone for zone in args.zones])
  zone_arg = '(zone :({}))'.format(zone_regexp)
  args.filter = (filter_arg + zone_arg) or default
  args.filter, filter_expr = flags.RewriteFilter(args, message=message)
  return filter_expr, scope_set


def _TranslateZonesFilters(args, resources):
  """Translates simple zone=( ...

  ) filters into scope set.

  Args:
    args: The argument namespace of BaseLister.
    resources: resources.Registry, The resource registry

  Returns:
    A scope set for the request.
  """
  _, zones = filter_scope_rewriter.FilterScopeRewriter().Rewrite(
      args.filter, keys={'zone'})
  if zones:
    zone_list = []
    for z in zones:
      zone_resource = resources.Parse(
          z,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='compute.zones')
      zone_list.append(zone_resource)
    return ZoneSet(zone_list)
  return AllScopes([
      resources.Parse(
          properties.VALUES.core.project.GetOrFail(),
          collection='compute.projects')
  ],
                   zonal=True,
                   regional=False)


def ParseZonalFlags(args, resources, message=None):
  """Make Frontend suitable for ZonalLister argument namespace.

  Generated client-side filter is stored to args.filter.

  Args:
    args: The argument namespace of BaseLister.
    resources: resources.Registry, The resource registry
    message: The response resource proto message for the request.

  Returns:
    Frontend initialized with information from BaseLister argument namespace.
    Server-side filter is None.
  """
  frontend = _GetBaseListerFrontendPrototype(args, message=message)
  filter_expr = frontend.filter
  if args.zones:
    filter_expr, scope_set = _TranslateZonesFlag(
        args, resources, message=message)
  elif args.filter and 'zone' in args.filter:
    scope_set = _TranslateZonesFilters(args, resources)
  else:
    scope_set = AllScopes(
        [
            resources.Parse(
                properties.VALUES.core.project.GetOrFail(),
                collection='compute.projects')
        ],
        zonal=True,
        regional=False)
  return _Frontend(filter_expr, frontend.max_results, scope_set)


def _TranslateRegionsFlag(args, resources, message=None):
  """Translates --regions flag into filter expression and scope set."""
  default = args.filter  # must preserve '' and None for default processing
  scope_set = RegionSet([
      resources.Parse(  # pylint: disable=g-complex-comprehension
          region,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='compute.regions') for region in args.regions
  ])
  # Refine args.filter specification to reuse gcloud filtering logic
  # for filtering based on regions
  filter_arg = '({}) AND '.format(args.filter) if args.filter else ''
  # How to escape '*' in region and what are special characters for
  # simple pattern?
  region_regexp = ' '.join([region for region in args.regions])
  region_arg = '(region :({}))'.format(region_regexp)
  args.filter = (filter_arg + region_arg) or default
  args.filter, filter_expr = flags.RewriteFilter(args, message=message)
  return filter_expr, scope_set


def _TranslateRegionsFilters(args, resources):
  """Translates simple region=( ...

  ) filters into scope set.

  Args:
    args: The argument namespace of BaseLister.
    resources: resources.Registry, The resource registry

  Returns:
    A region set for the request.
  """
  _, regions = filter_scope_rewriter.FilterScopeRewriter().Rewrite(
      args.filter, keys={'region'})
  if regions:
    region_list = []
    for r in regions:
      region_resource = resources.Parse(
          r,
          params={'project': properties.VALUES.core.project.GetOrFail},
          collection='compute.regions')
      region_list.append(region_resource)
    return RegionSet(region_list)
  return AllScopes([
      resources.Parse(
          properties.VALUES.core.project.GetOrFail(),
          collection='compute.projects')
  ],
                   zonal=False,
                   regional=True)


def ParseRegionalFlags(args, resources, message=None):
  """Make Frontend suitable for RegionalLister argument namespace.

  Generated client-side filter is stored to args.filter.

  Args:
    args: The argument namespace of RegionalLister.
    resources: resources.Registry, The resource registry
    message: The response resource proto message for the request.

  Returns:
    Frontend initialized with information from RegionalLister argument
    namespace.
  """
  frontend = _GetBaseListerFrontendPrototype(args, message=message)
  filter_expr = frontend.filter
  if args.regions:
    filter_expr, scope_set = _TranslateRegionsFlag(args, resources)
  elif args.filter and 'region' in args.filter:
    scope_set = _TranslateRegionsFilters(args, resources)
  else:
    scope_set = AllScopes(
        [
            resources.Parse(
                properties.VALUES.core.project.GetOrFail(),
                collection='compute.projects')
        ],
        zonal=False,
        regional=True)
  return _Frontend(filter_expr, frontend.max_results, scope_set)


def ParseMultiScopeFlags(args, resources, message=None):
  """Make Frontend suitable for MultiScopeLister argument namespace.

  Generated client-side filter is stored to args.filter.

  Args:
    args: The argument namespace of MultiScopeLister.
    resources: resources.Registry, The resource registry
    message: The response resource proto message for the request.

  Returns:
    Frontend initialized with information from MultiScopeLister argument
    namespace.
  """
  frontend = _GetBaseListerFrontendPrototype(args, message=message)
  filter_expr = frontend.filter
  if getattr(args, 'zones', None):
    filter_expr, scope_set = _TranslateZonesFlag(
        args, resources, message=message)
  elif args.filter and 'zone' in args.filter:
    scope_set = _TranslateZonesFilters(args, resources)
  elif getattr(args, 'regions', None):
    filter_expr, scope_set = _TranslateRegionsFlag(
        args, resources, message=message)
  elif args.filter and 'region' in args.filter:
    scope_set = _TranslateRegionsFilters(args, resources)
  elif getattr(args, 'global', None):
    scope_set = GlobalScope([
        resources.Parse(
            properties.VALUES.core.project.GetOrFail(),
            collection='compute.projects')
    ])
    args.filter, filter_expr = flags.RewriteFilter(args, message=message)
  else:
    scope_set = AllScopes(
        [
            resources.Parse(
                properties.VALUES.core.project.GetOrFail(),
                collection='compute.projects')
        ],
        zonal='zones' in args,
        regional='regions' in args)
  return _Frontend(filter_expr, frontend.max_results, scope_set)


def ParseNamesAndRegexpFlags(args, resources, message=None):
  """Makes Frontend suitable for GlobalLister argument namespace.

  Stores generated client-side filter in args.filter.

  Args:
    args: The argument namespace of BaseLister.
    resources: resources.Registry, The resource registry
    message: The resource proto message.

  Returns:
    Frontend initialized with information from BaseLister argument namespace.
  """
  frontend = _GetBaseListerFrontendPrototype(args, message=message)
  scope_set = GlobalScope([
      resources.Parse(
          properties.VALUES.core.project.GetOrFail(),
          collection='compute.projects')
  ])
  args.filter, filter_expr = flags.RewriteFilter(args, message=message)
  return _Frontend(filter_expr, frontend.max_results, scope_set)


class ZonalLister(object):
  """Implementation for former base_classes.ZonalLister subclasses.

  This implementation should be used only for porting from base_classes.

  This class should not be inherited.

  Attributes:
    client: The compute client.
    service: Zonal service whose resources will be listed.
  """
  # This implementation is designed to mimic precisely behavior (side-effects)
  # of base_classes.ZonalLister

  def __init__(self, client, service):
    self.client = client
    self.service = service

  def __deepcopy__(self, memodict=None):
    return self  # ZonalLister is immutable

  def __eq__(self, other):
    if not isinstance(other, ZonalLister):
      return False  # ZonalLister is not suited for inheritance
    return self.client == other.client and self.service == other.service

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash((self.client, self.service))

  def __repr__(self):
    return 'ZonalLister({}, {})'.format(repr(self.client), repr(self.service))

  def __call__(self, frontend):
    errors = []
    scope_set = frontend.scope_set
    filter_expr = frontend.filter
    if isinstance(scope_set, ZoneSet):
      for project, zones in six.iteritems(
          _GroupByProject(sorted(list(scope_set)))):
        for item in GetZonalResourcesDicts(
            service=self.service,
            project=project,
            requested_zones=[zone_ref.zone for zone_ref in zones],
            filter_expr=filter_expr,
            http=self.client.apitools_client.http,
            batch_url=self.client.batch_url,
            errors=errors):
          yield item
    else:
      # scopeSet is AllScopes
      # generate AggregatedList
      for project_ref in sorted(list(scope_set.projects)):
        for item in GetZonalResourcesDicts(
            service=self.service,
            project=project_ref.project,
            requested_zones=[],
            filter_expr=filter_expr,
            http=self.client.apitools_client.http,
            batch_url=self.client.batch_url,
            errors=errors):
          yield item
    if errors:
      utils.RaiseException(errors, ListException)


class RegionalLister(object):
  """Implementation replacing base_classes.RegionalLister base class.

  This implementation should be used only for porting from base_classes.

  Attributes:
    client: base_api.BaseApiClient, The compute client.
    service: base_api.BaseApiService, Regional service whose resources will be
    listed.
  """
  # This implementation is designed to mimic precisely behavior (side-effects)
  # of base_classes.RegionalLister

  def __init__(self, client, service):
    self.client = client
    self.service = service

  def __deepcopy__(self, memodict=None):
    return self  # RegionalLister is immutable

  def __eq__(self, other):
    # RegionalLister is not suited for inheritance
    return (isinstance(other, RegionalLister) and
            self.client == other.client and self.service == other.service)

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash((self.client, self.service))

  def __repr__(self):
    return 'RegionalLister({}, {})'.format(
        repr(self.client), repr(self.service))

  def __call__(self, frontend):
    errors = []
    scope_set = frontend.scope_set
    filter_expr = frontend.filter
    if isinstance(scope_set, RegionSet):
      for project, regions in six.iteritems(
          _GroupByProject(sorted(list(scope_set)))):
        for item in GetRegionalResourcesDicts(
            service=self.service,
            project=project,
            requested_regions=[region_ref.region for region_ref in regions],
            filter_expr=filter_expr,
            http=self.client.apitools_client.http,
            batch_url=self.client.batch_url,
            errors=errors):
          yield item
    else:
      # scopeSet is AllScopes
      # generate AggregatedList
      for project_ref in sorted(list(scope_set.projects)):
        for item in GetRegionalResourcesDicts(
            service=self.service,
            project=project_ref.project,
            requested_regions=[],
            filter_expr=filter_expr,
            http=self.client.apitools_client.http,
            batch_url=self.client.batch_url,
            errors=errors):
          yield item
    if errors:
      utils.RaiseException(errors, ListException)


class GlobalLister(object):
  """Implementation for former base_classes.GlobalLister subclasses.

  This implementation should be used only for porting from base_classes.

  Attributes:
    client: The compute client.
    service: Global service whose resources will be listed.
  """
  # This implementation is designed to mimic precisely behavior (side-effects)
  # of base_classes.GlobalLister

  def __init__(self, client, service):
    self.client = client
    self.service = service

  def __deepcopy__(self, memodict=None):
    return self  # GlobalLister is immutable

  def __eq__(self, other):
    if not isinstance(other, GlobalLister):
      return False  # GlobalLister is not suited for inheritance
    return self.client == other.client and self.service == other.service

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash((self.client, self.service))

  def __repr__(self):
    return 'GlobalLister({}, {})'.format(repr(self.client), repr(self.service))

  def __call__(self, frontend):
    errors = []
    scope_set = frontend.scope_set
    filter_expr = frontend.filter
    for project_ref in sorted(list(scope_set)):
      for item in GetGlobalResourcesDicts(
          service=self.service,
          project=project_ref.project,
          filter_expr=filter_expr,
          http=self.client.apitools_client.http,
          batch_url=self.client.batch_url,
          errors=errors):
        yield item
    if errors:
      utils.RaiseException(errors, ListException)


class MultiScopeLister(object):
  """General purpose lister implementation.

  This class can be used as a default to get lister implementation for
  `lister.Invoke()` function.

  Uses AggregatedList (if present) to dispatch AllScopes scope set.

  Example implementation of list command for zonal/regional resources:
  class List(base.ListCommand):

    def Run(self, args):
      holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
      client = holder.client

      request_data = lister.ParseMultiScopeFlags(args, holder.resources)

      list_implementation = lister.MultiScopeLister(
          client,
          zonal_service=client.apitools_client.instanceGroups,
          regional_service=client.apitools_client.regionInstanceGroups,
          aggregation_service=client.apitools_client.instanceGroups)

      return lister.Invoke(request_data, list_implementation)

  Attributes:
    client: base_api.BaseApiClient, The compute client.
    zonal_service: base_api.BaseApiService, Zonal service whose resources will
      be listed using List call.
    regional_service: base_api.BaseApiService, Regional service whose resources
      will be listed using List call.
    global_service: base_api.BaseApiService, Global service whose resources will
      be listed using List call.
    aggregation_service: base_api.BaseApiService, Aggregation service whose
      resources will be listed using AggregatedList call.
    allow_partial_server_failure: Allows Lister to continue presenting items
      from scopes that return succesfully while logging failures as a warning.
    return_partial_success: Allows Lister to pass returnPartialSuccess to
      aggregatedList requests to prevent single scope failures from failng the
      entire operation.
    image_zone_flag: Returns the images rolled out to the specific zone. This is
      used for images.list API
    instance_view_flag: control the retruned view of the instance,
      either default view or full view of instance/instanceProperities.
      this is used for instances.List/instanceTemplates.List API
  """

  def __init__(
      self,
      client,
      zonal_service=None,
      regional_service=None,
      global_service=None,
      aggregation_service=None,
      allow_partial_server_failure=True,
      return_partial_success=True,
      image_zone_flag=None,
      instance_view_flag=None,
  ):
    self.client = client
    self.zonal_service = zonal_service
    self.regional_service = regional_service
    self.global_service = global_service
    self.aggregation_service = aggregation_service
    self.allow_partial_server_failure = allow_partial_server_failure
    self.return_partial_success = return_partial_success
    self.image_zone_flag = image_zone_flag
    self.instance_view_flag = instance_view_flag

  def __deepcopy__(self, memodict=None):
    return self  # MultiScopeLister is immutable

  def __eq__(self, other):
    # MultiScopeLister is not suited for inheritance
    return (
        isinstance(other, MultiScopeLister) and self.client == other.client and
        self.zonal_service == other.zonal_service and
        self.regional_service == other.regional_service and
        self.global_service == other.global_service and
        self.aggregation_service == other.aggregation_service and
        self.allow_partial_server_failure == other.allow_partial_server_failure
        and self.return_partial_success == other.return_partial_success)

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash(
        (self.client, self.zonal_service, self.regional_service,
         self.global_service, self.aggregation_service,
         self.allow_partial_server_failure, self.return_partial_success))

  def __repr__(self):
    return 'MultiScopeLister({}, {}, {}, {}, {}, {}, {})'.format(
        repr(self.client), repr(self.zonal_service),
        repr(self.regional_service), repr(self.global_service),
        repr(self.aggregation_service), repr(self.allow_partial_server_failure),
        repr(self.return_partial_success))

  def __call__(self, frontend):
    scope_set = frontend.scope_set
    requests = []
    if isinstance(scope_set, ZoneSet):
      for project, zones in six.iteritems(
          _GroupByProject(sorted(list(scope_set)))):
        for zone_ref in zones:
          requests.append((self.zonal_service, 'List',
                           self.zonal_service.GetRequestType('List')(
                               filter=frontend.filter,
                               maxResults=frontend.max_results,
                               project=project,
                               zone=zone_ref.zone)))
    elif isinstance(scope_set, RegionSet):
      for project, regions in six.iteritems(
          _GroupByProject(sorted(list(scope_set)))):
        for region_ref in regions:
          requests.append((self.regional_service, 'List',
                           self.regional_service.GetRequestType('List')(
                               filter=frontend.filter,
                               maxResults=frontend.max_results,
                               project=project,
                               region=region_ref.region)))
    elif isinstance(scope_set, GlobalScope):
      for project_ref in sorted(list(scope_set)):
        if self.image_zone_flag is not None:
          requests.append((
              self.global_service,
              'List',
              self.global_service.GetRequestType('List')(
                  filter=frontend.filter,
                  maxResults=frontend.max_results,
                  zone=self.image_zone_flag,
                  project=project_ref.project,
              ),
          ))
        else:
          requests.append((
              self.global_service,
              'List',
              self.global_service.GetRequestType('List')(
                  filter=frontend.filter,
                  maxResults=frontend.max_results,
                  project=project_ref.project,
              ),
          ))
    else:
      # scopeSet is AllScopes
      # generate AggregatedList
      request_message = self.aggregation_service.GetRequestType(
          'AggregatedList')
      for project_ref in sorted(list(scope_set.projects)):
        input_params = {}

        if hasattr(request_message, 'includeAllScopes'):
          input_params['includeAllScopes'] = True
        if hasattr(request_message,
                   'returnPartialSuccess') and self.return_partial_success:
          input_params['returnPartialSuccess'] = True

        requests.append((self.aggregation_service, 'AggregatedList',
                         request_message(
                             filter=frontend.filter,
                             maxResults=frontend.max_results,
                             project=project_ref.project,
                             **input_params)))

    if self.instance_view_flag is not None:
      for request in requests:
        if request[1] == 'List':
          request[2].view = self.instance_view_flag
    errors = []
    response_count = 0
    for item in request_helper.ListJson(
        requests=requests,
        http=self.client.apitools_client.http,
        batch_url=self.client.batch_url,
        errors=errors):
      response_count += 1

      yield item

    if errors:
      # If the command allows partial server errors, instead of raising an
      # exception to show something went wrong, we show a warning message that
      # contains the error messages instead.
      if self.allow_partial_server_failure and response_count > 0:
        utils.WarnIfPartialRequestFail(errors)
      else:
        utils.RaiseException(errors, ListException)


class ZonalParallelLister(object):
  """List zonal resources from all zones in parallel (in one batch).

  This class can be used to list only zonal resources.

  This class should not be inherited.

  Attributes:
    client: The compute client.
    service: Zonal service whose resources will be listed.
    resources: The compute resource registry.
    allow_partial_server_failure: Allows Lister to continue presenting items
      from scopes that return succesfully while logging failures as a warning.
  """

  def __init__(self,
               client,
               service,
               resources,
               allow_partial_server_failure=True):
    self.client = client
    self.service = service
    self.resources = resources
    self.allow_partial_server_failure = allow_partial_server_failure

  def __deepcopy__(self, memodict=None):
    return self  # ZonalParallelLister is immutable

  def __eq__(self, other):
    if not isinstance(other, ZonalParallelLister):
      return False  # ZonalParallelLister is not suited for inheritance
    # Registry type should either be value type or mocked by ComputeApiMock
    # for self.resources to participate in __eq__ check here.
    return self.client == other.client and self.service == other.service

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash((self.client, self.service))

  def __repr__(self):
    return 'ZonalParallelLister({}, {}, {})'.format(
        repr(self.client), repr(self.service), repr(self.resources))

  def __call__(self, frontend):
    scope_set = frontend.scope_set
    filter_expr = frontend.filter
    if isinstance(scope_set, ZoneSet):
      # Set of zones was specified explicitly by frontend - use that setting
      zones = scope_set
    else:
      # Set of zones was not specified explicitly - fetch all of them
      # TODO(b/65008598) Use cached zone set instead of fetching it always

      zones_list_data = _Frontend(scopeSet=GlobalScope(scope_set.projects))
      zones_list_implementation = MultiScopeLister(
          self.client, global_service=self.client.apitools_client.zones)

      zones = ZoneSet([
          self.resources.Parse(z['selfLink'])
          for z in Invoke(zones_list_data, zones_list_implementation)
      ])

    service_list_data = _Frontend(
        filter_expr=filter_expr,
        maxResults=frontend.max_results,
        scopeSet=zones)
    service_list_implementation = MultiScopeLister(
        self.client,
        zonal_service=self.service,
        allow_partial_server_failure=self.allow_partial_server_failure)

    return Invoke(service_list_data, service_list_implementation)
