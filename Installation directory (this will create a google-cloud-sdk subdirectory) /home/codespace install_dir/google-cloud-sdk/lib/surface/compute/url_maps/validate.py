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
"""Validate URL maps command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


def _DetailedHelp():
  return {
      'brief':
          'Validate a URL map.',
      'DESCRIPTION':
          """\
        Runs static validation for the UrlMap.
        In particular, the tests of the provided UrlMap will be run.
        Calling this method does NOT create or update the UrlMap.
        """,
      'EXAMPLES':
          """\
        A URL map can be validated by running:

          $ {command} --source=<path-to-file>
        """
  }


def _GetApiVersion(release_track):
  """Returns the API version based on the release track."""
  if release_track == base.ReleaseTrack.ALPHA:
    return 'alpha'
  elif release_track == base.ReleaseTrack.BETA:
    return 'beta'
  return 'v1'


def _GetSchemaPath(release_track, for_help=False):
  """Returns the resource schema path."""
  return export_util.GetSchemaPath(
      'compute', _GetApiVersion(release_track), 'UrlMap', for_help=for_help)


def _AddSourceFlag(parser, schema_path=None):
  help_text = """Path to a YAML file containing configuration export data.
        The YAML file must not contain any output-only fields. Alternatively,
        you may omit this flag to read from standard input. For a schema
        describing the export/import format, see: {}.
      """.format(schema_path)
  parser.add_argument(
      '--source', help=textwrap.dedent(help_text), required=False)


def _AddGlobalFlag(parser):
  parser.add_argument(
      '--global', action='store_true', help='If set, the URL map is global.')


def _AddRegionFlag(parser):
  parser.add_argument('--region', help='Region of the URL map to validate.')


def _AddScopeFlags(parser):
  scope = parser.add_mutually_exclusive_group()
  _AddGlobalFlag(scope)
  _AddRegionFlag(scope)


def _AddLoadBalancingSchemeFlag(parser):
  """Add --load-balancing-scheme flag."""
  help_text = """\
  Specifies the load balancer type this validation request is for. Use
  `EXTERNAL_MANAGED` for global external Application Load Balancer. Use
  `EXTERNAL` for classic Application Load Balancer.

  Other load balancer types are not supported. For more information, refer to
  [Choosing a load balancer](https://cloud.google.com/load-balancing/docs/choosing-load-balancer/).

  If unspecified, the load balancing scheme will be inferred from the backend
  service resources this URL map references. If that can not be inferred (for
  example, this URL map only references backend buckets, or this URL map is
  for rewrites and redirects only and doesn't reference any backends),
  `EXTERNAL` will be used as the default type.

  If specified, the scheme must not conflict with the load balancing
  scheme of the backend service resources this URL map references.
  """
  parser.add_argument(
      '--load-balancing-scheme',
      choices=['EXTERNAL', 'EXTERNAL_MANAGED'],
      help=help_text,
      required=False)


def _MakeGlobalRequest(client, project, url_map, load_balancing_scheme):
  """Construct (not send) and return the request for global UrlMap."""
  if load_balancing_scheme is None:
    return client.messages.ComputeUrlMapsValidateRequest(
        project=project,
        urlMap=url_map.name,
        urlMapsValidateRequest=client.messages.UrlMapsValidateRequest(
            resource=url_map))
  else:
    scheme_enum = client.messages.UrlMapsValidateRequest.LoadBalancingSchemesValueListEntryValuesEnum(
        load_balancing_scheme)
    return client.messages.ComputeUrlMapsValidateRequest(
        project=project,
        urlMap=url_map.name,
        urlMapsValidateRequest=client.messages.UrlMapsValidateRequest(
            resource=url_map, loadBalancingSchemes=[scheme_enum]))


def _MakeRegionalRequest(client, project, region, url_map):
  return client.messages.ComputeRegionUrlMapsValidateRequest(
      project=project,
      region=region,
      urlMap=url_map.name,
      regionUrlMapsValidateRequest=client.messages.RegionUrlMapsValidateRequest(
          resource=url_map))


def _SendGlobalRequest(client, project, url_map, load_balancing_scheme):
  return client.apitools_client.urlMaps.Validate(
      _MakeGlobalRequest(client, project, url_map, load_balancing_scheme))


def _SendRegionalRequest(client, project, region, url_map):
  return client.apitools_client.regionUrlMaps.Validate(
      _MakeRegionalRequest(client, project, region, url_map))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Validate(base.Command):
  """Validates URL map configs from your project."""

  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    _AddSourceFlag(parser, _GetSchemaPath(cls.ReleaseTrack(), for_help=True))
    _AddScopeFlags(parser)
    _AddLoadBalancingSchemeFlag(parser)

  def Run(self, args):
    """Runs the command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      A response object returned by rpc call Validate.
    """
    project = properties.VALUES.core.project.GetOrFail()
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    if args.region is not None and args.load_balancing_scheme:
      raise exceptions.InvalidArgumentException(
          '--load-balancing-scheme',
          'Cannot specify load balancing scheme for regional URL maps.')

    # Import UrlMap to be verified
    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)
    try:
      url_map = export_util.Import(
          message_type=client.messages.UrlMap,
          stream=data,
          schema_path=_GetSchemaPath(self.ReleaseTrack()))
    except yaml_validator.ValidationError as e:
      raise compute_exceptions.ValidationError(str(e))

    # Send UrlMap.validate request
    if args.region is not None:
      return _SendRegionalRequest(client, project, args.region, url_map)
    return _SendGlobalRequest(client, project, url_map,
                              args.load_balancing_scheme)
