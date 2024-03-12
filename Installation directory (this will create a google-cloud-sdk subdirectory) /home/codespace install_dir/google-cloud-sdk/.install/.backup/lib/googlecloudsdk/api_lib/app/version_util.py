# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Utilities for dealing with version resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import metric_names
from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core.util import retry
from googlecloudsdk.core.util import text
from googlecloudsdk.core.util import times
import six
from six.moves import map  # pylint: disable=redefined-builtin


class VersionValidationError(exceptions.Error):
  pass


class VersionsDeleteError(exceptions.Error):
  pass


class Version(object):
  """Value class representing a version resource.

  This wrapper around appengine_<API-version>_messages.Version is necessary
  because Versions don't have traffic split, project, or last_deployed_time as a
  datetime object.
  """

  # The smallest allowed traffic split is 1e-3. Because of floating point
  # peculiarities, we use 1e-4 as our max allowed epsilon when testing whether a
  # version is receiving all traffic.
  _ALL_TRAFFIC_EPSILON = 1e-4

  _RESOURCE_PATH_PARTS = 3  # project/service/version

  # This is the name in the Version resource from the API
  _VERSION_NAME_PATTERN = ('apps/(?P<project>.*)/'
                           'services/(?P<service>.*)/'
                           'versions/(?P<version>.*)')

  def __init__(self,
               project,
               service,
               version_id,
               traffic_split=None,
               last_deployed_time=None,
               environment=None,
               version_resource=None,
               service_account=None):
    self.project = project
    self.service = service
    self.id = version_id
    self.version = version_resource
    self.traffic_split = traffic_split
    self.last_deployed_time = last_deployed_time
    self.environment = environment
    self.service_account = service_account

  @classmethod
  def FromResourcePath(cls, path):
    parts = path.split('/')
    if not 0 < len(parts) <= cls._RESOURCE_PATH_PARTS:
      raise VersionValidationError('[{0}] is not a valid resource path. '
                                   'Expected <project>/<service>/<version>')

    parts = [None] * (cls._RESOURCE_PATH_PARTS - len(parts)) + parts
    return cls(*parts)

  @classmethod
  def FromVersionResource(cls, version, service):
    """Convert appengine_<API-version>_messages.Version into wrapped Version."""
    project, service_id, _ = re.match(cls._VERSION_NAME_PATTERN,
                                      version.name).groups()
    traffic_split = service and service.split.get(version.id, 0.0)
    last_deployed = None
    try:
      if version.createTime:
        last_deployed_dt = times.ParseDateTime(version.createTime).replace(
            microsecond=0)
        last_deployed = times.LocalizeDateTime(last_deployed_dt)
    except ValueError:
      pass
    if version.env == 'flexible':
      environment = env.FLEX
    elif version.vm:
      environment = env.MANAGED_VMS
    else:
      environment = env.STANDARD
    return cls(project, service_id, version.id, traffic_split=traffic_split,
               last_deployed_time=last_deployed, environment=environment,
               version_resource=version)

  def IsReceivingAllTraffic(self):
    return abs(self.traffic_split - 1.0) < self._ALL_TRAFFIC_EPSILON

  def GetVersionResource(self, api_client):
    """Attempts to load the Version resource for this version.

    Returns the cached Version resource if it exists. Otherwise, attempts to
    load it from the server. Errors are logged and ignored.

    Args:
      api_client: An AppengineApiClient.

    Returns:
      The Version resource, or None if it could not be loaded.
    """
    if not self.version:
      try:
        self.version = api_client.GetVersionResource(self.service, self.id)
        if not self.version:
          log.info('Failed to retrieve resource for version [{0}]'.format(self))
      except apitools_exceptions.Error as e:
        # Log and drop the exception so we don't introduce a new failure mode
        # into the app deployment flow. If we find this isn't happening very
        # often, we could choose to propagate the error.
        log.warning('Error retrieving Version resource [{0}]: {1}'
                    .format(six.text_type(self), six.text_type(e)))
    return self.version

  def __eq__(self, other):
    return (type(other) is Version and
            self.project == other.project and
            self.service == other.service and
            self.id == other.id)

  def __ne__(self, other):
    return not self == other

  def __cmp__(self, other):
    return cmp((self.project, self.service, self.id),
               (other.project, other.service, other.id))

  def __str__(self):
    return '{0}/{1}/{2}'.format(self.project, self.service, self.id)


def _ValidateServicesAreSubset(filtered_versions, all_versions):
  """Validate that each version in filtered_versions is also in all_versions.

  Args:
    filtered_versions: list of Version representing a filtered subset of
      all_versions.
    all_versions: list of Version representing all versions in the current
      project.

  Raises:
    VersionValidationError: If a service or version is not found.
  """
  for version in filtered_versions:
    if version.service not in [v.service for v in all_versions]:
      raise VersionValidationError(
          'Service [{0}] not found.'.format(version.service))
    if version not in all_versions:
      raise VersionValidationError(
          'Version [{0}/{1}] not found.'.format(version.service,
                                                version.id))


def ParseVersionResourcePaths(paths, project):
  """Parse the list of resource paths specifying versions.

  Args:
    paths: The list of resource paths by which to filter.
    project: The current project. Used for validation.

  Returns:
    list of Version

  Raises:
    VersionValidationError: If not all versions are valid resource paths for the
      current project.
  """
  versions = list(map(Version.FromResourcePath, paths))

  for version in versions:
    if not (version.project or version.service):
      raise VersionValidationError('If you provide a resource path as an '
                                   'argument, all arguments must be resource '
                                   'paths.')
    if version.project and version.project != project:
      raise VersionValidationError(
          'All versions must be in the current project.')
    version.project = project
  return versions


def GetMatchingVersions(all_versions, versions, service):
  """Return a list of versions to act on based on user arguments.

  Args:
    all_versions: list of Version representing all services in the project.
    versions: list of string, version names to filter for.
      If empty, match all versions.
    service: string or None, service name. If given, only match versions in the
      given service.

  Returns:
    list of matching Version

  Raises:
    VersionValidationError: If an improper combination of arguments is given.
  """
  filtered_versions = all_versions
  if service:
    if service not in [v.service for v in all_versions]:
      raise VersionValidationError('Service [{0}] not found.'.format(service))
    filtered_versions = [v for v in all_versions if v.service == service]

  if versions:
    filtered_versions = [v for v in filtered_versions if v.id in versions]

  return filtered_versions


def DeleteVersions(api_client, versions):
  """Delete the given version of the given services."""
  errors = {}
  for version in versions:
    version_path = '{0}/{1}'.format(version.service, version.id)
    try:
      operations_util.CallAndCollectOpErrors(
          api_client.DeleteVersion, version.service, version.id)
    except operations_util.MiscOperationError as err:
      errors[version_path] = six.text_type(err)

  if errors:
    printable_errors = {}
    for version_path, error_msg in errors.items():
      printable_errors[version_path] = '[{0}]: {1}'.format(version_path,
                                                           error_msg)
    raise VersionsDeleteError(
        'Issue deleting {0}: [{1}]\n\n'.format(
            text.Pluralize(len(printable_errors), 'version'),
            ', '.join(list(printable_errors.keys()))) +
        '\n\n'.join(list(printable_errors.values())))


def PromoteVersion(all_services, new_version, api_client, stop_previous_version,
                   wait_for_stop_version):
  """Promote the new version to receive all traffic.

  First starts the new version if it is not running.

  Additionally, stops the previous version if stop_previous_version is True and
  it is possible to stop the previous version.

  Args:
    all_services: {str, Service}, A mapping of service id to Service objects
      for all services in the app.
    new_version: Version, The version to promote.
    api_client: appengine_api_client.AppengineApiClient to use to make requests.
    stop_previous_version: bool, True to stop the previous version which was
      receiving all traffic, if any.
    wait_for_stop_version: bool, indicating whether to wait for stop operation
    to finish.
  """
  old_default_version = None
  if stop_previous_version:
    # Grab the list of versions before we promote, since we need to
    # figure out what the previous default version was
    old_default_version = _GetPreviousVersion(
        all_services, new_version, api_client)

  # If the new version is stopped, try to start it.
  new_version_resource = new_version.GetVersionResource(api_client)
  status_enum = api_client.messages.Version.ServingStatusValueValuesEnum
  if (new_version_resource and
      new_version_resource.servingStatus == status_enum.STOPPED):
    # start new version
    log.status.Print('Starting version [{0}] before promoting it.'
                     .format(new_version))
    api_client.StartVersion(new_version.service, new_version.id, block=True)

  _SetDefaultVersion(new_version, api_client)

  if old_default_version:
    _StopPreviousVersionIfApplies(old_default_version, api_client,
                                  wait_for_stop_version)


def GetUri(version):
  return version.version.versionUrl


def _GetPreviousVersion(all_services, new_version, api_client):
  """Get the previous default version of which new_version is replacing.

  If there is no such version, return None.

  Args:
    all_services: {str, Service}, A mapping of service id to Service objects
      for all services in the app.
    new_version: Version, The version to promote.
    api_client: appengine_api_client.AppengineApiClient, The client for talking
      to the App Engine Admin API.

  Returns:
    Version, The previous version or None.
  """
  service = all_services.get(new_version.service, None)
  if not service:
    return None
  for old_version in api_client.ListVersions([service]):
    # Make sure not to stop the just-deployed version!
    # This can happen with a new service, or with a deployment over
    # an existing version.
    if (old_version.IsReceivingAllTraffic() and
        old_version.id != new_version.id):
      return old_version


def _SetDefaultVersion(new_version, api_client):
  """Sets the given version as the default.

  Args:
    new_version: Version, The version to promote.
    api_client: appengine_api_client.AppengineApiClient to use to make requests.
  """
  metrics.CustomTimedEvent(metric_names.SET_DEFAULT_VERSION_API_START)
  # Retry it if we get a service not found error.
  def ShouldRetry(exc_type, unused_exc_value, unused_traceback, unused_state):
    return issubclass(exc_type, apitools_exceptions.HttpError)

  try:
    retryer = retry.Retryer(max_retrials=3, exponential_sleep_multiplier=2)
    retryer.RetryOnException(
        api_client.SetDefaultVersion, [new_version.service, new_version.id],
        should_retry_if=ShouldRetry, sleep_ms=1000)
  except retry.MaxRetrialsException as e:
    (unused_result, exc_info) = e.last_result
    if exc_info:
      exceptions.reraise(exc_info[1], tb=exc_info[2])
    else:
      # This shouldn't happen, but if we don't have the exception info for some
      # reason, just convert the MaxRetrialsException.
      raise exceptions.InternalError()
  metrics.CustomTimedEvent(metric_names.SET_DEFAULT_VERSION_API)


def _StopPreviousVersionIfApplies(old_default_version, api_client,
                                  wait_for_stop_version):
  """Stop the previous default version if applicable.

  Cases where a version will not be stopped:

  * If the previous default version is not serving, there is no need to stop it.
  * If the previous default version is an automatically scaled standard
    environment app, it cannot be stopped.

  Args:
    old_default_version: Version, The old default version to stop.
    api_client: appengine_api_client.AppengineApiClient to use to make requests.
    wait_for_stop_version: bool, indicating whether to wait for stop operation
    to finish.
  """
  version_object = old_default_version.version
  status_enum = api_client.messages.Version.ServingStatusValueValuesEnum
  if version_object.servingStatus != status_enum.SERVING:
    log.info(
        'Previous default version [{0}] not serving, so not stopping '
        'it.'.format(old_default_version))
    return
  is_standard = not (version_object.vm or version_object.env == 'flex' or
                     version_object.env == 'flexible')
  if (is_standard and not version_object.basicScaling and
      not version_object.manualScaling):
    log.info(
        'Previous default version [{0}] is an automatically scaled '
        'standard environment app, so not stopping it.'.format(
            old_default_version))
    return

  log.status.Print('Stopping version [{0}].'.format(old_default_version))
  try:
    # Block only if wait_for_stop_version is true.
    # Waiting for stop the previous version to finish adds a long time
    # (reports of 2.5 minutes) to deployment. The risk is that if we don't wait,
    # the operation might fail and leave an old version running. But the time
    # savings is substantial.
    operations_util.CallAndCollectOpErrors(
        api_client.StopVersion,
        service_name=old_default_version.service,
        version_id=old_default_version.id,
        block=wait_for_stop_version)
  except operations_util.MiscOperationError as err:
    log.warning('Error stopping version [{0}]: {1}'.format(old_default_version,
                                                           six.text_type(err)))
    log.warning('Version [{0}] is still running and you must stop or delete it '
                'yourself in order to turn it off. (If you do not, you may be '
                'charged.)'.format(old_default_version))
  else:
    if not wait_for_stop_version:
      # TODO(b/318248525): Switch to refer to `gcloud app operations wait` when
      # available
      log.status.Print(
          'Sent request to stop version [{0}]. This operation may take some time '
          'to complete. If you would like to verify that it succeeded, run:\n'
          '  $ gcloud app versions describe -s {0.service} {0.id}\n'
          'until it shows that the version has stopped.'.format(
              old_default_version))
