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
"""Import target HTTPS Proxies command."""

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
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.target_https_proxies import target_https_proxies_utils
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


def _DetailedHelp():
  return {
      'brief':
          'Import a target HTTPS proxy.',
      'DESCRIPTION':
          """\
          Imports a target HTTPS proxy's configuration from a file.
          """,
      'EXAMPLES':
          """\
          A global target HTTPS proxy can be imported by running:

            $ {command} NAME --source=<path-to-file>

          A regional target HTTPS proxy can be imported by running:

            $ {command} NAME --source=<path-to-file> --region=REGION_NAME
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
      'TargetHttpsProxy',
      for_help=for_help)


def _SendInsertRequest(client, resources, target_https_proxy_ref,
                       target_https_proxy):
  """Sends Target HTTPS Proxy insert request."""
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
      target_https_proxy_ref):
    service = client.apitools_client.regionTargetHttpsProxies
    operation = service.Insert(
        client.messages.ComputeRegionTargetHttpsProxiesInsertRequest(
            project=target_https_proxy_ref.project,
            region=target_https_proxy_ref.region,
            targetHttpsProxy=target_https_proxy))
  else:
    service = client.apitools_client.targetHttpsProxies
    operation = service.Insert(
        client.messages.ComputeTargetHttpsProxiesInsertRequest(
            project=target_https_proxy_ref.project,
            targetHttpsProxy=target_https_proxy))

  return _WaitForOperation(resources, service, operation,
                           target_https_proxy_ref, 'Inserting TargetHttpsProxy')


def _SendPatchRequest(client, resources, target_https_proxy_ref,
                      target_https_proxy):
  """Make target HTTP proxy patch request."""
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
      target_https_proxy_ref):
    service = client.apitools_client.regionTargetHttpsProxies
    operation = service.Patch(
        client.messages.ComputeRegionTargetHttpsProxiesPatchRequest(
            project=target_https_proxy_ref.project,
            region=target_https_proxy_ref.region,
            targetHttpsProxy=target_https_proxy_ref.Name(),
            targetHttpsProxyResource=target_https_proxy))
  else:
    service = client.apitools_client.targetHttpsProxies
    operation = service.Patch(
        client.messages.ComputeTargetHttpsProxiesPatchRequest(
            project=target_https_proxy_ref.project,
            targetHttpsProxy=target_https_proxy_ref.Name(),
            targetHttpsProxyResource=target_https_proxy))

  return _WaitForOperation(resources, service, operation,
                           target_https_proxy_ref, 'Updating TargetHttpsProxy')


def _WaitForOperation(resources, service, operation, target_https_proxy_ref,
                      message):
  """Waits for the TargetHttpsProxy operation to finish."""
  if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
      target_https_proxy_ref):
    collection = operation_utils.GetRegionalOperationsCollection()
  else:
    collection = operation_utils.GetGlobalOperationsCollection()

  return operation_utils.WaitForOperation(resources, service, operation,
                                          collection, target_https_proxy_ref,
                                          message)


def _Run(args, holder, target_https_proxy_arg, release_track):
  """Issues requests necessary to import target HTTPS proxies."""
  client = holder.client
  resources = holder.resources

  target_https_proxy_ref = target_https_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

  try:
    target_https_proxy = export_util.Import(
        message_type=client.messages.TargetHttpsProxy,
        stream=data,
        schema_path=_GetSchemaPath(release_track))
  except yaml_validator.ValidationError as e:
    raise compute_exceptions.ValidationError(str(e))

  # Get existing target HTTPS proxy.
  try:
    old_target_https_proxy = target_https_proxies_utils.SendGetRequest(
        client, target_https_proxy_ref)
  except apitools_exceptions.HttpError as error:
    if error.status_code != 404:
      raise error
    # Target HTTPS proxy does not exist, create a new one.
    return _SendInsertRequest(client, resources, target_https_proxy_ref,
                              target_https_proxy)

  if old_target_https_proxy == target_https_proxy:
    return

  console_io.PromptContinue(
      message=('Target Https Proxy [{0}] will be overwritten.').format(
          target_https_proxy_ref.Name()),
      cancel_on_no=True)

  # Populate id and fingerprint fields. These two fields are manually
  # removed from the schema files.
  target_https_proxy.id = old_target_https_proxy.id

  if hasattr(old_target_https_proxy, 'fingerprint'):
    target_https_proxy.fingerprint = old_target_https_proxy.fingerprint

  # Unspecified fields are assumed to be cleared.
  cleared_fields = []
  if target_https_proxy.description is None:
    cleared_fields.append('description')
  if target_https_proxy.serverTlsPolicy is None:
    cleared_fields.append('serverTlsPolicy')
  if target_https_proxy.authorizationPolicy is None:
    cleared_fields.append('authorizationPolicy')
  if hasattr(target_https_proxy,
             'certificateMap') and target_https_proxy.certificateMap is None:
    cleared_fields.append('certificateMap')
  if hasattr(target_https_proxy,
             'httpFilters') and not target_https_proxy.httpFilters:
    cleared_fields.append('httpFilters')
  if target_https_proxy.proxyBind is None:
    cleared_fields.append('proxyBind')
  if target_https_proxy.quicOverride is None:
    cleared_fields.append('quicOverride')
  if not target_https_proxy.sslCertificates:
    cleared_fields.append('sslCertificates')
  if target_https_proxy.sslPolicy is None:
    cleared_fields.append('sslPolicy')
  if target_https_proxy.urlMap is None:
    cleared_fields.append('urlMap')

  with client.apitools_client.IncludeFields(cleared_fields):
    return _SendPatchRequest(client, resources, target_https_proxy_ref,
                             target_https_proxy)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Import(base.UpdateCommand):
  """Import a target HTTPS Proxy."""

  detailed_help = _DetailedHelp()
  TARGET_HTTPS_PROXY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument()
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='import')
    export_util.AddImportFlags(
        parser, _GetSchemaPath(cls.ReleaseTrack(), for_help=True))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.TARGET_HTTPS_PROXY_ARG, self.ReleaseTrack())
