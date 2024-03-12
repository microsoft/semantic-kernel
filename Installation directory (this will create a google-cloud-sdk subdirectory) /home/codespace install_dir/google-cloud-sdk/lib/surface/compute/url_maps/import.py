# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Import URL maps command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.url_maps import flags
from googlecloudsdk.command_lib.compute.url_maps import url_maps_utils
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


def _DetailedHelp():
  return {
      'brief':
          'Import a URL map.',
      'DESCRIPTION':
          """\
          Imports a URL map's configuration from a file.
          """,
      'EXAMPLES':
          """\
          A URL map can be imported by running:

            $ {command} NAME --source=<path-to-file>
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


def _SendPatchRequest(client, resources, url_map_ref, replacement):
  """Sends a URL map patch request and waits for the operation to finish.

  Args:
    client: The API client.
    resources: The resource parser.
    url_map_ref: The URL map reference.
    replacement: The URL map to patch with.

  Returns:
    The operation result.
  """
  if url_map_ref.Collection() == 'compute.regionUrlMaps':
    service = client.apitools_client.regionUrlMaps
    operation = client.apitools_client.regionUrlMaps.Patch(
        client.messages.ComputeRegionUrlMapsPatchRequest(
            project=url_map_ref.project,
            region=url_map_ref.region,
            urlMap=url_map_ref.Name(),
            urlMapResource=replacement))
  else:
    service = client.apitools_client.urlMaps
    operation = client.apitools_client.urlMaps.Patch(
        client.messages.ComputeUrlMapsPatchRequest(
            project=url_map_ref.project,
            urlMap=url_map_ref.Name(),
            urlMapResource=replacement))

  return url_maps_utils.WaitForOperation(resources, service, operation,
                                         url_map_ref, 'Updating URL map')


def _SendInsertRequest(client, resources, url_map_ref, url_map):
  """Sends a URL map insert request and waits for the operation to finish.

  Args:
    client: The API client.
    resources: The resource parser.
    url_map_ref: The URL map reference.
    url_map: The URL map to insert.

  Returns:
    The operation result.
  """
  if url_map_ref.Collection() == 'compute.regionUrlMaps':
    service = client.apitools_client.regionUrlMaps
    operation = client.apitools_client.regionUrlMaps.Insert(
        client.messages.ComputeRegionUrlMapsInsertRequest(
            project=url_map_ref.project,
            region=url_map_ref.region,
            urlMap=url_map))
  else:
    service = client.apitools_client.urlMaps
    operation = client.apitools_client.urlMaps.Insert(
        client.messages.ComputeUrlMapsInsertRequest(
            project=url_map_ref.project, urlMap=url_map))

  return url_maps_utils.WaitForOperation(resources, service, operation,
                                         url_map_ref, 'Creating URL map')


def _GetClearedFieldsForDuration(duration, field_prefix):
  """Gets a list of fields cleared by the user for Duration."""
  cleared_fields = []
  if hasattr(duration, 'seconds'):
    cleared_fields.append(field_prefix + 'seconds')
  if hasattr(duration, 'nanos'):
    cleared_fields.append(field_prefix + 'nanos')
  return cleared_fields


def _GetClearedFieldsForUrlRewrite(url_rewrite, field_prefix):
  """Gets a list of fields cleared by the user for UrlRewrite."""
  cleared_fields = []
  if not url_rewrite.pathPrefixRewrite:
    cleared_fields.append(field_prefix + 'pathPrefixRewrite')
  if not url_rewrite.hostRewrite:
    cleared_fields.append(field_prefix + 'hostRewrite')
  return cleared_fields


def _GetClearedFieldsForRetryPolicy(retry_policy, field_prefix):
  """Gets a list of fields cleared by the user for RetryPolicy."""
  cleared_fields = []
  if not retry_policy.retryConditions:
    cleared_fields.append(field_prefix + 'retryConditions')
  if hasattr(retry_policy, 'numRetries'):
    cleared_fields.append(field_prefix + 'numRetries')
  if not retry_policy.perTryTimeout:
    cleared_fields.append(field_prefix + 'perTryTimeout')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForDuration(
        retry_policy.perTryTimeout, field_prefix + 'perTryTimeout.')
  return cleared_fields


def _GetClearedFieldsForRequestMirrorPolicy(mirror_policy, field_prefix):
  """Gets a list of fields cleared by the user for RequestMirrorPolicy."""
  cleared_fields = []
  if not mirror_policy.backendService:
    cleared_fields.append(field_prefix + 'backendService')
  return cleared_fields


def _GetClearedFieldsForCorsPolicy(cors_policy, field_prefix):
  """Gets a list of fields cleared by the user for CorsPolicy."""
  cleared_fields = []
  if not cors_policy.allowOrigins:
    cleared_fields.append(field_prefix + 'allowOrigins')
  if not cors_policy.allowOriginRegexes:
    cleared_fields.append(field_prefix + 'allowOriginRegexes')
  if not cors_policy.allowMethods:
    cleared_fields.append(field_prefix + 'allowMethods')
  if not cors_policy.allowHeaders:
    cleared_fields.append(field_prefix + 'allowHeaders')
  if not cors_policy.exposeHeaders:
    cleared_fields.append(field_prefix + 'exposeHeaders')
  if not cors_policy.maxAge:
    cleared_fields.append(field_prefix + 'maxAge')
  if not cors_policy.allowCredentials:
    cleared_fields.append(field_prefix + 'allowCredentials')
  if not cors_policy.disabled:
    cleared_fields.append(field_prefix + 'disabled')
  return cleared_fields


def _GetClearedFieldsForFaultDelay(fault_delay, field_prefix):
  """Gets a list of fields cleared by the user for HttpFaultDelay."""
  cleared_fields = []
  if not fault_delay.fixedDelay:
    cleared_fields.append(field_prefix + 'fixedDelay')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForDuration(
        fault_delay.fixedDelay, field_prefix + 'fixedDelay.')
  if not fault_delay.percentage:
    cleared_fields.append(field_prefix + 'percentage')
  return cleared_fields


def _GetClearedFieldsForFaultAbort(fault_abort, field_prefix):
  """Gets a list of fields cleared by the user for HttpFaultAbort."""
  cleared_fields = []
  if not fault_abort.httpStatus:
    cleared_fields.append(field_prefix + 'httpStatus')
  if not fault_abort.percentage:
    cleared_fields.append(field_prefix + 'percentage')
  return cleared_fields


def _GetClearedFieldsForFaultInjectionPolicy(fault_injection_policy,
                                             field_prefix):
  """Gets a list of fields cleared by the user for FaultInjectionPolicy."""
  cleared_fields = []
  if not fault_injection_policy.delay:
    cleared_fields.append(field_prefix + 'delay')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForFaultDelay(
        fault_injection_policy.delay, field_prefix + 'delay.')
  if not fault_injection_policy.abort:
    cleared_fields.append(field_prefix + 'abort')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForFaultAbort(
        fault_injection_policy.abort, field_prefix + 'abort.')
  return cleared_fields


def _GetClearedFieldsForRoutAction(route_action, field_prefix):
  """Gets a list of fields cleared by the user for HttpRouteAction."""
  cleared_fields = []
  if not route_action.weightedBackendServices:
    cleared_fields.append(field_prefix + 'weightedBackendServices')
  if not route_action.urlRewrite:
    cleared_fields.append(field_prefix + 'urlRewrite')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForUrlRewrite(
        route_action.urlRewrite, field_prefix + 'urlRewrite.')
  if not route_action.timeout:
    cleared_fields.append(field_prefix + 'timeout')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForDuration(
        route_action.timeout, field_prefix + 'timeout.')
  if not route_action.retryPolicy:
    cleared_fields.append(field_prefix + 'retryPolicy')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForRetryPolicy(
        route_action.retryPolicy, field_prefix + 'retryPolicy.')
  if not route_action.requestMirrorPolicy:
    cleared_fields.append(field_prefix + 'requestMirrorPolicy')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForRequestMirrorPolicy(
        route_action.requestMirrorPolicy, field_prefix + 'requestMirrorPolicy.')
  if not route_action.corsPolicy:
    cleared_fields.append(field_prefix + 'corsPolicy')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForCorsPolicy(
        route_action.corsPolicy, field_prefix + 'corsPolicy.')
  if not route_action.faultInjectionPolicy:
    cleared_fields.append(field_prefix + 'faultInjectionPolicy')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForFaultInjectionPolicy(
        route_action.faultInjectionPolicy,
        field_prefix + 'faultInjectionPolicy.')
  return cleared_fields


def _GetClearedFieldsForUrlRedirect(url_redirect, field_prefix):
  """Gets a list of fields cleared by the user for UrlRedirect."""
  cleared_fields = []
  if not url_redirect.hostRedirect:
    cleared_fields.append(field_prefix + 'hostRedirect')
  if not url_redirect.pathRedirect:
    cleared_fields.append(field_prefix + 'pathRedirect')
  if not url_redirect.prefixRedirect:
    cleared_fields.append(field_prefix + 'prefixRedirect')
  if not url_redirect.redirectResponseCode:
    cleared_fields.append(field_prefix + 'redirectResponseCode')
  if not url_redirect.httpsRedirect:
    cleared_fields.append(field_prefix + 'httpsRedirect')
  if not url_redirect.stripQuery:
    cleared_fields.append(field_prefix + 'stripQuery')
  return cleared_fields


def _GetClearedFieldsForHeaderAction(header_action, field_prefix):
  """Gets a list of fields cleared by the user for HeaderAction."""
  cleared_fields = []
  if not header_action.requestHeadersToRemove:
    cleared_fields.append(field_prefix + 'requestHeadersToRemove')
  if not header_action.requestHeadersToAdd:
    cleared_fields.append(field_prefix + 'requestHeadersToAdd')
  if not header_action.responseHeadersToRemove:
    cleared_fields.append(field_prefix + 'responseHeadersToRemove')
  if not header_action.responseHeadersToAdd:
    cleared_fields.append(field_prefix + 'responseHeadersToAdd')
  return cleared_fields


def _Run(args, holder, url_map_arg, release_track):
  """Issues requests necessary to import URL maps."""
  client = holder.client
  resources = holder.resources

  url_map_ref = url_map_arg.ResolveAsResource(
      args,
      resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

  try:
    url_map = export_util.Import(
        message_type=client.messages.UrlMap,
        stream=data,
        schema_path=_GetSchemaPath(release_track))
  except yaml_validator.ValidationError as e:
    raise compute_exceptions.ValidationError(str(e))

  if url_map.name != url_map_ref.Name():
    # Replace warning and raise error after 10/01/2021
    log.warning('The name of the Url Map must match the value of the ' +
                '\'name\' attribute in the YAML file. Future versions of ' +
                'gcloud will fail with an error.')
  # Get existing URL map.
  try:
    url_map_old = url_maps_utils.SendGetRequest(client, url_map_ref)
  except apitools_exceptions.HttpError as error:
    if error.status_code != 404:
      raise error
    # Url Map does not exist, create a new one.
    return _SendInsertRequest(client, resources, url_map_ref, url_map)

  # No change, do not send requests to server.
  if url_map_old == url_map:
    return

  console_io.PromptContinue(
      message=('Url Map [{0}] will be overwritten.').format(url_map_ref.Name()),
      cancel_on_no=True)

  # Populate id and fingerprint fields when YAML files don't contain them.
  if not url_map.id:
    url_map.id = url_map_old.id
  if url_map.fingerprint:
    # Replace warning and raise error after 10/01/2021
    log.warning('An up-to-date fingerprint must be provided to ' +
                'update the Url Map. Future versions of gcloud will fail ' +
                'with an error \'412 conditionNotMet\'')
    url_map.fingerprint = url_map_old.fingerprint
  # Unspecified fields are assumed to be cleared.
  # TODO(b/182287403) Replace with proto reflection and update scenario tests.
  cleared_fields = []
  if not url_map.description:
    cleared_fields.append('description')
  if not url_map.hostRules:
    cleared_fields.append('hostRules')
  if not url_map.pathMatchers:
    cleared_fields.append('pathMatchers')
  if not url_map.tests:
    cleared_fields.append('tests')
  if not url_map.defaultService:
    cleared_fields.append('defaultService')
  if not url_map.defaultRouteAction:
    cleared_fields.append('defaultRouteAction')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForRoutAction(
        url_map.defaultRouteAction, 'defaultRouteAction.')
  if not url_map.defaultUrlRedirect:
    cleared_fields.append('defaultUrlRedirect')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForUrlRedirect(
        url_map.defaultUrlRedirect, 'defaultUrlRedirect.')
  if not url_map.headerAction:
    cleared_fields.append('headerAction')
  else:
    cleared_fields = cleared_fields + _GetClearedFieldsForHeaderAction(
        url_map.headerAction, 'headerAction.')

  with client.apitools_client.IncludeFields(cleared_fields):
    return _SendPatchRequest(client, resources, url_map_ref, url_map)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import a URL map."""

  detailed_help = _DetailedHelp()
  URL_MAP_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.URL_MAP_ARG = flags.UrlMapArgument()
    cls.URL_MAP_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(
        parser, _GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.URL_MAP_ARG, self.ReleaseTrack())
