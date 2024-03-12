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

# pylint: disable=raise-missing-from
"""Allows you to write surfaces in terms of logical Serverless operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import dataclasses
import functools
import random
import string

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.run import condition as run_condition
from googlecloudsdk.api_lib.run import configuration
from googlecloudsdk.api_lib.run import domain_mapping
from googlecloudsdk.api_lib.run import execution
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run import job
from googlecloudsdk.api_lib.run import metric_names
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import route
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import task
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.run import artifact_registry
from googlecloudsdk.command_lib.run import config_changes as config_changes_mod
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import name_generator
from googlecloudsdk.command_lib.run import op_pollers
from googlecloudsdk.command_lib.run import resource_name_conversion
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run.sourcedeploys import deployer
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import retry
import six

DEFAULT_ENDPOINT_VERSION = 'v1'

_NONCE_LENGTH = 10

# Wait 11 mins for each deployment. This is longer than the server timeout,
# making it more likely to get a useful error message from the server.
MAX_WAIT_MS = 660000

ALLOW_UNAUTH_POLICY_BINDING_MEMBER = 'allUsers'
ALLOW_UNAUTH_POLICY_BINDING_ROLE = 'roles/run.invoker'

NEEDED_IAM_PERMISSIONS = ['run.services.setIamPolicy']


class UnknownAPIError(exceptions.Error):
  pass


@contextlib.contextmanager
def Connect(conn_context, already_activated_service=False):
  """Provide a ServerlessOperations instance to use.

  If we're using the GKE Serverless Add-on, connect to the relevant cluster.
  Otherwise, connect to the right region of GSE.

  Arguments:
    conn_context: a context manager that yields a ConnectionInfo and manages a
      dynamic context that makes connecting to serverless possible.
    already_activated_service: bool that should be true if we already checked if
      the run.googleapis.com service was enabled. If this is true, we skip
      prompting the user to enable the service because they should have already
      been prompted if the API wasn't activated.

  Yields:
    A ServerlessOperations instance.
  """

  # The One Platform client is required for making requests against
  # endpoints that do not supported Kubernetes-style resource naming
  # conventions. The One Platform client must be initialized outside of a
  # connection context so that it does not pick up the api_endpoint_overrides
  # values from the connection context.
  # pylint: disable=protected-access
  op_client = apis.GetClientInstance(
      conn_context.api_name,
      conn_context.api_version,
      skip_activation_prompt=already_activated_service,
  )
  # pylint: enable=protected-access

  with conn_context as conn_info:
    response_func = (
        apis.CheckResponse(already_activated_service)
        if conn_context.supports_one_platform
        else None
    )
    # pylint: disable=protected-access
    client = apis_internal._GetClientInstance(
        conn_info.api_name,
        conn_info.api_version,
        # Only check response if not connecting to GKE
        check_response_func=response_func,
        http_client=conn_context.HttpClient(),
    )
    # pylint: enable=protected-access
    yield ServerlessOperations(
        client,
        conn_info.api_name,
        conn_info.api_version,
        conn_info.region,
        op_client,
    )


def _Nonce():
  """Return a random string with unlikely collision to use as a nonce."""
  return ''.join(
      random.choice(string.ascii_lowercase) for _ in range(_NONCE_LENGTH)
  )


@dataclasses.dataclass(frozen=True)
class _NewRevisionNonceChange(config_changes_mod.TemplateConfigChanger):
  """Forces a new revision to get created by posting a random nonce label."""

  nonce: str

  def Adjust(self, resource):
    resource.template.labels[revision.NONCE_LABEL] = self.nonce
    resource.template.name = None
    return resource


class _NewRevisionForcingChange(config_changes_mod.RevisionNameChanges):
  """Forces a new revision to get created by changing the revision name."""

  def Adjust(self, resource):
    """Adjust by revision name."""
    if revision.NONCE_LABEL in resource.template.labels:
      del resource.template.labels[revision.NONCE_LABEL]
    return super().Adjust(resource)


def _IsDigest(url):
  """Return true if the given image url is by-digest."""
  return '@sha256:' in url


@dataclasses.dataclass(frozen=True)
class _SwitchToDigestChange(config_changes_mod.TemplateConfigChanger):
  """Switches the configuration from by-tag to by-digest."""

  base_revision: revision.Revision

  def Adjust(self, resource):
    if _IsDigest(self.base_revision.image):
      return resource
    if not self.base_revision.image_digest:
      return resource

    resource.template.image = self.base_revision.image_digest
    return resource


@dataclasses.dataclass(frozen=True)
class _AddDigestToImageChange(config_changes_mod.TemplateConfigChanger):
  """Add image digest that comes from source build."""

  image_digest: str

  def Adjust(self, resource):
    if _IsDigest(resource.template.image):
      return resource

    resource.template.image = resource.template.image + '@' + self.image_digest
    return resource


class ServerlessOperations(object):
  """Client used by Serverless to communicate with the actual Serverless API."""

  def __init__(self, client, api_name, api_version, region, op_client):
    """Inits ServerlessOperations with given API clients.

    Args:
      client: The API client for interacting with Kubernetes Cloud Run APIs.
      api_name: str, The name of the Cloud Run API.
      api_version: str, The version of the Cloud Run API.
      region: str, The region of the control plane if operating against hosted
        Cloud Run, else None.
      op_client: The API client for interacting with One Platform APIs. Or None
        if interacting with Cloud Run for Anthos.
    """
    self._client = client
    self._registry = resources.REGISTRY.Clone()
    self._registry.RegisterApiByName(api_name, api_version)
    self._op_client = op_client
    self._region = region

  @property
  def messages_module(self):
    return self._client.MESSAGES_MODULE

  def GetRevision(self, revision_ref):
    """Get the revision.

    Args:
      revision_ref: Resource, revision to get.

    Returns:
      A revision.Revision object.
    """
    messages = self.messages_module
    revision_name = revision_ref.RelativeName()
    request = messages.RunNamespacesRevisionsGetRequest(name=revision_name)
    try:
      with metrics.RecordDuration(metric_names.GET_REVISION):
        response = self._client.namespaces_revisions.Get(request)
      return revision.Revision(response, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

  def Upload(self, deployable):
    """Upload the code for the given deployable."""
    deployable.UploadFiles()

  def WaitForCondition(self, poller, max_wait_ms=0):
    """Wait for a configuration to be ready in latest revision.

    Args:
      poller: A ConditionPoller object.
      max_wait_ms: int, if not 0, passed to waiter.PollUntilDone.

    Returns:
      A condition.Conditions object.

    Raises:
      RetryException: Max retry limit exceeded.
      ConfigurationError: configuration failed to
    """

    try:
      if max_wait_ms == 0:
        return waiter.PollUntilDone(poller, None, wait_ceiling_ms=1000)
      return waiter.PollUntilDone(
          poller, None, max_wait_ms=max_wait_ms, wait_ceiling_ms=1000
      )
    except retry.RetryException as err:
      conditions = poller.GetConditions()
      # err.message already indicates timeout. Check ready_cond_type for more
      # information.
      msg = conditions.DescriptiveMessage() if conditions else None
      if msg:
        log.error('Still waiting: {}'.format(msg))
      raise err

  def ListServices(self, namespace_ref):
    """Returns all services in the namespace."""
    messages = self.messages_module
    request = messages.RunNamespacesServicesListRequest(
        parent=namespace_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.LIST_SERVICES):
        response = self._client.namespaces_services.List(request)
      return [service.Service(item, messages) for item in response.items]
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

  def ListConfigurations(self, namespace_ref):
    """Returns all configurations in the namespace."""
    messages = self.messages_module
    request = messages.RunNamespacesConfigurationsListRequest(
        parent=namespace_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.LIST_CONFIGURATIONS):
        response = self._client.namespaces_configurations.List(request)
      return [
          configuration.Configuration(item, messages) for item in response.items
      ]
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

  def ListRoutes(self, namespace_ref):
    """Returns all routes in the namespace."""
    messages = self.messages_module
    request = messages.RunNamespacesRoutesListRequest(
        parent=namespace_ref.RelativeName()
    )
    with metrics.RecordDuration(metric_names.LIST_ROUTES):
      response = self._client.namespaces_routes.List(request)
    return [route.Route(item, messages) for item in response.items]

  def GetService(self, service_ref):
    """Return the relevant Service from the server, or None if 404."""
    messages = self.messages_module
    service_get_request = messages.RunNamespacesServicesGetRequest(
        name=service_ref.RelativeName()
    )

    try:
      with metrics.RecordDuration(metric_names.GET_SERVICE):
        service_get_response = self._client.namespaces_services.Get(
            service_get_request
        )
        return service.Service(service_get_response, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

  def WaitService(self, operation_id):
    """Return the relevant Service from the server, or None if 404."""
    messages = self.messages_module
    project = properties.VALUES.core.project.Get(required=True)
    op_name = (
        f'projects/{project}/locations/{self._region}/operations/{operation_id}'
    )
    op_ref = self._registry.ParseRelativeName(
        op_name, collection='run.projects.locations.operations'
    )
    try:
      with metrics.RecordDuration(metric_names.WAIT_OPERATION):
        poller = op_pollers.WaitOperationPoller(
            self._client.projects_locations_services,
            self._client.projects_locations_operations,
        )
        operation = waiter.PollUntilDone(poller, op_ref)
        as_dict = encoding.MessageToPyValue(operation.response)
        as_pb = encoding.PyValueToMessage(messages.Service, as_dict)
        return service.Service(as_pb, self.messages_module)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

  def GetConfiguration(self, service_or_configuration_ref):
    """Return the relevant Configuration from the server, or None if 404."""
    messages = self.messages_module
    if hasattr(service_or_configuration_ref, 'servicesId'):
      name = self._registry.Parse(
          service_or_configuration_ref.servicesId,
          params={
              'namespacesId': service_or_configuration_ref.namespacesId,
          },
          collection='run.namespaces.configurations',
      ).RelativeName()
    else:
      name = service_or_configuration_ref.RelativeName()
    configuration_get_request = messages.RunNamespacesConfigurationsGetRequest(
        name=name
    )

    try:
      with metrics.RecordDuration(metric_names.GET_CONFIGURATION):
        configuration_get_response = self._client.namespaces_configurations.Get(
            configuration_get_request
        )
      return configuration.Configuration(configuration_get_response, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

  def GetRoute(self, service_or_route_ref):
    """Return the relevant Route from the server, or None if 404."""
    messages = self.messages_module
    if hasattr(service_or_route_ref, 'servicesId'):
      name = self._registry.Parse(
          service_or_route_ref.servicesId,
          params={
              'namespacesId': service_or_route_ref.namespacesId,
          },
          collection='run.namespaces.routes',
      ).RelativeName()
    else:
      name = service_or_route_ref.RelativeName()
    route_get_request = messages.RunNamespacesRoutesGetRequest(name=name)

    try:
      with metrics.RecordDuration(metric_names.GET_ROUTE):
        route_get_response = self._client.namespaces_routes.Get(
            route_get_request
        )
      return route.Route(route_get_response, messages)
    except api_exceptions.HttpNotFoundError:
      return None

  def DeleteService(self, service_ref):
    """Delete the provided Service.

    Args:
      service_ref: Resource, a reference to the Service to delete

    Raises:
      ServiceNotFoundError: if provided service is not found.
    """
    messages = self.messages_module
    service_name = service_ref.RelativeName()
    service_delete_request = messages.RunNamespacesServicesDeleteRequest(
        name=service_name,
    )

    try:
      with metrics.RecordDuration(metric_names.DELETE_SERVICE):
        self._client.namespaces_services.Delete(service_delete_request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.ServiceNotFoundError(
          'Service [{}] could not be found.'.format(service_ref.servicesId)
      )

  def DeleteRevision(self, revision_ref):
    """Delete the provided Revision.

    Args:
      revision_ref: Resource, a reference to the Revision to delete

    Raises:
      RevisionNotFoundError: if provided revision is not found.
    """
    messages = self.messages_module
    revision_name = revision_ref.RelativeName()
    request = messages.RunNamespacesRevisionsDeleteRequest(name=revision_name)
    try:
      with metrics.RecordDuration(metric_names.DELETE_REVISION):
        self._client.namespaces_revisions.Delete(request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.RevisionNotFoundError(
          'Revision [{}] could not be found.'.format(revision_ref.revisionsId)
      )

  def GetRevisionsByNonce(self, namespace_ref, nonce):
    """Return all revisions with the given nonce."""
    messages = self.messages_module
    request = messages.RunNamespacesRevisionsListRequest(
        parent=namespace_ref.RelativeName(),
        labelSelector='{} = {}'.format(revision.NONCE_LABEL, nonce),
    )
    try:
      response = self._client.namespaces_revisions.List(request)
      return [revision.Revision(item, messages) for item in response.items]
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

  def _GetBaseRevision(self, template, metadata, status):
    """Return a Revision for use as the "base revision" for a change.

    When making a change that should not affect the code running, the
    "base revision" is the revision that we should lock the code to - it's where
    we get the digest for the image to run.

    Getting this revision:
      * If there's a name in the template metadata, use that
      * If there's a nonce in the revisonTemplate metadata, use that
      * If that query produces >1 or 0 after a short timeout, use
        the latestCreatedRevision in status.

    Arguments:
      template: Revision, the revision template to get the base revision of. May
        have been derived from a Service.
      metadata: ObjectMeta, the metadata from the top-level object
      status: Union[ConfigurationStatus, ServiceStatus], the status of the top-
        level object.

    Returns:
      The base revision of the configuration or None if not found by revision
        name nor nonce and latestCreatedRevisionName does not exist on the
        Service object.
    """
    base_revision = None
    # Try to find by revision name
    base_revision_name = template.name
    if base_revision_name:
      try:
        revision_ref_getter = functools.partial(
            self._registry.Parse,
            params={'namespacesId': metadata.namespace},
            collection='run.namespaces.revisions',
        )
        poller = op_pollers.RevisionNameBasedPoller(self, revision_ref_getter)
        base_revision = poller.GetResult(
            waiter.PollUntilDone(
                poller, base_revision_name, sleep_ms=500, max_wait_ms=2000
            )
        )
      except retry.RetryException:
        pass
    # Name polling didn't work. Fall back to nonce polling
    if not base_revision:
      base_revision_nonce = template.labels.get(revision.NONCE_LABEL, None)
      if base_revision_nonce:
        try:
          # TODO(b/148817410): Remove this when the api has been split.
          # This try/except block is needed because the v1alpha1 and v1 run apis
          # have different collection names for the namespaces.
          try:
            namespace_ref = self._registry.Parse(
                metadata.namespace, collection='run.namespaces'
            )
          except resources.InvalidCollectionException:
            namespace_ref = self._registry.Parse(
                metadata.namespace, collection='run.api.v1.namespaces'
            )
          poller = op_pollers.NonceBasedRevisionPoller(self, namespace_ref)
          base_revision = poller.GetResult(
              waiter.PollUntilDone(
                  poller, base_revision_nonce, sleep_ms=500, max_wait_ms=2000
              )
          )
        except retry.RetryException:
          pass
    # Nonce polling didn't work, because some client didn't post one or didn't
    # change one. Fall back to the (slightly racy) `latestCreatedRevisionName`.
    if not base_revision:
      if status.latestCreatedRevisionName:
        # Get by latestCreatedRevisionName
        revision_ref = self._registry.Parse(
            status.latestCreatedRevisionName,
            params={'namespacesId': metadata.namespace},
            collection='run.namespaces.revisions',
        )
        base_revision = self.GetRevision(revision_ref)
    return base_revision

  def _EnsureImageDigest(self, serv, config_changes):
    """Make config_changes include switch by-digest image if not so already."""
    if not _IsDigest(serv.template.image):
      base_revision = self._GetBaseRevision(
          serv.template, serv.metadata, serv.status
      )
      if base_revision:
        config_changes.append(_SwitchToDigestChange(base_revision))

  def _UpdateOrCreateService(
      self, service_ref, config_changes, with_code, serv, dry_run=False
  ):
    """Apply config_changes to the service.

    Create it if necessary.

    Arguments:
      service_ref: Reference to the service to create or update
      config_changes: list of ConfigChanger to modify the service with
      with_code: bool, True if the config_changes contains code to deploy. We
        can't create the service if we're not deploying code.
      serv: service.Service, For update the Service to update and for create
        None.
      dry_run: bool, if True only validate the change.

    Returns:
      The Service object we created or modified.
    """
    messages = self.messages_module
    try:
      if serv:
        # PUT the changed Service
        serv = config_changes_mod.WithChanges(serv, config_changes)
        serv_name = service_ref.RelativeName()
        serv_update_req = messages.RunNamespacesServicesReplaceServiceRequest(
            service=serv.Message(),
            name=serv_name,
            dryRun=('all' if dry_run else None),
        )
        with metrics.RecordDuration(metric_names.UPDATE_SERVICE):
          updated = self._client.namespaces_services.ReplaceService(
              serv_update_req
          )
        return service.Service(updated, messages)

      else:
        if not with_code:
          raise serverless_exceptions.ServiceNotFoundError(
              'Service [{}] could not be found.'.format(service_ref.servicesId)
          )
        # POST a new Service
        new_serv = service.Service.New(self._client, service_ref.namespacesId)
        new_serv.name = service_ref.servicesId
        parent = service_ref.Parent().RelativeName()
        new_serv = config_changes_mod.WithChanges(new_serv, config_changes)
        serv_create_req = messages.RunNamespacesServicesCreateRequest(
            service=new_serv.Message(),
            parent=parent,
            dryRun='all' if dry_run else None,
        )
        with metrics.RecordDuration(metric_names.CREATE_SERVICE):
          raw_service = self._client.namespaces_services.Create(serv_create_req)
        return service.Service(raw_service, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpBadRequestError as e:
      exceptions.reraise(serverless_exceptions.HttpError(e))
    except api_exceptions.HttpNotFoundError as e:
      platform = properties.VALUES.run.platform.Get()
      error_msg = 'Deployment endpoint was not found.'
      if platform == 'gke':
        all_clusters = global_methods.ListClusters()
        clusters = ['* {} in {}'.format(c.name, c.zone) for c in all_clusters]
        error_msg += (
            ' Perhaps the provided cluster was invalid or '
            'does not have Cloud Run enabled. Pass the '
            '`--cluster` and `--cluster-location` flags or set the '
            '`run/cluster` and `run/cluster_location` properties to '
            'a valid cluster and zone and retry.'
            '\nAvailable clusters:\n{}'.format('\n'.join(clusters))
        )
      elif platform == 'managed':
        all_regions = global_methods.ListRegions(self._op_client)
        if self._region not in all_regions:
          regions = ['* {}'.format(r) for r in all_regions]
          error_msg += (
              ' The provided region was invalid. '
              'Pass the `--region` flag or set the '
              '`run/region` property to a valid region and retry.'
              '\nAvailable regions:\n{}'.format('\n'.join(regions))
          )
      elif platform == 'kubernetes':
        error_msg += (
            ' Perhaps the provided cluster was invalid or '
            'does not have Cloud Run enabled. Ensure in your '
            'kubeconfig file that the cluster referenced in '
            'the current context or the specified context '
            'is a valid cluster and retry.'
        )
      raise serverless_exceptions.DeploymentFailedError(error_msg)
    except api_exceptions.HttpError as e:
      platform = properties.VALUES.run.platform.Get()
      if platform == 'managed':
        exceptions.reraise(e)
      k8s_error = serverless_exceptions.KubernetesExceptionParser(e)
      causes = '\n\n'.join([c['message'] for c in k8s_error.causes])
      if not causes:
        causes = k8s_error.error
      raise serverless_exceptions.KubernetesError(
          'Error{}:\n{}\n'.format(
              's' if len(k8s_error.causes) > 1 else '', causes
          )
      )

  def UpdateTraffic(self, service_ref, config_changes, tracker, asyn):
    """Update traffic splits for service."""
    if tracker is None:
      tracker = progress_tracker.NoOpStagedProgressTracker(
          stages.UpdateTrafficStages(),
          interruptable=True,
          aborted_message='aborted',
      )
    serv = self.GetService(service_ref)
    if not serv:
      raise serverless_exceptions.ServiceNotFoundError(
          'Service [{}] could not be found.'.format(service_ref.servicesId)
      )

    updated_serv = self._UpdateOrCreateService(
        service_ref, config_changes, False, serv
    )

    if not asyn:
      if updated_serv.conditions.IsReady():
        return updated_serv

      getter = (
          functools.partial(self.GetService, service_ref)
          if updated_serv.operation_id is None
          else functools.partial(self.WaitService, updated_serv.operation_id)
      )
      poller = op_pollers.ServiceConditionPoller(
          getter, tracker, serv=updated_serv
      )
      self.WaitForCondition(poller)
      updated_serv = poller.GetResource()
    return updated_serv

  def _AddRevisionForcingChange(self, serv, config_changes):
    """Get a new revision forcing config change for the given service."""
    curr_generation = serv.generation if serv is not None else 0
    revision_suffix = '{}-{}'.format(
        str(curr_generation + 1).zfill(5), name_generator.GenerateName()
    )
    config_changes.insert(0, _NewRevisionForcingChange(revision_suffix))

  def ReleaseService(
      self,
      service_ref,
      config_changes,
      release_track,
      tracker=None,
      asyn=False,
      allow_unauthenticated=None,
      for_replace=False,
      prefetch=False,
      build_image=None,
      build_pack=None,
      build_source=None,
      repo_to_create=None,
      already_activated_services=False,
      dry_run=False,
      generate_name=False,
  ):
    """Change the given service in prod using the given config_changes.

    Ensures a new revision is always created, even if the spec of the revision
    has not changed.

    Args:
      service_ref: Resource, the service to release.
      config_changes: list, objects that implement Adjust().
      release_track: ReleaseTrack, the release track of a command calling this.
      tracker: StagedProgressTracker, to report on the progress of releasing.
      asyn: bool, if True, return without waiting for the service to be updated.
      allow_unauthenticated: bool, True if creating a hosted Cloud Run service
        which should also have its IAM policy set to allow unauthenticated
        access. False if removing the IAM policy to allow unauthenticated access
        from a service.
      for_replace: bool, If the change is for a replacing the service from a
        YAML specification.
      prefetch: the service, pre-fetched for ReleaseService. `False` indicates
        the caller did not perform a prefetch; `None` indicates a nonexistent
        service.
      build_image: The build image reference to the build.
      build_pack: The build pack reference to the build.
      build_source: The build source reference to the build.
      repo_to_create: Optional
        googlecloudsdk.command_lib.artifacts.docker_util.DockerRepo defining a
        repository to be created.
      already_activated_services: bool. If true, skip activation prompts for
        services
      dry_run: bool. If true, only validate the configuration.
      generate_name: bool. If true, create a revision name, otherwise add nonce.

    Returns:
      service.Service, the service as returned by the server on the POST/PUT
       request to create/update the service.
    """
    if tracker is None:
      tracker = progress_tracker.NoOpStagedProgressTracker(
          stages.ServiceStages(
              allow_unauthenticated is not None,
              include_build=build_source is not None,
              include_create_repo=repo_to_create is not None,
          ),
          interruptable=True,
          aborted_message='aborted',
      )

    # TODO(b/321837261): Use Build API to create Repository
    if repo_to_create:
      self._CreateRepository(
          tracker,
          repo_to_create,
          skip_activation_prompt=already_activated_services,
      )

    if build_source is not None:
      image_digest = deployer.CreateImage(
          tracker,
          build_image,
          build_source,
          build_pack,
          release_track,
          already_activated_services,
          self._region,
          service_ref,
      )
      if image_digest is None:
        return
      config_changes.append(_AddDigestToImageChange(image_digest))
    if prefetch is None:
      serv = None
    elif build_source:
      # if we're building from source, we want to force a new fetch
      # because building takes a while which leaves a long time for
      # potential write conflicts.
      serv = self.GetService(service_ref)
    else:
      serv = prefetch or self.GetService(service_ref)
    if for_replace:
      with_image = True
    else:
      with_image = any(
          isinstance(c, config_changes_mod.ImageChange) for c in config_changes
      )
      if config_changes_mod.AdjustsTemplate(config_changes):
        # Only force a new revision if there's other template-level changes that
        # warrant a new revision.
        if generate_name:
          self._AddRevisionForcingChange(serv, config_changes)
        else:
          config_changes.append(_NewRevisionNonceChange(_Nonce()))
        if serv and not with_image:
          # Avoid changing the running code by making the new revision by digest
          self._EnsureImageDigest(serv, config_changes)

    if serv and serv.metadata.deletionTimestamp is not None:
      raise serverless_exceptions.DeploymentFailedError(
          'Service [{}] is in the process of being deleted.'.format(
              service_ref.servicesId
          )
      )

    updated_service = self._UpdateOrCreateService(
        service_ref, config_changes, with_image, serv, dry_run
    )

    if allow_unauthenticated is not None:
      try:
        tracker.StartStage(stages.SERVICE_IAM_POLICY_SET)
        tracker.UpdateStage(stages.SERVICE_IAM_POLICY_SET, '')
        self.AddOrRemoveIamPolicyBinding(
            service_ref,
            allow_unauthenticated,
            ALLOW_UNAUTH_POLICY_BINDING_MEMBER,
            ALLOW_UNAUTH_POLICY_BINDING_ROLE,
        )
        tracker.CompleteStage(stages.SERVICE_IAM_POLICY_SET)
      except api_exceptions.HttpError:
        warning_message = (
            'Setting IAM policy failed, try "gcloud beta run services '
            '{}-iam-policy-binding --region={region} --member=allUsers '
            '--role=roles/run.invoker {service}"'.format(
                'add' if allow_unauthenticated else 'remove',
                region=self._region,
                service=service_ref.servicesId,
            )
        )
        tracker.CompleteStageWithWarning(
            stages.SERVICE_IAM_POLICY_SET, warning_message=warning_message
        )

    if not asyn and not dry_run:
      if updated_service.conditions.IsReady():
        return updated_service

      getter = (
          functools.partial(self.GetService, service_ref)
          if updated_service.operation_id is None
          else functools.partial(self.WaitService, updated_service.operation_id)
      )
      poller = op_pollers.ServiceConditionPoller(
          getter,
          tracker,
          dependencies=stages.ServiceDependencies(),
          serv=updated_service,
      )
      self.WaitForCondition(poller)
      for msg in run_condition.GetNonTerminalMessages(poller.GetConditions()):
        tracker.AddWarning(msg)
      updated_service = poller.GetResource()

    return updated_service

  def ListExecutions(
      self, namespace_ref, label_selector='', limit=None, page_size=100
  ):
    """List all executions for the given job.

    Executions list gets sorted by job name, creation timestamp, and completion
    timestamp.

    Args:
      namespace_ref: Resource, namespace to list executions in
      label_selector: Optional[string], extra label selector to filter
        executions
      limit: Optional[int], max number of executions to list.
      page_size: Optional[int], number of executions to fetch at a time

    Yields:
      Executions for the given surface
    """
    messages = self.messages_module
    # NB: This is a hack to compensate for apitools not generating this line.
    #     It's necessary to make the URL parameter be "continue".
    encoding.AddCustomJsonFieldMapping(
        messages.RunNamespacesExecutionsListRequest, 'continue_', 'continue'
    )
    request = messages.RunNamespacesExecutionsListRequest(
        parent=namespace_ref.RelativeName()
    )
    if label_selector:
      request.labelSelector = label_selector
    try:
      for result in list_pager.YieldFromList(
          service=self._client.namespaces_executions,
          request=request,
          limit=limit,
          batch_size=page_size,
          current_token_attribute='continue_',
          next_token_attribute=('metadata', 'continue_'),
          batch_size_attribute='limit',
      ):
        yield execution.Execution(result, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

  def ListTasks(
      self,
      namespace_ref,
      execution_name,
      include_states=None,
      limit=None,
      page_size=100,
  ):
    """List all tasks for the given execution.

    Args:
      namespace_ref: Resource, namespace to list tasks in
      execution_name: str, The execution for which to list tasks.
      include_states: List[str], states of tasks to include in the list.
      limit: Optional[int], max number of tasks to list.
      page_size: Optional[int], number of tasks to fetch at a time

    Yields:
      Executions for the given surface
    """
    messages = self.messages_module
    # NB: This is a hack to compensate for apitools not generating this line.
    #     It's necessary to make the URL parameter be "continue".
    encoding.AddCustomJsonFieldMapping(
        messages.RunNamespacesTasksListRequest, 'continue_', 'continue'
    )
    request = messages.RunNamespacesTasksListRequest(
        parent=namespace_ref.RelativeName()
    )
    label_selectors = []
    if execution_name is not None:
      label_selectors.append(
          '{label} = {name}'.format(
              label=task.EXECUTION_LABEL, name=execution_name
          )
      )
    if include_states is not None:
      status_selector = '{label} in ({states})'.format(
          label=task.STATE_LABEL, states=','.join(include_states)
      )
      label_selectors.append(status_selector)
    if label_selectors:
      request.labelSelector = ','.join(label_selectors)
    try:
      for result in list_pager.YieldFromList(
          service=self._client.namespaces_tasks,
          request=request,
          limit=limit,
          batch_size=page_size,
          current_token_attribute='continue_',
          next_token_attribute=('metadata', 'continue_'),
          batch_size_attribute='limit',
      ):
        yield task.Task(result, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

  def ListRevisions(
      self, namespace_ref, service_name, limit=None, page_size=100
  ):
    """List all revisions for the given service.

    Revision list gets sorted by service name and creation timestamp.

    Args:
      namespace_ref: Resource, namespace to list revisions in
      service_name: str, The service for which to list revisions.
      limit: Optional[int], max number of revisions to list.
      page_size: Optional[int], number of revisions to fetch at a time

    Yields:
      Revisions for the given surface
    """
    messages = self.messages_module
    # NB: This is a hack to compensate for apitools not generating this line.
    #     It's necessary to make the URL parameter be "continue".
    encoding.AddCustomJsonFieldMapping(
        messages.RunNamespacesRevisionsListRequest, 'continue_', 'continue'
    )
    request = messages.RunNamespacesRevisionsListRequest(
        parent=namespace_ref.RelativeName(),
    )
    if service_name is not None:
      # For now, same as the service name, and keeping compatible with
      # 'service-less' operation.
      request.labelSelector = 'serving.knative.dev/service = {}'.format(
          service_name
      )
    try:
      for result in list_pager.YieldFromList(
          service=self._client.namespaces_revisions,
          request=request,
          limit=limit,
          batch_size=page_size,
          current_token_attribute='continue_',
          next_token_attribute=('metadata', 'continue_'),
          batch_size_attribute='limit',
      ):
        yield revision.Revision(result, messages)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

  def ListDomainMappings(self, namespace_ref):
    """List all domain mappings.

    Args:
      namespace_ref: Resource, namespace to list domain mappings in.

    Returns:
      A list of domain mappings.
    """
    messages = self.messages_module
    request = messages.RunNamespacesDomainmappingsListRequest(
        parent=namespace_ref.RelativeName()
    )
    with metrics.RecordDuration(metric_names.LIST_DOMAIN_MAPPINGS):
      response = self._client.namespaces_domainmappings.List(request)
    return [
        domain_mapping.DomainMapping(item, messages) for item in response.items
    ]

  def CreateDomainMapping(
      self,
      domain_mapping_ref,
      service_name,
      config_changes,
      force_override=False,
  ):
    """Create a domain mapping.

    Args:
      domain_mapping_ref: Resource, domainmapping resource.
      service_name: str, the service to which to map domain.
      config_changes: list of ConfigChanger to modify the domainmapping with
      force_override: bool, override an existing mapping of this domain.

    Returns:
      A domain_mapping.DomainMapping object.
    """

    messages = self.messages_module
    new_mapping = domain_mapping.DomainMapping.New(
        self._client, domain_mapping_ref.namespacesId
    )
    new_mapping.name = domain_mapping_ref.domainmappingsId
    new_mapping.route_name = service_name
    new_mapping.force_override = force_override

    for config_change in config_changes:
      new_mapping = config_change.Adjust(new_mapping)

    request = messages.RunNamespacesDomainmappingsCreateRequest(
        domainMapping=new_mapping.Message(),
        parent=domain_mapping_ref.Parent().RelativeName(),
    )
    with metrics.RecordDuration(metric_names.CREATE_DOMAIN_MAPPING):
      try:
        response = self._client.namespaces_domainmappings.Create(request)
      except api_exceptions.HttpConflictError:
        raise serverless_exceptions.DomainMappingCreationError(
            'Domain mapping to [{}] already exists in this region.'.format(
                domain_mapping_ref.Name()
            )
        )
      # 'run domain-mappings create' is synchronous. Poll for its completion.x
      with progress_tracker.ProgressTracker('Creating...'):
        mapping = waiter.PollUntilDone(
            op_pollers.DomainMappingResourceRecordPoller(self),
            domain_mapping_ref,
        )
      ready = mapping.conditions.get('Ready')
      message = None
      if ready and ready.get('message'):
        message = ready['message']
      if not mapping.records:
        if (
            mapping.ready_condition['reason']
            == domain_mapping.MAPPING_ALREADY_EXISTS_CONDITION_REASON
        ):
          raise serverless_exceptions.DomainMappingAlreadyExistsError(
              'Domain mapping to [{}] is already in use elsewhere.'.format(
                  domain_mapping_ref.Name()
              )
          )
        raise serverless_exceptions.DomainMappingCreationError(
            message or 'Could not create domain mapping.'
        )
      if message:
        log.status.Print(message)
      return mapping

    return domain_mapping.DomainMapping(response, messages)

  def DeleteDomainMapping(self, domain_mapping_ref):
    """Delete a domain mapping.

    Args:
      domain_mapping_ref: Resource, domainmapping resource.
    """
    messages = self.messages_module

    request = messages.RunNamespacesDomainmappingsDeleteRequest(
        name=domain_mapping_ref.RelativeName()
    )
    with metrics.RecordDuration(metric_names.DELETE_DOMAIN_MAPPING):
      self._client.namespaces_domainmappings.Delete(request)

  def GetDomainMapping(self, domain_mapping_ref):
    """Get a domain mapping.

    Args:
      domain_mapping_ref: Resource, domainmapping resource.

    Returns:
      A domain_mapping.DomainMapping object.
    """
    messages = self.messages_module
    request = messages.RunNamespacesDomainmappingsGetRequest(
        name=domain_mapping_ref.RelativeName()
    )
    with metrics.RecordDuration(metric_names.GET_DOMAIN_MAPPING):
      response = self._client.namespaces_domainmappings.Get(request)
    return domain_mapping.DomainMapping(response, messages)

  def DeployJob(
      self,
      job_ref,
      config_changes,
      release_track,
      tracker=None,
      asyn=False,
      build_image=None,
      build_pack=None,
      build_source=None,
      repo_to_create=None,
      prefetch=None,
      already_activated_services=False,
  ):
    """Deploy to create a new Cloud Run Job or to update an existing one.

    Args:
      job_ref: Resource, the job to create or update.
      config_changes: list, objects that implement Adjust().
      release_track: ReleaseTrack, the release track of a command calling this.
      tracker: StagedProgressTracker, to report on the progress of releasing.
      asyn: bool, if True, return without waiting for the job to be updated.
      build_image: The build image reference to the build.
      build_pack: The build pack reference to the build.
      build_source: The build source reference to the build.
      repo_to_create: Optional
        googlecloudsdk.command_lib.artifacts.docker_util.DockerRepo defining a
        repository to be created.
      prefetch: the job, pre-fetched for DeployJob. `None` indicates a
        nonexistent job so the job has to be created, else this is for an
        update.
      already_activated_services: bool. If true, skip activation prompts for
        services

    Returns:
      A job.Job object.
    """
    if tracker is None:
      tracker = progress_tracker.NoOpStagedProgressTracker(
          stages.JobStages(
              include_build=build_source is not None,
              include_create_repo=repo_to_create is not None,
          ),
          interruptable=True,
          aborted_message='aborted',
      )

    # TODO(b/321837261): Use Build API to create Repository
    if repo_to_create:
      self._CreateRepository(
          tracker,
          repo_to_create,
          skip_activation_prompt=already_activated_services,
      )

    if build_source is not None:
      image_digest = deployer.CreateImage(
          tracker,
          build_image,
          build_source,
          build_pack,
          release_track,
          already_activated_services,
          self._region,
          job_ref,
      )
      if image_digest is None:
        return
      config_changes.append(_AddDigestToImageChange(image_digest))

    is_create = not prefetch
    if is_create:
      return self.CreateJob(job_ref, config_changes, tracker, asyn)
    else:
      return self.UpdateJob(job_ref, config_changes, tracker, asyn)

  def CreateJob(self, job_ref, config_changes, tracker=None, asyn=False):
    """Create a new Cloud Run Job.

    Args:
      job_ref: Resource, the job to create.
      config_changes: list, objects that implement Adjust().
      tracker: StagedProgressTracker, to report on the progress of releasing.
      asyn: bool, if True, return without waiting for the job to be updated.

    Returns:
      A job.Job object.
    """
    messages = self.messages_module
    new_job = job.Job.New(self._client, job_ref.Parent().Name())
    new_job.name = job_ref.Name()
    parent = job_ref.Parent().RelativeName()
    for config_change in config_changes:
      new_job = config_change.Adjust(new_job)
    create_request = messages.RunNamespacesJobsCreateRequest(
        job=new_job.Message(), parent=parent
    )
    with metrics.RecordDuration(metric_names.CREATE_JOB):
      try:
        created_job = job.Job(
            self._client.namespaces_jobs.Create(create_request), messages
        )
      except api_exceptions.HttpConflictError:
        raise serverless_exceptions.DeploymentFailedError(
            'Job [{}] already exists.'.format(job_ref.Name())
        )

    if not asyn:
      getter = functools.partial(self.GetJob, job_ref)
      poller = op_pollers.ConditionPoller(getter, tracker)
      self.WaitForCondition(poller)
      created_job = poller.GetResource()

    return created_job

  def UpdateJob(self, job_ref, config_changes, tracker=None, asyn=False):
    """Update an existing Cloud Run Job.

    Args:
      job_ref: Resource, the job to update.
      config_changes: list, objects that implement Adjust().
      tracker: StagedProgressTracker, to report on the progress of updating.
      asyn: bool, if True, return without waiting for the job to be updated.

    Returns:
      A job.Job object.
    """
    messages = self.messages_module
    update_job = self.GetJob(job_ref)
    if update_job is None:
      raise serverless_exceptions.JobNotFoundError(
          'Job [{}] could not be found.'.format(job_ref.Name())
      )
    for config_change in config_changes:
      update_job = config_change.Adjust(update_job)
    replace_request = messages.RunNamespacesJobsReplaceJobRequest(
        job=update_job.Message(), name=job_ref.RelativeName()
    )
    with metrics.RecordDuration(metric_names.UPDATE_JOB):
      returned_job = job.Job(
          self._client.namespaces_jobs.ReplaceJob(replace_request), messages
      )

    if not asyn:
      getter = functools.partial(self.GetJob, job_ref)
      poller = op_pollers.ConditionPoller(getter, tracker)
      self.WaitForCondition(poller)
      returned_job = poller.GetResource()

    return returned_job

  def RunJob(
      self,
      job_ref,
      tracker=None,
      wait=False,
      asyn=False,
      release_track=None,
      overrides=None,
  ):
    """Run a Cloud Run Job, creating an Execution.

    Args:
      job_ref: Resource, the job to run
      tracker: StagedProgressTracker, to report on the progress of running
      wait: boolean, True to wait until the job is complete
      asyn: bool, if True, return without waiting for anything
      release_track: ReleaseTrack, the release track of a command calling this
      overrides: ExecutionOverrides to be applied for this run of a job

    Returns:
      An Execution Resource in its state when RunJob returns.
    """
    messages = self.messages_module
    run_job_request = messages.RunJobRequest()
    if overrides:
      run_job_request.overrides = overrides
    run_request = messages.RunNamespacesJobsRunRequest(
        name=job_ref.RelativeName(), runJobRequest=run_job_request
    )
    with metrics.RecordDuration(metric_names.RUN_JOB):
      try:
        execution_message = self._client.namespaces_jobs.Run(run_request)
      except api_exceptions.HttpError as e:
        if e.status_code == 429:  # resource exhausted
          raise serverless_exceptions.DeploymentFailedError(
              'Resource exhausted error. This may mean that '
              'too many executions are already running. Please wait until one '
              'completes before creating a new one.'
          )
        raise e
    if asyn:
      return execution.Execution(execution_message, messages)

    execution_ref = self._registry.Parse(
        execution_message.metadata.name,
        params={'namespacesId': execution_message.metadata.namespace},
        collection='run.namespaces.executions',
    )
    getter = functools.partial(self.GetExecution, execution_ref)
    terminal_condition = (
        execution.COMPLETED_CONDITION if wait else execution.STARTED_CONDITION
    )
    ex = self.GetExecution(execution_ref)
    for msg in run_condition.GetNonTerminalMessages(
        ex.conditions, ignore_retry=True
    ):
      tracker.AddWarning(msg)
    poller = op_pollers.ExecutionConditionPoller(
        getter,
        tracker,
        terminal_condition,
        dependencies=stages.ExecutionDependencies(),
    )
    try:
      self.WaitForCondition(poller, None if wait else 0)
    except serverless_exceptions.ExecutionFailedError:
      raise serverless_exceptions.ExecutionFailedError(
          'The execution failed.'
          + messages_util.GetExecutionCreatedMessage(release_track, ex)
      )
    return self.GetExecution(execution_ref)

  def GetJob(self, job_ref):
    """Return the relevant Job from the server, or None if 404."""
    messages = self.messages_module
    get_request = messages.RunNamespacesJobsGetRequest(
        name=job_ref.RelativeName()
    )

    try:
      with metrics.RecordDuration(metric_names.GET_JOB):
        job_response = self._client.namespaces_jobs.Get(get_request)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

    return job.Job(job_response, messages)

  def GetTask(self, task_ref):
    """Return the relevant Task from the server, or None if 404."""
    messages = self.messages_module
    get_request = messages.RunNamespacesTasksGetRequest(
        name=task_ref.RelativeName()
    )

    try:
      with metrics.RecordDuration(metric_names.GET_TASK):
        task_response = self._client.namespaces_tasks.Get(get_request)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

    return task.Task(task_response, messages)

  def GetExecution(self, execution_ref):
    """Return the relevant Execution from the server, or None if 404."""
    messages = self.messages_module
    get_request = messages.RunNamespacesExecutionsGetRequest(
        name=execution_ref.RelativeName()
    )

    try:
      with metrics.RecordDuration(metric_names.GET_EXECUTION):
        execution_response = self._client.namespaces_executions.Get(get_request)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)
    except api_exceptions.HttpNotFoundError:
      return None

    return execution.Execution(execution_response, messages)

  def ListJobs(self, namespace_ref):
    """Returns all jobs in the namespace."""
    messages = self.messages_module
    request = messages.RunNamespacesJobsListRequest(
        parent=namespace_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.LIST_JOBS):
        response = self._client.namespaces_jobs.List(request)
    except api_exceptions.InvalidDataFromServerError as e:
      serverless_exceptions.MaybeRaiseCustomFieldMismatch(e)

    return [job.Job(item, messages) for item in response.items]

  def DeleteJob(self, job_ref):
    """Delete the provided Job.

    Args:
      job_ref: Resource, a reference to the Job to delete

    Raises:
      JobNotFoundError: if provided job is not found.
    """
    messages = self.messages_module
    request = messages.RunNamespacesJobsDeleteRequest(
        name=job_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.DELETE_JOB):
        self._client.namespaces_jobs.Delete(request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.JobNotFoundError(
          'Job [{}] could not be found.'.format(job_ref.Name())
      )

  def DeleteExecution(self, execution_ref):
    """Delete the provided Execution.

    Args:
      execution_ref: Resource, a reference to the Execution to delete

    Raises:
      ExecutionNotFoundError: if provided Execution is not found.
    """
    messages = self.messages_module
    request = messages.RunNamespacesExecutionsDeleteRequest(
        name=execution_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.DELETE_EXECUTION):
        self._client.namespaces_executions.Delete(request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.ExecutionNotFoundError(
          'Execution [{}] could not be found.'.format(execution_ref.Name())
      )

  def CancelExecution(self, execution_ref):
    """Cancel the provided Execution.

    Args:
      execution_ref: Resource, a reference to the Execution to cancel

    Raises:
      ExecutionNotFoundError: if provided Execution is not found.
    """
    messages = self.messages_module
    request = messages.RunNamespacesExecutionsCancelRequest(
        name=execution_ref.RelativeName()
    )
    try:
      with metrics.RecordDuration(metric_names.CANCEL_EXECUTION):
        self._client.namespaces_executions.Cancel(request)
    except api_exceptions.HttpNotFoundError:
      raise serverless_exceptions.ExecutionNotFoundError(
          'Execution [{}] could not be found.'.format(execution_ref.Name())
      )

  def _GetIamPolicy(self, service_name):
    """Gets the IAM policy for the service."""
    messages = self.messages_module
    request = messages.RunProjectsLocationsServicesGetIamPolicyRequest(
        resource=six.text_type(service_name)
    )
    response = self._op_client.projects_locations_services.GetIamPolicy(request)
    return response

  def AddOrRemoveIamPolicyBinding(
      self, service_ref, add_binding=True, member=None, role=None
  ):
    """Add or remove the given IAM policy binding to the provided service.

    If no members or role are provided, set the IAM policy to the current IAM
    policy. This is useful for checking whether the authenticated user has
    the appropriate permissions for setting policies.

    Args:
      service_ref: str, The service to which to add the IAM policy.
      add_binding: bool, Whether to add to or remove from the IAM policy.
      member: str, One of the users for which the binding applies.
      role: str, The role to grant the provided members.

    Returns:
      A google.iam.v1.TestIamPermissionsResponse.
    """
    messages = self.messages_module
    oneplatform_service = resource_name_conversion.K8sToOnePlatform(
        service_ref, self._region
    )
    policy = self._GetIamPolicy(oneplatform_service)
    # Don't modify bindings if not member or roles provided
    if member and role:
      if add_binding:
        iam_util.AddBindingToIamPolicy(messages.Binding, policy, member, role)
      elif iam_util.BindingInPolicy(policy, member, role):
        iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    request = messages.RunProjectsLocationsServicesSetIamPolicyRequest(
        resource=six.text_type(oneplatform_service),
        setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy),
    )
    result = self._op_client.projects_locations_services.SetIamPolicy(request)
    return result

  def CanSetIamPolicyBinding(self, service_ref):
    """Check if user has permission to set the iam policy on the service."""
    messages = self.messages_module
    oneplatform_service = resource_name_conversion.K8sToOnePlatform(
        service_ref, self._region
    )
    request = messages.RunProjectsLocationsServicesTestIamPermissionsRequest(
        resource=six.text_type(oneplatform_service),
        testIamPermissionsRequest=messages.TestIamPermissionsRequest(
            permissions=NEEDED_IAM_PERMISSIONS
        ),
    )
    response = self._client.projects_locations_services.TestIamPermissions(
        request
    )
    return set(NEEDED_IAM_PERMISSIONS).issubset(set(response.permissions))

  def _CreateRepository(self, tracker, repo_to_create, skip_activation_prompt):
    """Create an artifact repository."""
    tracker.StartStage(stages.CREATE_REPO)
    tracker.UpdateHeaderMessage('Creating Container Repository.')
    artifact_registry.CreateRepository(repo_to_create, skip_activation_prompt)
    tracker.CompleteStage(stages.CREATE_REPO)

  def ValidateConfigOverrides(self, job_ref, config_overrides):
    """Apply config changes to Job resource to validate.

    This is to replicate the same validation logic in `jobs/services update`.
    Override attempts with types (out of string literals, secrets,
    config maps) that are different from currently set value type will appear as
    errors in the console.

    Args:
      job_ref: Resource, job resource.
      config_overrides: Job configuration changes from Overrides
    """
    run_job = self.GetJob(job_ref)
    for override in config_overrides:
      run_job = override.Adjust(run_job)

  def GetExecutionOverrides(self, tasks, task_timeout, container_overrides):
    return self.messages_module.Overrides(
        containerOverrides=container_overrides,
        taskCount=tasks,
        timeoutSeconds=task_timeout,
    )

  def GetContainerOverrides(self, update_env_vars, args, clear_args):
    container_overrides = []
    env_vars = self._GetEnvVarList(update_env_vars)
    container_overrides.append(
        self.messages_module.ContainerOverride(
            args=args or [], env=env_vars, clearArgs=clear_args
        )
    )
    return container_overrides

  def _GetEnvVarList(self, env_vars):
    env_var_list = []
    if env_vars is not None:
      for name, value in env_vars.items():
        env_var_list.append(self.messages_module.EnvVar(name=name, value=value))
    return env_var_list
