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
"""Import target HTTP Proxies command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import operation_utils
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_http_proxies import flags
from googlecloudsdk.command_lib.compute.target_http_proxies import target_http_proxies_utils
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


def _DetailedHelp():
  return {
      'brief':
          'Import a target HTTP proxy.',
      'DESCRIPTION':
          """\
          Imports a target HTTP proxy's configuration from a file.
          """,
      'EXAMPLES':
          """\
          A target HTTP proxy can be imported by running:

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
      'compute',
      _GetApiVersion(release_track),
      'TargetHttpProxy',
      for_help=for_help)


def _SendInsertRequest(client, resources, target_http_proxy_ref,
                       target_http_proxy):
  """Sends Target HTTP Proxy insert request."""
  if target_http_proxies_utils.IsRegionalTargetHttpProxiesRef(
      target_http_proxy_ref):
    service = client.apitools_client.regionTargetHttpProxies
    operation = service.Insert(
        client.messages.ComputeRegionTargetHttpProxiesInsertRequest(
            project=target_http_proxy_ref.project,
            region=target_http_proxy_ref.region,
            targetHttpProxy=target_http_proxy))
  else:
    service = client.apitools_client.targetHttpProxies
    operation = service.Insert(
        client.messages.ComputeTargetHttpProxiesInsertRequest(
            project=target_http_proxy_ref.project,
            targetHttpProxy=target_http_proxy))

  return _WaitForOperation(resources, service, operation, target_http_proxy_ref,
                           'Inserting TargetHttpProxy')


def _SendPatchRequest(client, resources, target_http_proxy_ref,
                      target_http_proxy):
  """Make target HTTP proxy patch request."""
  if target_http_proxies_utils.IsRegionalTargetHttpProxiesRef(
      target_http_proxy_ref):
    console_message = ('Target HTTP Proxy [{0}] cannot be updated'.format(
        target_http_proxy_ref.Name()))
    raise NotImplementedError(console_message)

  service = client.apitools_client.targetHttpProxies
  operation = service.Patch(
      client.messages.ComputeTargetHttpProxiesPatchRequest(
          project=target_http_proxy_ref.project,
          targetHttpProxy=target_http_proxy_ref.Name(),
          targetHttpProxyResource=target_http_proxy))

  return _WaitForOperation(resources, service, operation, target_http_proxy_ref,
                           'Updating TargetHttpProxy')


def _WaitForOperation(resources, service, operation, target_http_proxy_ref,
                      message):
  """Waits for the TargetHttpProxy operation to finish."""
  if target_http_proxies_utils.IsRegionalTargetHttpProxiesRef(
      target_http_proxy_ref):
    collection = operation_utils.GetRegionalOperationsCollection()
  else:
    collection = operation_utils.GetGlobalOperationsCollection()

  return operation_utils.WaitForOperation(resources, service, operation,
                                          collection, target_http_proxy_ref,
                                          message)


def _Run(args, holder, target_http_proxy_arg, release_track):
  """Issues requests necessary to import target HTTP proxies."""
  client = holder.client
  resources = holder.resources

  target_http_proxy_ref = target_http_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

  try:
    target_http_proxy = export_util.Import(
        message_type=client.messages.TargetHttpProxy,
        stream=data,
        schema_path=_GetSchemaPath(release_track))
  except yaml_validator.ValidationError as e:
    raise compute_exceptions.ValidationError(str(e))

  # Get existing target HTTP proxy.
  try:
    target_http_proxy_old = target_http_proxies_utils.SendGetRequest(
        client, target_http_proxy_ref)
  except apitools_exceptions.HttpError as error:
    if error.status_code != 404:
      raise error
    # Target HTTP proxy does not exist, create a new one.
    return _SendInsertRequest(client, resources, target_http_proxy_ref,
                              target_http_proxy)

  if target_http_proxy_old == target_http_proxy:
    return

  console_io.PromptContinue(
      message=('Target Http Proxy [{0}] will be overwritten.').format(
          target_http_proxy_ref.Name()),
      cancel_on_no=True)

  # Populate id and fingerprint fields. These two fields are manually
  # removed from the schema files.
  target_http_proxy.id = target_http_proxy_old.id
  target_http_proxy.fingerprint = target_http_proxy_old.fingerprint

  # Unspecified fields are assumed to be cleared.
  cleared_fields = []
  if target_http_proxy.description is None:
    cleared_fields.append('description')

  # The REST API will reject requests without the UrlMap. However, we want to
  # avoid doing partial validations in the client and rely on server side
  # behavior.
  if target_http_proxy.urlMap is None:
    cleared_fields.append('urlMap')
  if release_track != base.ReleaseTrack.GA:
    if target_http_proxy.proxyBind is None:
      cleared_fields.append('proxyBind')

  with client.apitools_client.IncludeFields(cleared_fields):
    return _SendPatchRequest(client, resources, target_http_proxy_ref,
                             target_http_proxy)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import a target HTTP Proxy."""

  detailed_help = _DetailedHelp()
  TARGET_HTTP_PROXY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTP_PROXY_ARG = flags.TargetHttpProxyArgument()
    cls.TARGET_HTTP_PROXY_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(
        parser, _GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.TARGET_HTTP_PROXY_ARG, self.ReleaseTrack())
