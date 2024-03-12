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
"""High-level client for interacting with the Cloud Build API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import time

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import logs as cloudbuild_logs
from googlecloudsdk.api_lib.util import requests
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from six.moves import range  # pylint: disable=redefined-builtin


_ERROR_FORMAT_STRING = ('Error Response:{status_code? [{?}]}'
                        '{status_message? {?}}{url?\n{?}}'
                        '{details?\n\nDetails:\n{?}}')


def GetBuildProp(build_op, prop_key, required=False):
  """Extract the value of a build's prop_key from a build operation.

  Args:
    build_op: A Google Cloud Builder build operation.
    prop_key: str, The property name.
    required: If True, raise an OperationError if prop_key isn't present.

  Returns:
    The corresponding build operation value indexed by prop_key.

  Raises:
    OperationError: The required prop_key was not found.
  """
  if build_op.metadata is not None:
    for prop in build_op.metadata.additionalProperties:
      if prop.key == 'build':
        for build_prop in prop.value.object_value.properties:
          if build_prop.key == prop_key:
            string_value = build_prop.value.string_value
            return string_value or build_prop.value
  if required:
    raise OperationError('Build operation does not contain required '
                         'property [{}]'.format(prop_key))


def _GetStatusFromOp(op):
  """Get the Cloud Build Status from an Operation object.

  The op.response field is supposed to have a copy of the build object; however,
  the wire JSON from the server doesn't get deserialized into an actual build
  object. Instead, it is stored as a generic ResponseValue object, so we have
  to root around a bit.

  Args:
    op: the Operation object from a CloudBuild build request.

  Returns:
    string status, likely "SUCCESS" or "ERROR".
  """
  if op.response and op.response.additionalProperties:
    for prop in op.response.additionalProperties:
      if prop.key == 'status':
        return prop.value.string_value
  return 'UNKNOWN'


class BuildFailedError(exceptions.Error):
  """Raised when a Google Cloud Builder build fails."""


class OperationTimeoutError(exceptions.Error):
  """Raised when an operation times out."""
  pass


class OperationError(exceptions.Error):
  """Raised when an operation contains an error."""
  pass


class CloudBuildClient(object):
  """High-level client for interacting with the Cloud Build API."""

  _RETRY_INTERVAL = 1
  _MAX_RETRIES = 60 * 60
  CLOUDBUILD_SUCCESS = 'SUCCESS'
  CLOUDBUILD_LOGFILE_FMT_STRING = 'log-{build_id}.txt'

  def __init__(self, client=None, messages=None):
    self.client = client or cloudbuild_util.GetClientInstance()
    self.messages = messages or cloudbuild_util.GetMessagesModule()

  def ExecuteCloudBuildAsync(self, build, project=None):
    """Execute a call to CloudBuild service and return the build operation.


    Args:
      build: Build object. The Build to execute.
      project: The project to execute, or None to use the current project
          property.

    Raises:
      BuildFailedError: when the build fails.

    Returns:
      build_op, an in-progress build operation.
    """
    if project is None:
      project = properties.VALUES.core.project.Get(required=True)

    build_op = self.client.projects_builds.Create(
        self.messages.CloudbuildProjectsBuildsCreateRequest(
            projectId=project,
            build=build,))
    return build_op

  def ExecuteCloudBuild(self, build, project=None):
    """Execute a call to CloudBuild service and wait for it to finish.


    Args:
      build: Build object. The Build to execute.
      project: The project to execute, or None to use the current project
          property.

    Raises:
      BuildFailedError: when the build fails.
    """

    build_op = self.ExecuteCloudBuildAsync(build, project)
    self.WaitAndStreamLogs(build_op)

  def WaitAndStreamLogs(self, build_op):
    """Wait for a Cloud Build to finish, streaming logs if possible."""
    build_id = GetBuildProp(build_op, 'id', required=True)
    logs_uri = GetBuildProp(build_op, 'logUrl')
    logs_bucket = GetBuildProp(build_op, 'logsBucket')
    log.status.Print(
        'Started cloud build [{build_id}].'.format(build_id=build_id))
    log_loc = 'in the Cloud Console.'
    log_tailer = None
    if logs_bucket:
      log_object = self.CLOUDBUILD_LOGFILE_FMT_STRING.format(build_id=build_id)
      log_tailer = cloudbuild_logs.GCSLogTailer(
          bucket=logs_bucket,
          obj=log_object)
      if logs_uri:
        log.status.Print('To see logs in the Cloud Console: ' + logs_uri)
        log_loc = 'at ' + logs_uri
      else:
        log.status.Print('Logs can be found in the Cloud Console.')

    callback = None
    if log_tailer:
      callback = log_tailer.Poll

    try:
      op = self.WaitForOperation(operation=build_op, retry_callback=callback)
    except OperationTimeoutError:
      log.debug('', exc_info=True)
      raise BuildFailedError('Cloud build timed out. Check logs ' + log_loc)

    # Poll the logs one final time to ensure we have everything. We know this
    # final poll will get the full log contents because GCS is strongly
    # consistent and Cloud Build waits for logs to finish pushing before
    # marking the build complete.
    if log_tailer:
      log_tailer.Poll(is_last=True)

    final_status = _GetStatusFromOp(op)
    if final_status != self.CLOUDBUILD_SUCCESS:
      message = requests.ExtractErrorMessage(
          encoding.MessageToPyValue(op.error))
      raise BuildFailedError('Cloud build failed. Check logs ' + log_loc
                             + ' Failure status: ' + final_status + ': '
                             + message)

  def WaitForOperation(self, operation, retry_callback=None):
    """Wait until the operation is complete or times out.

    This does not use the core api_lib.util.waiter because the cloud build logs
    serve as a progress tracker.

    Args:
      operation: The operation resource to wait on
      retry_callback: A callback to be executed before each retry, if desired.
    Returns:
      The operation resource when it has completed
    Raises:
      OperationTimeoutError: when the operation polling times out
    """

    completed_operation = self._PollUntilDone(operation, retry_callback)
    if not completed_operation:
      raise OperationTimeoutError(('Operation [{0}] timed out. This operation '
                                   'may still be underway.').format(
                                       operation.name))

    return completed_operation

  def _PollUntilDone(self, operation, retry_callback):
    """Polls the operation resource until it is complete or times out."""
    if operation.done:
      return operation

    request_type = self.client.operations.GetRequestType('Get')
    request = request_type(name=operation.name)

    for _ in range(self._MAX_RETRIES):
      operation = self.client.operations.Get(request)
      if operation.done:
        log.debug('Operation [{0}] complete. Result: {1}'.format(
            operation.name,
            json.dumps(encoding.MessageToDict(operation), indent=4)))
        return operation
      log.debug('Operation [{0}] not complete. Waiting {1}s.'.format(
          operation.name, self._RETRY_INTERVAL))
      time.sleep(self._RETRY_INTERVAL)
      if retry_callback is not None:
        retry_callback()

    return None
