# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Common utility functions for sql instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import os
import subprocess
import time

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import constants
from googlecloudsdk.api_lib.sql import exceptions as sql_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files as file_utils
import six


messages = apis.GetMessagesModule('sql', 'v1beta4')

_BASE_CLOUD_SQL_PROXY_ERROR = 'Failed to start the Cloud SQL Proxy'

_MYSQL_DATABASE_VERSION_PREFIX = 'MYSQL'
_POSTGRES_DATABASE_VERSION_PREFIX = 'POSTGRES'
_SQLSERVER_DATABASE_VERSION_PREFIX = 'SQLSERVER'


class DatabaseInstancePresentation(object):
  """Represents a DatabaseInstance message that is modified for user visibility."""

  def __init__(self, orig):
    for field in orig.all_fields():
      if field.name == 'state':
        if orig.settings and orig.settings.activationPolicy == messages.Settings.ActivationPolicyValueValuesEnum.NEVER:
          self.state = 'STOPPED'
        else:
          self.state = orig.state
      else:
        value = getattr(orig, field.name)
        if value is not None and not (isinstance(value, list) and not value):
          if field.name in ['currentDiskSize', 'maxDiskSize']:
            setattr(self, field.name, six.text_type(value))
          else:
            setattr(self, field.name, value)

  def __eq__(self, other):
    """Overrides the default implementation by checking attribute dicts."""
    if isinstance(other, DatabaseInstancePresentation):
      return self.__dict__ == other.__dict__
    return False

  def __ne__(self, other):
    """Overrides the default implementation (only needed for Python 2)."""
    return not self.__eq__(other)


def GetRegionFromZone(gce_zone):
  """Parses and returns the region string from the gce_zone string."""
  zone_components = gce_zone.split('-')
  # The region is all but the last component of the zone.
  return '-'.join(zone_components[:-1])


def _IsCloudSqlProxyPresentInSdkBin(cloud_sql_proxy_path):
  """Checks if cloud_sql_proxy_path binary is present in cloud sdk bin."""
  return (os.path.exists(cloud_sql_proxy_path) and
          os.access(cloud_sql_proxy_path, os.X_OK))


def _GetCloudSqlProxyPath():
  """Determines the path to the cloud_sql_proxy binary."""
  sdk_bin_path = config.Paths().sdk_bin_path

  if sdk_bin_path:
    # Validate if the cloud_sql_proxy binary present in Cloud SDK bin repository
    # and it has access for invoking user,
    # otherwise look for it in PATH
    cloud_sql_proxy_path = os.path.join(sdk_bin_path, 'cloud_sql_proxy')
    if _IsCloudSqlProxyPresentInSdkBin(cloud_sql_proxy_path):
      return cloud_sql_proxy_path

  # Check if cloud_sql_proxy is located on the PATH.
  proxy_path = file_utils.FindExecutableOnPath('cloud_sql_proxy')
  if proxy_path:
    log.debug('Using cloud_sql_proxy found at [{path}]'.format(path=proxy_path))
    return proxy_path
  else:
    raise sql_exceptions.SqlProxyNotFound(
        'A Cloud SQL Proxy SDK root could not be found, or access is denied.'
        'Please check your installation.')


def _RaiseProxyError(error_msg=None):
  message = '{}.'.format(_BASE_CLOUD_SQL_PROXY_ERROR)
  if error_msg:
    message = '{}: {}'.format(_BASE_CLOUD_SQL_PROXY_ERROR, error_msg)
  raise sql_exceptions.CloudSqlProxyError(message)


def _ReadLineFromStderr(proxy_process):
  """Reads and returns the next line from the proxy stderr stream."""
  return encoding.Decode(proxy_process.stderr.readline())


def _WaitForProxyToStart(proxy_process, port, seconds_to_timeout):
  """Wait for the proxy to be ready for connections, then return proxy_process.

  Args:
    proxy_process: Process, the process corresponding to the Cloud SQL Proxy.
    port: int, the port that the proxy was started on.
    seconds_to_timeout: Seconds to wait before timing out.

  Returns:
    The Process object corresponding to the Cloud SQL Proxy.
  """

  total_wait_seconds = 0
  seconds_to_sleep = 0.2
  while proxy_process.poll() is None:
    line = _ReadLineFromStderr(proxy_process)
    while line:
      log.status.write(line)
      if constants.PROXY_ADDRESS_IN_USE_ERROR in line:
        _RaiseProxyError(
            'Port already in use. Exit the process running on port {} or try '
            'connecting again on a different port.'.format(port))
      elif constants.PROXY_READY_FOR_CONNECTIONS_MSG in line:
        # The proxy is ready to go, so stop polling!
        return proxy_process
      line = _ReadLineFromStderr(proxy_process)

    # If we've been waiting past the timeout, throw an error.
    if total_wait_seconds >= seconds_to_timeout:
      _RaiseProxyError('Timed out.')

    # Keep polling on the proxy output until relevant lines are found.
    total_wait_seconds += seconds_to_sleep
    time.sleep(seconds_to_sleep)

  # If we've reached this point, the proxy process exited unexpectedly.
  _RaiseProxyError()


def StartCloudSqlProxy(instance, port, seconds_to_timeout=10):
  """Starts the Cloud SQL Proxy for instance on the given port.

  Args:
    instance: The instance to start the proxy for.
    port: The port to bind the proxy to.
    seconds_to_timeout: Seconds to wait before timing out.

  Returns:
    The Process object corresponding to the Cloud SQL Proxy.

  Raises:
    CloudSqlProxyError: An error starting the Cloud SQL Proxy.
    SqlProxyNotFound: An error finding a Cloud SQL Proxy installation.
  """
  command_path = _GetCloudSqlProxyPath()

  # Specify the instance and port to connect with.
  args = ['-instances', '{}=tcp:{}'.format(instance.connectionName, port)]
  # Specify the credentials.
  account = properties.VALUES.core.account.Get(required=True)
  args += ['-credential_file', config.Paths().LegacyCredentialsAdcPath(account)]
  proxy_args = execution_utils.ArgsForExecutableTool(command_path, *args)
  log.status.write(
      'Starting Cloud SQL Proxy: [{args}]]\n'.format(args=' '.join(proxy_args)))

  try:
    proxy_process = subprocess.Popen(
        proxy_args,
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE)
  except EnvironmentError as e:
    if e.errno == errno.ENOENT:
      # We are trying to catch here the 'file not found error', so that a proper
      # message can be sent to the user with installation help.
      raise sql_exceptions.CloudSqlProxyError(
          'Failed to start Cloud SQL Proxy. Please make sure it is available in the PATH [{}]. '
          'Learn more about installing the Cloud SQL Proxy here: '
          'https://cloud.google.com/sql/docs/mysql/connect-admin-proxy#install. '
          'If you would like to report this issue, please run the following command: '
          'gcloud feedback'.format(command_path))
    # Else raise the EnvironmentError.
    raise

  return _WaitForProxyToStart(proxy_process, port, seconds_to_timeout)


def IsInstanceV2(sql_messages, instance):
  """Returns a boolean indicating if the database instance is second gen."""
  return instance.backendType == sql_messages.DatabaseInstance.BackendTypeValueValuesEnum.SECOND_GEN


# TODO(b/73648377): Factor out static methods into module-level functions.
class _BaseInstances(object):
  """Common utility functions for sql instances."""

  @staticmethod
  def GetDatabaseInstances(limit=None, batch_size=None):
    """Gets SQL instances in a given project.

    Modifies current state of an individual instance to 'STOPPED' if
    activationPolicy is 'NEVER'.

    Args:
      limit: int, The maximum number of records to yield. None if all available
          records should be yielded.
      batch_size: int, The number of items to retrieve per request.

    Returns:
      List of yielded DatabaseInstancePresentation instances.
    """

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages
    project_id = properties.VALUES.core.project.Get(required=True)

    params = {}
    if limit is not None:
      params['limit'] = limit

    # High default batch size to avoid excess polling on big projects.
    default_batch_size = 1000
    params['batch_size'] = (
        batch_size if batch_size is not None else default_batch_size)

    yielded = list_pager.YieldFromList(
        sql_client.instances,
        sql_messages.SqlInstancesListRequest(project=project_id), **params)

    def YieldInstancesWithAModifiedState():
      for result in yielded:
        yield DatabaseInstancePresentation(result)

    return YieldInstancesWithAModifiedState()

  @staticmethod
  def PrintAndConfirmAuthorizedNetworksOverwrite():
    console_io.PromptContinue(
        message='When adding a new IP address to authorized networks, '
        'make sure to also include any IP addresses that have already been '
        'authorized. Otherwise, they will be overwritten and de-authorized.',
        default=True,
        cancel_on_no=True)

  @staticmethod
  def PrintAndConfirmSimulatedMaintenanceEvent():
    console_io.PromptContinue(
        message='This request will trigger a simulated maintenance event '
        'and will not change the maintenance version on the instance. Downtime '
        'will occur on the instance.',
        default=False,
        cancel_on_no=True)

  @staticmethod
  def IsMysqlDatabaseVersion(database_version):
    """Returns a boolean indicating if the database version is MySQL."""
    return database_version.name.startswith(_MYSQL_DATABASE_VERSION_PREFIX)

  @staticmethod
  def IsPostgresDatabaseVersion(database_version):
    """Returns a boolean indicating if the database version is Postgres."""
    return database_version.name.startswith(_POSTGRES_DATABASE_VERSION_PREFIX)

  @staticmethod
  def IsSqlServerDatabaseVersion(database_version):
    """Returns a boolean indicating if the database version is SQL Server."""
    return database_version.name.startswith(_SQLSERVER_DATABASE_VERSION_PREFIX)


class InstancesV1Beta4(_BaseInstances):
  """Common utility functions for sql instances V1Beta4."""

  @staticmethod
  def SetProjectAndInstanceFromRef(instance_resource, instance_ref):
    instance_resource.project = instance_ref.project
    instance_resource.name = instance_ref.instance

  @staticmethod
  def AddBackupConfigToSettings(settings, backup_config):
    settings.backupConfiguration = backup_config
