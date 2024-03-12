# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""`gcloud access-context-manager perimeters dry-run create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.accesscontextmanager import zones as zones_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.accesscontextmanager import perimeters
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.args import repeated


def _AddCommonArgsForDryRunCreate(parser, prefix='', version='v1'):
  """Adds arguments common to the two dry-run create modes.

  Args:
    parser: The argparse parser to add the arguments to.
    prefix: Optional prefix, e.g. 'perimeter-' to use for the argument names.
    version: Api version. e.g. v1alpha, v1beta, v1.
  """
  parser.add_argument(
      '--{}resources'.format(prefix),
      metavar='resources',
      type=arg_parsers.ArgList(),
      default=None,
      help="""Comma-separated list of resources (currently only projects, in the
              form `projects/<projectnumber>`) in this perimeter.""")
  parser.add_argument(
      '--{}restricted-services'.format(prefix),
      metavar='restricted_services',
      type=arg_parsers.ArgList(),
      default=None,
      help="""Comma-separated list of services to which the perimeter boundary
              *does* apply (for example, `storage.googleapis.com`).""")
  parser.add_argument(
      '--{}access-levels'.format(prefix),
      metavar='access_levels',
      type=arg_parsers.ArgList(),
      default=None,
      help="""Comma-separated list of IDs for access levels (in the same policy)
              that an intra-perimeter request must satisfy to be allowed.""")
  vpc_group = parser.add_argument_group()
  vpc_group.add_argument(
      '--{}enable-vpc-accessible-services'.format(prefix),
      action='store_true',
      default=None,
      help="""Whether to restrict API calls within the perimeter to those in the
              `vpc-allowed-services` list.""")
  vpc_group.add_argument(
      '--{}vpc-allowed-services'.format(prefix),
      metavar='vpc_allowed_services',
      type=arg_parsers.ArgList(),
      default=None,
      help="""Comma-separated list of APIs accessible from within the Service
              Perimeter. In order to include all restricted services, use
              reference "RESTRICTED-SERVICES". Requires vpc-accessible-services
              be enabled.""")
  parser.add_argument(
      '--{}ingress-policies'.format(prefix),
      metavar='YAML_FILE',
      type=perimeters.ParseIngressPolicies(version),
      default=None,
      help="""Path to a file containing a list of Ingress Policies.
              This file contains a list of YAML-compliant objects representing
              Ingress Policies described in the API reference.
              For more information about the alpha version, see:
              https://cloud.google.com/access-context-manager/docs/reference/rest/v1alpha/accessPolicies.servicePerimeters
              For more information about non-alpha versions, see:
              https://cloud.google.com/access-context-manager/docs/reference/rest/v1/accessPolicies.servicePerimeters"""
  )
  parser.add_argument(
      '--{}egress-policies'.format(prefix),
      metavar='YAML_FILE',
      type=perimeters.ParseEgressPolicies(version),
      default=None,
      help="""Path to a file containing a list of Egress Policies.
              This file contains a list of YAML-compliant objects representing
              Egress Policies described in the API reference.
              For more information about the alpha version, see:
              https://cloud.google.com/access-context-manager/docs/reference/rest/v1alpha/accessPolicies.servicePerimeters
              For more information about non-alpha versions, see:
              https://cloud.google.com/access-context-manager/docs/reference/rest/v1/accessPolicies.servicePerimeters"""
  )


def _ParseArgWithShortName(args, short_name):
  """Returns the argument value for given short_name or None if not specified.

  Args:
    args: The argument object obtained by parsing the command-line arguments
      using argparse.
    short_name: The regular name for the argument to be fetched, such as
      `access_levels`.
  """
  alt_name = 'perimeter_' + short_name
  if args.IsSpecified(short_name):
    return getattr(args, short_name, None)
  elif args.IsSpecified(alt_name):
    return getattr(args, alt_name, None)
  return None


def _ParseDirectionalPolicies(args):
  ingress_policies = _ParseArgWithShortName(args, 'ingress_policies')
  egress_policies = _ParseArgWithShortName(args, 'egress_policies')
  return ingress_policies, egress_policies


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class CreatePerimeterDryRun(base.UpdateCommand):
  """Creates a dry-run spec for a new or existing Service Perimeter."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    CreatePerimeterDryRun.ArgsVersioned(parser, version='v1')

  @staticmethod
  def ArgsVersioned(parser, version='v1'):
    parser.add_argument(
        '--async',
        action='store_true',
        help="""Return immediately, without waiting for the operation in
                progress to complete.""")
    perimeters.AddResourceArg(parser, 'to update')
    top_level_group = parser.add_mutually_exclusive_group(required=True)
    existing_perimeter_group = top_level_group.add_argument_group(
        'Arguments for creating dry-run spec for an **existing** Service '
        'Perimeter.')
    _AddCommonArgsForDryRunCreate(existing_perimeter_group, version=version)
    new_perimeter_group = top_level_group.add_argument_group(
        'Arguments for creating a dry-run spec for a new Service Perimeter.')
    _AddCommonArgsForDryRunCreate(
        new_perimeter_group, prefix='perimeter-', version=version)
    new_perimeter_group.add_argument(
        '--perimeter-title',
        required=True,
        default=None,
        help="""Short human-readable title for the Service Perimeter.""")
    new_perimeter_group.add_argument(
        '--perimeter-description',
        default=None,
        help="""Long-form description of Service Perimeter.""")
    new_perimeter_group.add_argument(
        '--perimeter-type',
        required=True,
        default=None,
        help="""Type of the perimeter.

            A *regular* perimeter allows resources within this service perimeter
            to import and export data amongst themselves. A project may belong
            to at most one regular service perimeter.

            A *bridge* perimeter allows resources in different regular service
            perimeters to import and export data between each other. A project
            may belong to multiple bridge service perimeters (only if it also
            belongs to a regular service perimeter). Both restricted and
            unrestricted service lists, as well as access level lists, must be
            empty.""")

  def Run(self, args):
    client = zones_api.Client(version=self._API_VERSION)
    perimeter_ref = args.CONCEPTS.perimeter.Parse()

    perimeter_type = perimeters.GetPerimeterTypeEnumForShortName(
        args.perimeter_type, self._API_VERSION)

    # Extract the arguments that reside in a ServicePerimeterConfig.
    resources = _ParseArgWithShortName(args, 'resources')
    levels = _ParseArgWithShortName(args, 'access_levels')
    levels = perimeters.ExpandLevelNamesIfNecessary(
        levels, perimeter_ref.accessPoliciesId)
    restricted_services = _ParseArgWithShortName(args, 'restricted_services')
    vpc_allowed_services = _ParseArgWithShortName(args, 'vpc_allowed_services')
    ingress_policies, egress_policies = _ParseDirectionalPolicies(args)
    if (args.enable_vpc_accessible_services is None and
        args.perimeter_enable_vpc_accessible_services is None):
      enable_vpc_accessible_services = None
    else:
      enable_vpc_accessible_services = (
          args.enable_vpc_accessible_services or
          args.perimeter_enable_vpc_accessible_services)

    result = repeated.CachedResult.FromFunc(client.Get, perimeter_ref)
    try:
      result.Get()  # Check if the perimeter was actually obtained.
    except apitools_exceptions.HttpNotFoundError:
      if args.perimeter_title is None or perimeter_type is None:
        raise exceptions.RequiredArgumentException(
            'perimeter-title',
            ('Since this Service Perimeter does not exist, perimeter-title '
             'and perimeter-type must be supplied.'))
    else:
      if args.perimeter_title is not None or perimeter_type is not None:
        raise exceptions.InvalidArgumentException('perimeter-title', (
            'A Service Perimeter with the given name already exists. The '
            'title and the type fields cannot be updated in the dry-run mode.'))
    policies.ValidateAccessPolicyArg(perimeter_ref, args)

    return client.PatchDryRunConfig(
        perimeter_ref,
        title=args.perimeter_title,
        description=args.perimeter_description,
        perimeter_type=perimeter_type,
        resources=resources,
        levels=levels,
        restricted_services=restricted_services,
        vpc_allowed_services=vpc_allowed_services,
        enable_vpc_accessible_services=enable_vpc_accessible_services,
        ingress_policies=ingress_policies,
        egress_policies=egress_policies)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreatePerimeterDryRunAlpha(CreatePerimeterDryRun):
  """Creates a dry-run spec for a new or existing Service Perimeter."""
  _API_VERSION = 'v1alpha'

  @staticmethod
  def Args(parser):
    CreatePerimeterDryRun.ArgsVersioned(parser, version='v1alpha')


detailed_help = {
    'brief':
        """Create a dry-run mode configuration for a new or existing Service
        Perimeter.""",
    'DESCRIPTION': (
        'When a Service Perimeter with the specified name does not exist, a '
        'new Service Perimeter will be created. In this case, the newly '
        'created Service Perimeter will not have any enforcement mode '
        'configuration, and, therefore, all policy violations will be '
        'logged.\n\nWhen a perimeter with the specified name does exist, a '
        'dry-run mode configuration will be created for it. The behavior of '
        'the enforcement mode configuration, if present, will not be impacted '
        'in this case. Requests that violate the existing enforcement mode '
        'configuration of the Service Perimeter will continue being denied. '
        'Requests that only violate the policy in the dry-run mode '
        'configuration will be logged but will not be denied.'),
    'EXAMPLES': (
        'To create a dry-run configuration for an existing Service '
        'Perimeter:\n\n  $ {command} my-perimeter '
        '--resources="projects/0123456789" '
        '--access-levels="accessPolicies/a_policy/accessLevels/a_level" '
        '--restricted-services="storage.googleapis.com"\n\nTo create a dry-run'
        ' configuration for a new Service Perimeter:\n\n  $ {command} '
        'my-perimeter --perimeter-title="My New Perimeter" '
        '--perimeter-description="Perimeter description" '
        '--perimeter-type="regular" '
        '--perimeter-resources="projects/0123456789" '
        '--perimeter-access-levels="accessPolicies/a_policy/accessLevels/a_level"'
        ' --perimeter-restricted-services="storage.googleapis.com"')
}

CreatePerimeterDryRunAlpha.detailed_help = detailed_help
CreatePerimeterDryRun.detailed_help = detailed_help
