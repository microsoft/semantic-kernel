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
"""Import backend service command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        Imports a backend service's configuration from a file.
        """,
    'EXAMPLES':
        """\
        A backend service can be imported by running:

          $ {command} NAME --source=<path-to-file> --global
        """
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ImportGA(base.UpdateCommand):
  """Import a backend service.

  If the specified backend service already exists, it will be overwritten.
  Otherwise, a new backend service will be created.
  To edit a backend service you can export the backend service to a file,
  edit its configuration, and then import the new configuration.
  """

  detailed_help = DETAILED_HELP
  _support_negative_cache = False

  @classmethod
  def GetApiVersion(cls):
    """Returns the API version based on the release track."""
    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      return 'alpha'
    elif cls.ReleaseTrack() == base.ReleaseTrack.BETA:
      return 'beta'
    return 'v1'

  @classmethod
  def GetSchemaPath(cls, for_help=False):
    """Returns the resource schema path."""
    return export_util.GetSchemaPath(
        'compute', cls.GetApiVersion(), 'BackendService', for_help=for_help)

  @classmethod
  def Args(cls, parser):
    flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.AddArgument(
        parser, operation_type='import')
    export_util.AddImportFlags(parser, cls.GetSchemaPath(for_help=True))

  def SendPatchRequest(self, client, resources, backend_service_ref,
                       replacement):
    """Sends a Backend Services patch request and waits for the operation to finish.

    Args:
      client: The API client.
      resources: The resource parser.
      backend_service_ref: The backend service reference.
      replacement: The backend service to patch with.

    Returns:
      The operation result.
    """
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      service = client.apitools_client.regionBackendServices
      operation = client.apitools_client.regionBackendServices.Patch(
          client.messages.ComputeRegionBackendServicesPatchRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              backendService=backend_service_ref.Name(),
              backendServiceResource=replacement))
    else:
      service = client.apitools_client.backendServices
      operation = client.apitools_client.backendServices.Patch(
          client.messages.ComputeBackendServicesPatchRequest(
              project=backend_service_ref.project,
              backendService=backend_service_ref.Name(),
              backendServiceResource=replacement))

    return backend_services_utils.WaitForOperation(resources, service,
                                                   operation,
                                                   backend_service_ref,
                                                   'Updating backend service')

  def SendInsertRequest(self, client, resources, backend_service_ref,
                        backend_service):
    """Sends a Backend Services insert request and waits for the operation to finish.

    Args:
      client: The API client.
      resources: The resource parser.
      backend_service_ref: The backend service reference.
      backend_service: The backend service to insert.

    Returns:
      The operation result.
    """
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      service = client.apitools_client.regionBackendServices
      operation = client.apitools_client.regionBackendServices.Insert(
          client.messages.ComputeRegionBackendServicesInsertRequest(
              project=backend_service_ref.project,
              region=backend_service_ref.region,
              backendService=backend_service))
    else:
      service = client.apitools_client.backendServices
      operation = client.apitools_client.backendServices.Insert(
          client.messages.ComputeBackendServicesInsertRequest(
              project=backend_service_ref.project,
              backendService=backend_service))

    return backend_services_utils.WaitForOperation(resources, service,
                                                   operation,
                                                   backend_service_ref,
                                                   'Creating backend service')

  def GetClearedFieldList(self, backend_service):
    """Retrieves a list of fields to clear for the backend service being inserted.

    Args:
      backend_service: The backend service being inserted.

    Returns:
      The the list of fields to clear for a GA resource.
    """
    # Unspecified fields are assumed to be cleared.
    cleared_fields = []
    # TODO(b/321258406) This entire section ought to use a library which
    # walks the schema and compares it to the resource being imported
    # and the utility must be tested to verify that deeply nested structures
    # are creating field masks appropriately.
    if not backend_service.securitySettings:
      cleared_fields.append('securitySettings')
    if not backend_service.localityLbPolicy:
      cleared_fields.append('localityLbPolicy')
    if not backend_service.localityLbPolicies:
      cleared_fields.append('localityLbPolicies')
    if not backend_service.circuitBreakers:
      cleared_fields.append('circuitBreakers')
    if not backend_service.consistentHash:
      cleared_fields.append('consistentHash')
    if not backend_service.outlierDetection:
      cleared_fields.append('outlierDetection')
    if not backend_service.customRequestHeaders:
      cleared_fields.append('customRequestHeaders')
    if not backend_service.customResponseHeaders:
      cleared_fields.append('customResponseHeaders')
    if backend_service.cdnPolicy:
      cdn_policy = backend_service.cdnPolicy
      if cdn_policy.defaultTtl is None:
        cleared_fields.append('cdnPolicy.defaultTtl')
      if cdn_policy.clientTtl is None:
        cleared_fields.append('cdnPolicy.clientTtl')
      if cdn_policy.maxTtl is None:
        cleared_fields.append('cdnPolicy.maxTtl')
      if not cdn_policy.negativeCachingPolicy:
        cleared_fields.append('cdnPolicy.negativeCachingPolicy')
      if not cdn_policy.bypassCacheOnRequestHeaders:
        cleared_fields.append('cdnPolicy.bypassCacheOnRequestHeaders')
      if cdn_policy.serveWhileStale is None:
        cleared_fields.append('cdnPolicy.serveWhileStale')
      if cdn_policy.requestCoalescing is None:
        cleared_fields.append('cdnPolicy.requestCoalescing')
    else:
      cleared_fields.append('cdnPolicy')
    return cleared_fields

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    backend_service_ref = (
        flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG.ResolveAsResource(
            args,
            resources,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))

    data = console_io.ReadFromFileOrStdin(args.source or '-', binary=False)

    try:
      backend_service = export_util.Import(
          message_type=client.messages.BackendService,
          stream=data,
          schema_path=self.GetSchemaPath())
    except yaml_validator.ValidationError as e:
      raise exceptions.ValidationError(str(e))

    # Get existing backend service.
    try:
      backend_service_old = backend_services_utils.SendGetRequest(
          client, backend_service_ref)
    except apitools_exceptions.HttpError as error:
      if error.status_code != 404:
        raise error
      # Backend service does not exist, create a new one.
      return self.SendInsertRequest(client, resources, backend_service_ref,
                                    backend_service)

    # No change, do not send requests to server.
    if backend_service_old == backend_service:
      return

    console_io.PromptContinue(
        message=('Backend Service [{0}] will be overwritten.').format(
            backend_service_ref.Name()),
        cancel_on_no=True)

    # populate id and fingerprint fields. These two fields are manually
    # removed from the schema files.
    backend_service.id = backend_service_old.id
    backend_service.fingerprint = backend_service_old.fingerprint

    # Unspecified fields are assumed to be cleared.
    cleared_fields = self.GetClearedFieldList(backend_service)

    with client.apitools_client.IncludeFields(cleared_fields):
      return self.SendPatchRequest(client, resources, backend_service_ref,
                                   backend_service)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ImportAlphaBeta(ImportGA):
  """Import a backend service.

  If the specified backend service already exists, it will be overwritten.
  Otherwise, a new backend service will be created.
  To edit a backend service you can export the backend service to a file,
  edit its configuration, and then import the new configuration.
  """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ImportAlpha(ImportGA):
  """Import a backend service.

  If the specified backend service already exists, it will be overwritten.
  Otherwise, a new backend service will be created.
  To edit a backend service you can export the backend service to a file,
  edit its configuration, and then import the new configuration.
  """

  def GetClearedFieldList(self, backend_service):
    """Retrieves a list of fields to clear for the backend service being inserted.

    Args:
      backend_service: The backend service being inserted.

    Returns:
      The the list of fields to clear for a GA resource.
    """

    # TODO(b/321258406) This entire section ought to use a library which
    # walks the schema and compares it to the resource being imported
    # and the utility must be tested to verify that deeply nested structures
    # are creating field masks appropriately.
    cleared_fields = super().GetClearedFieldList(backend_service)
    if backend_service.haPolicy:
      ha_policy = backend_service.haPolicy
      if not ha_policy.fastIPMove:
        cleared_fields.append('haPolicy.fastIPMove')
      if ha_policy.leader:
        leader = ha_policy.leader
        if not leader.backendGroup:
          cleared_fields.append('haPolicy.leader.backendGroup')
        if leader.networkEndpoint:
          if not leader.networkEndpoint.instance:
            cleared_fields.append('haPolicy.leader.networkEndpoint.instance')
        else:
          cleared_fields.append('haPolicy.leader.networkEndpoint')
      else:
        cleared_fields.append('haPolicy.leader')
    else:
      cleared_fields.append('haPolicy')
    return cleared_fields
