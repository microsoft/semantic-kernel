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
"""Common utilities for the gcloud dataproc tool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import hashlib
import json
import os
import subprocess
import tempfile
import time
import uuid
from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import retry

import six

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), 'schemas')


def FormatRpcError(error):
  """Returns a printable representation of a failed Google API's status.proto.

  Args:
    error: the failed Status to print.

  Returns:
    A ready-to-print string representation of the error.
  """
  log.debug('Error:\n' + encoding.MessageToJson(error))
  return error.message


def WaitForResourceDeletion(request_method,
                            resource_ref,
                            message,
                            timeout_s=60,
                            poll_period_s=5):
  """Poll Dataproc resource until it no longer exists."""
  with progress_tracker.ProgressTracker(message, autotick=True):
    start_time = time.time()
    while timeout_s > (time.time() - start_time):
      try:
        request_method(resource_ref)
      except apitools_exceptions.HttpNotFoundError:
        # Object deleted
        return
      except apitools_exceptions.HttpError as error:
        log.debug('Get request for [{0}] failed:\n{1}', resource_ref, error)

        # Do not retry on 4xx errors
        if IsClientHttpException(error):
          raise
      time.sleep(poll_period_s)
  raise exceptions.OperationTimeoutError(
      'Deleting resource [{0}] timed out.'.format(resource_ref))


def GetUniqueId():
  return uuid.uuid4().hex


class Bunch(object):
  """Class that converts a dictionary to javascript like object.

  For example:
      Bunch({'a': {'b': {'c': 0}}}).a.b.c == 0
  """

  def __init__(self, dictionary):
    for key, value in six.iteritems(dictionary):
      if isinstance(value, dict):
        value = Bunch(value)
      self.__dict__[key] = value


def AddJvmDriverFlags(parser):
  parser.add_argument(
      '--jar',
      dest='main_jar',
      help='The HCFS URI of jar file containing the driver jar.')
  parser.add_argument(
      '--class',
      dest='main_class',
      help=('The class containing the main method of the driver. Must be in a'
            ' provided jar or jar that is already on the classpath'))


def IsClientHttpException(http_exception):
  """Returns true if the http exception given is an HTTP 4xx error."""
  return http_exception.status_code >= 400 and http_exception.status_code < 500


# TODO(b/36056506): Use api_lib.utils.waiter
def WaitForOperation(dataproc, operation, message, timeout_s, poll_period_s=5):
  """Poll dataproc Operation until its status is done or timeout reached.

  Args:
    dataproc: wrapper for Dataproc messages, resources, and client
    operation: Operation, message of the operation to be polled.
    message: str, message to display to user while polling.
    timeout_s: number, seconds to poll with retries before timing out.
    poll_period_s: number, delay in seconds between requests.

  Returns:
    Operation: the return value of the last successful operations.get
    request.

  Raises:
    OperationError: if the operation times out or finishes with an error.
  """
  request = dataproc.messages.DataprocProjectsRegionsOperationsGetRequest(
      name=operation.name)
  log.status.Print('Waiting on operation [{0}].'.format(operation.name))
  start_time = time.time()
  warnings_so_far = 0
  is_tty = console_io.IsInteractive(error=True)
  tracker_separator = '\n' if is_tty else ''

  def _LogWarnings(warnings):
    new_warnings = warnings[warnings_so_far:]
    if new_warnings:
      # Drop a line to print nicely with the progress tracker.
      log.err.write(tracker_separator)
      for warning in new_warnings:
        log.warning(warning)

  with progress_tracker.ProgressTracker(message, autotick=True):
    while timeout_s > (time.time() - start_time):
      try:
        operation = dataproc.client.projects_regions_operations.Get(request)
        metadata = ParseOperationJsonMetadata(
            operation.metadata, dataproc.messages.ClusterOperationMetadata)
        _LogWarnings(metadata.warnings)
        warnings_so_far = len(metadata.warnings)
        if operation.done:
          break
      except apitools_exceptions.HttpError as http_exception:
        # Do not retry on 4xx errors.
        if IsClientHttpException(http_exception):
          raise
      time.sleep(poll_period_s)
  metadata = ParseOperationJsonMetadata(
      operation.metadata, dataproc.messages.ClusterOperationMetadata)
  _LogWarnings(metadata.warnings)
  if not operation.done:
    raise exceptions.OperationTimeoutError('Operation [{0}] timed out.'.format(
        operation.name))
  elif operation.error:
    raise exceptions.OperationError('Operation [{0}] failed: {1}.'.format(
        operation.name, FormatRpcError(operation.error)))

  log.info('Operation [%s] finished after %.3f seconds', operation.name,
           (time.time() - start_time))
  return operation


def PrintWorkflowMetadata(metadata, status, operations, errors):
  """Print workflow and job status for the running workflow template.

  This method will detect any changes of state in the latest metadata and print
  all the new states in a workflow template.

  For example:
    Workflow template template-name RUNNING
    Creating cluster: Operation ID create-id.
    Job ID job-id-1 RUNNING
    Job ID job-id-1 COMPLETED
    Deleting cluster: Operation ID delete-id.
    Workflow template template-name DONE

  Args:
    metadata: Dataproc WorkflowMetadata message object, contains the latest
      states of a workflow template.
    status: Dictionary, stores all jobs' status in the current workflow
      template, as well as the status of the overarching workflow.
    operations: Dictionary, stores cluster operation status for the workflow
      template.
    errors: Dictionary, stores errors from the current workflow template.
  """
  # Key chosen to avoid collision with job ids, which are at least 3 characters.
  template_key = 'wt'
  if template_key not in status or metadata.state != status[template_key]:
    if metadata.template is not None:
      log.status.Print('WorkflowTemplate [{0}] {1}'.format(
          metadata.template, metadata.state))
    else:
      # Workflows instantiated inline do not store an id in their metadata.
      log.status.Print('WorkflowTemplate {0}'.format(metadata.state))
    status[template_key] = metadata.state
  if metadata.createCluster != operations['createCluster']:
    if hasattr(metadata.createCluster,
               'error') and metadata.createCluster.error is not None:
      log.status.Print(metadata.createCluster.error)
    elif hasattr(metadata.createCluster,
                 'done') and metadata.createCluster.done is not None:
      log.status.Print('Created cluster: {0}.'.format(metadata.clusterName))
    elif hasattr(
        metadata.createCluster,
        'operationId') and metadata.createCluster.operationId is not None:
      log.status.Print('Creating cluster: Operation ID [{0}].'.format(
          metadata.createCluster.operationId))
    operations['createCluster'] = metadata.createCluster
  if hasattr(metadata.graph, 'nodes'):
    for node in metadata.graph.nodes:
      if not node.jobId:
        continue
      if node.jobId not in status or status[node.jobId] != node.state:
        log.status.Print('Job ID {0} {1}'.format(node.jobId, node.state))
        status[node.jobId] = node.state
      if node.error and (node.jobId not in errors or
                         errors[node.jobId] != node.error):
        log.status.Print('Job ID {0} error: {1}'.format(node.jobId, node.error))
        errors[node.jobId] = node.error
  if metadata.deleteCluster != operations['deleteCluster']:
    if hasattr(metadata.deleteCluster,
               'error') and metadata.deleteCluster.error is not None:
      log.status.Print(metadata.deleteCluster.error)
    elif hasattr(metadata.deleteCluster,
                 'done') and metadata.deleteCluster.done is not None:
      log.status.Print('Deleted cluster: {0}.'.format(metadata.clusterName))
    elif hasattr(
        metadata.deleteCluster,
        'operationId') and metadata.deleteCluster.operationId is not None:
      log.status.Print('Deleting cluster: Operation ID [{0}].'.format(
          metadata.deleteCluster.operationId))
    operations['deleteCluster'] = metadata.deleteCluster


# TODO(b/36056506): Use api_lib.utils.waiter
def WaitForWorkflowTemplateOperation(dataproc,
                                     operation,
                                     timeout_s=None,
                                     poll_period_s=5):
  """Poll dataproc Operation until its status is done or timeout reached.

  Args:
    dataproc: wrapper for Dataproc messages, resources, and client
    operation: Operation, message of the operation to be polled.
    timeout_s: number, seconds to poll with retries before timing out.
    poll_period_s: number, delay in seconds between requests.

  Returns:
    Operation: the return value of the last successful operations.get
    request.

  Raises:
    OperationError: if the operation times out or finishes with an error.
  """
  request = dataproc.messages.DataprocProjectsRegionsOperationsGetRequest(
      name=operation.name)
  log.status.Print('Waiting on operation [{0}].'.format(operation.name))
  start_time = time.time()
  operations = {'createCluster': None, 'deleteCluster': None}
  status = {}
  errors = {}

  # If no timeout is specified, poll forever.
  while timeout_s is None or timeout_s > (time.time() - start_time):
    try:
      operation = dataproc.client.projects_regions_operations.Get(request)
      metadata = ParseOperationJsonMetadata(operation.metadata,
                                            dataproc.messages.WorkflowMetadata)

      PrintWorkflowMetadata(metadata, status, operations, errors)
      if operation.done:
        break
    except apitools_exceptions.HttpError as http_exception:
      # Do not retry on 4xx errors.
      if IsClientHttpException(http_exception):
        raise
    time.sleep(poll_period_s)
  metadata = ParseOperationJsonMetadata(operation.metadata,
                                        dataproc.messages.WorkflowMetadata)

  if not operation.done:
    raise exceptions.OperationTimeoutError('Operation [{0}] timed out.'.format(
        operation.name))
  elif operation.error:
    raise exceptions.OperationError('Operation [{0}] failed: {1}.'.format(
        operation.name, FormatRpcError(operation.error)))
  for op in ['createCluster', 'deleteCluster']:
    if op in operations and operations[op] is not None and operations[op].error:
      raise exceptions.OperationError('Operation [{0}] failed: {1}.'.format(
          operations[op].operationId, operations[op].error))

  log.info('Operation [%s] finished after %.3f seconds', operation.name,
           (time.time() - start_time))
  return operation


class NoOpProgressDisplay(object):
  """For use in place of a ProgressTracker in a 'with' block."""

  def __enter__(self):
    pass

  def __exit__(self, *unused_args):
    pass


def WaitForJobTermination(dataproc,
                          job,
                          job_ref,
                          message,
                          goal_state,
                          error_state=None,
                          stream_driver_log=False,
                          log_poll_period_s=1,
                          dataproc_poll_period_s=10,
                          timeout_s=None):
  """Poll dataproc Job until its status is terminal or timeout reached.

  Args:
    dataproc: wrapper for dataproc resources, client and messages
    job: The job to wait to finish.
    job_ref: Parsed dataproc.projects.regions.jobs resource containing a
      projectId, region, and jobId.
    message: str, message to display to user while polling.
    goal_state: JobStatus.StateValueValuesEnum, the state to define success
    error_state: JobStatus.StateValueValuesEnum, the state to define failure
    stream_driver_log: bool, Whether to show the Job's driver's output.
    log_poll_period_s: number, delay in seconds between checking on the log.
    dataproc_poll_period_s: number, delay in seconds between requests to the
      Dataproc API.
    timeout_s: number, time out for job completion. None means no timeout.

  Returns:
    Job: the return value of the last successful jobs.get request.

  Raises:
    JobError: if the job finishes with an error.
  """
  request = dataproc.messages.DataprocProjectsRegionsJobsGetRequest(
      projectId=job_ref.projectId, region=job_ref.region, jobId=job_ref.jobId)
  driver_log_stream = None
  last_job_poll_time = 0
  job_complete = False
  wait_display = None
  driver_output_uri = None

  def ReadDriverLogIfPresent():
    if driver_log_stream and driver_log_stream.open:
      # TODO(b/36049794): Don't read all output.
      driver_log_stream.ReadIntoWritable(log.err)

  def PrintEqualsLine():
    attr = console_attr.GetConsoleAttr()
    log.err.Print('=' * attr.GetTermSize()[0])

  if stream_driver_log:
    log.status.Print('Waiting for job output...')
    wait_display = NoOpProgressDisplay()
  else:
    wait_display = progress_tracker.ProgressTracker(message, autotick=True)
  start_time = now = time.time()
  with wait_display:
    while not timeout_s or timeout_s > (now - start_time):
      # Poll logs first to see if it closed.
      ReadDriverLogIfPresent()
      log_stream_closed = driver_log_stream and not driver_log_stream.open
      if (not job_complete and
          job.status.state in dataproc.terminal_job_states):
        job_complete = True
        # Wait an 10s to get trailing output.
        timeout_s = now - start_time + 10

      if job_complete and (not stream_driver_log or log_stream_closed):
        # Nothing left to wait for
        break

      regular_job_poll = (
          not job_complete
          # Poll less frequently on dataproc API
          and now >= last_job_poll_time + dataproc_poll_period_s)
      # Poll at regular frequency before output has streamed and after it has
      # finished.
      expecting_output_stream = stream_driver_log and not driver_log_stream
      expecting_job_done = not job_complete and log_stream_closed
      if regular_job_poll or expecting_output_stream or expecting_job_done:
        last_job_poll_time = now
        try:
          job = dataproc.client.projects_regions_jobs.Get(request)
        except apitools_exceptions.HttpError as error:
          log.warning('GetJob failed:\n{}'.format(six.text_type(error)))
          # Do not retry on 4xx errors.
          if IsClientHttpException(error):
            raise
        if (stream_driver_log and job.driverOutputResourceUri and
            job.driverOutputResourceUri != driver_output_uri):
          if driver_output_uri:
            PrintEqualsLine()
            log.warning("Job attempt failed. Streaming new attempt's output.")
            PrintEqualsLine()
          driver_output_uri = job.driverOutputResourceUri
          driver_log_stream = storage_helpers.StorageObjectSeriesStream(
              job.driverOutputResourceUri)
      time.sleep(log_poll_period_s)
      now = time.time()

  state = job.status.state

  # goal_state and error_state will always be terminal
  if state in dataproc.terminal_job_states:
    if stream_driver_log:
      if not driver_log_stream:
        log.warning('Expected job output not found.')
      elif driver_log_stream.open:
        log.warning('Job terminated, but output did not finish streaming.')
    if state is goal_state:
      return job
    if error_state and state is error_state:
      if job.status.details:
        raise exceptions.JobError('Job [{0}] failed with error:\n{1}'.format(
            job_ref.jobId, job.status.details))
      raise exceptions.JobError('Job [{0}] failed.'.format(job_ref.jobId))
    if job.status.details:
      log.info('Details:\n' + job.status.details)
    raise exceptions.JobError(
        'Job [{0}] entered state [{1}] while waiting for [{2}].'.format(
            job_ref.jobId, state, goal_state))
  raise exceptions.JobTimeoutError(
      'Job [{0}] timed out while in state [{1}].'.format(job_ref.jobId, state))


# This replicates the fallthrough logic of flags._RegionAttributeConfig.
# It is necessary in cases like the --region flag where we are not parsing
# ResourceSpecs
def ResolveRegion():
  return properties.VALUES.dataproc.region.GetOrFail()


# This replicates the fallthrough logic of flags._LocationAttributeConfig.
# It is necessary in cases like the --location flag where we are not parsing
# ResourceSpecs
def ResolveLocation():
  return properties.VALUES.dataproc.location.GetOrFail()


# You probably want to use flags.AddClusterResourceArgument instead.
# If calling this method, you *must* have called flags.AddRegionFlag first to
# ensure a --region flag is stored into properties, which ResolveRegion
# depends on. This is also mutually incompatible with any usage of args.CONCEPTS
# which use --region as a resource attribute.
def ParseCluster(name, dataproc):
  ref = dataproc.resources.Parse(
      name,
      params={
          'region': ResolveRegion,
          'projectId': properties.VALUES.core.project.GetOrFail
      },
      collection='dataproc.projects.regions.clusters')
  return ref


# You probably want to use flags.AddJobResourceArgument instead.
# If calling this method, you *must* have called flags.AddRegionFlag first to
# ensure a --region flag is stored into properties, which ResolveRegion
# depends on. This is also mutually incompatible with any usage of args.CONCEPTS
# which use --region as a resource attribute.
def ParseJob(job_id, dataproc):
  ref = dataproc.resources.Parse(
      job_id,
      params={
          'region': ResolveRegion,
          'projectId': properties.VALUES.core.project.GetOrFail
      },
      collection='dataproc.projects.regions.jobs')
  return ref


def ParseOperationJsonMetadata(metadata_value, metadata_type):
  """Returns an Operation message for a metadata value."""
  if not metadata_value:
    return metadata_type()
  return encoding.JsonToMessage(metadata_type,
                                encoding.MessageToJson(metadata_value))


# Used in bizarre scenarios where we want a qualified region rather than a
# short name
def ParseRegion(dataproc):
  ref = dataproc.resources.Parse(
      None,
      params={
          'regionId': ResolveRegion,
          'projectId': properties.VALUES.core.project.GetOrFail
      },
      collection='dataproc.projects.regions')
  return ref


# Get dataproc.projects.locations resource
def ParseProjectsLocations(dataproc):
  ref = dataproc.resources.Parse(
      None,
      params={
          'locationsId': ResolveRegion,
          'projectsId': properties.VALUES.core.project.GetOrFail
      },
      collection='dataproc.projects.locations')
  return ref


# Get dataproc.projects.locations resource
# This can be merged with ParseProjectsLocations() once we have migrated batches
# from `region` to `location`.
def ParseProjectsLocationsForSession(dataproc):
  ref = dataproc.resources.Parse(
      None,
      params={
          'locationsId': ResolveLocation(),
          'projectsId': properties.VALUES.core.project.GetOrFail
      },
      collection='dataproc.projects.locations')
  return ref


def ReadAutoscalingPolicy(dataproc, policy_id, policy_file_name=None):
  """Returns autoscaling policy read from YAML file.

  Args:
    dataproc: wrapper for dataproc resources, client and messages.
    policy_id: The autoscaling policy id (last piece of the resource name).
    policy_file_name: if set, location of the YAML file to read from. Otherwise,
      reads from stdin.

  Raises:
    argparse.ArgumentError if duration formats are invalid or out of bounds.
  """
  data = console_io.ReadFromFileOrStdin(policy_file_name or '-', binary=False)
  policy = export_util.Import(
      message_type=dataproc.messages.AutoscalingPolicy, stream=data)

  # Ignore user set id in the file (if any), and overwrite with the policy_ref
  # provided with this command
  policy.id = policy_id

  # Similarly, ignore the set resource name. This field is OUTPUT_ONLY, so we
  # can just clear it.
  policy.name = None

  # Set duration fields to their seconds values
  if policy.basicAlgorithm is not None:
    if policy.basicAlgorithm.cooldownPeriod is not None:
      policy.basicAlgorithm.cooldownPeriod = str(
          arg_parsers.Duration(lower_bound='2m', upper_bound='1d')(
              policy.basicAlgorithm.cooldownPeriod)) + 's'
    if policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout is not None:
      policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout = str(
          arg_parsers.Duration(lower_bound='0s', upper_bound='1d')
          (policy.basicAlgorithm.yarnConfig.gracefulDecommissionTimeout)) + 's'

  return policy


def CreateAutoscalingPolicy(dataproc, name, policy):
  """Returns the server-resolved policy after creating the given policy.

  Args:
    dataproc: wrapper for dataproc resources, client and messages.
    name: The autoscaling policy resource name.
    policy: The AutoscalingPolicy message to create.
  """
  # TODO(b/109837200) make the dataproc discovery doc parameters consistent
  # Parent() fails for the collection because of projectId/projectsId and
  # regionId/regionsId inconsistencies.
  # parent = template_ref.Parent().RelativePath()
  parent = '/'.join(name.split('/')[0:4])

  request = \
    dataproc.messages.DataprocProjectsRegionsAutoscalingPoliciesCreateRequest(
        parent=parent,
        autoscalingPolicy=policy)
  policy = dataproc.client.projects_regions_autoscalingPolicies.Create(request)
  log.status.Print('Created [{0}].'.format(policy.id))
  return policy


def UpdateAutoscalingPolicy(dataproc, name, policy):
  """Returns the server-resolved policy after updating the given policy.

  Args:
    dataproc: wrapper for dataproc resources, client and messages.
    name: The autoscaling policy resource name.
    policy: The AutoscalingPolicy message to create.
  """
  # Though the name field is OUTPUT_ONLY in the API, the Update() method of the
  # gcloud generated dataproc client expects it to be set.
  policy.name = name

  policy = \
    dataproc.client.projects_regions_autoscalingPolicies.Update(policy)
  log.status.Print('Updated [{0}].'.format(policy.id))
  return policy


def _DownscopeCredentials(token, access_boundary_json):
  """Downscope the given credentials to the given access boundary.

  Args:
    token: The credentials to downscope.
    access_boundary_json: The JSON-formatted access boundary.

  Returns:
    A downscopded credential with the given access-boundary.
  """
  payload = {
      'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
      'requested_token_type': 'urn:ietf:params:oauth:token-type:access_token',
      'subject_token_type': 'urn:ietf:params:oauth:token-type:access_token',
      'subject_token': token,
      'options': access_boundary_json
  }
  cab_token_url = 'https://sts.googleapis.com/v1/token'
  headers = {'Content-Type': 'application/x-www-form-urlencoded'}
  downscope_response = requests.GetSession().post(
      cab_token_url, headers=headers, data=payload)
  if downscope_response.status_code != 200:
    raise ValueError('Error downscoping credentials')
  cab_token = json.loads(downscope_response.content)
  return cab_token.get('access_token', None)


def GetCredentials(access_boundary_json):
  """Get an access token for the user's current credentials.

  Args:
    access_boundary_json: JSON string holding the definition of the access
      boundary to apply to the credentials.

  Raises:
    PersonalAuthError: If no access token could be fetched for the user.

  Returns:
    An access token for the user.
  """
  cred = c_store.Load(
      None, allow_account_impersonation=True, use_google_auth=True)
  c_store.Refresh(cred)
  if c_creds.IsOauth2ClientCredentials(cred):
    token = cred.access_token
  else:
    token = cred.token
  if not token:
    raise exceptions.PersonalAuthError(
        'No access token could be obtained from the current credentials.')
  return _DownscopeCredentials(token, access_boundary_json)


class PersonalAuthUtils(object):
  """Util functions for enabling personal auth session."""

  def __init__(self):
    pass

  def _RunOpensslCommand(self, openssl_executable, args, stdin=None):
    """Run the specified command, capturing and returning output as appropriate.

    Args:
      openssl_executable: The path to the openssl executable.
      args: The arguments to the openssl command to run.
      stdin: The input to the command.

    Returns:
      The output of the command.

    Raises:
      PersonalAuthError: If the call to openssl fails
    """
    command = [openssl_executable]
    command.extend(args)
    stderr = None
    try:
      if getattr(subprocess, 'run', None):
        proc = subprocess.run(
            command,
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False)
        stderr = proc.stderr.decode('utf-8').strip()
        # N.B. It would be better if we could simply call `subprocess.run` with
        # the `check` keyword arg set to true rather than manually calling
        # `check_returncode`. However, we want to capture the stderr when the
        # command fails, and the CalledProcessError type did not have a field
        # for the stderr until Python version 3.5.
        #
        # As such, we need to manually call `check_returncode` as long as we
        # are supporting Python versions prior to 3.5.
        proc.check_returncode()
        return proc.stdout
      else:
        p = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, _ = p.communicate(input=stdin)
        return stdout
    except Exception as ex:
      if stderr:
        log.error('OpenSSL command "%s" failed with error message "%s"',
                  ' '.join(command), stderr)
      raise exceptions.PersonalAuthError('Failure running openssl command: "' +
                                         ' '.join(command) + '": ' +
                                         six.text_type(ex))

  def _ComputeHmac(self, key, data, openssl_executable):
    """Compute HMAC tag using OpenSSL."""
    cmd_output = self._RunOpensslCommand(
        openssl_executable, ['dgst', '-sha256', '-hmac', key],
        stdin=data).decode('utf-8')
    try:
      # Split the openssl output to get the HMAC.
      stripped_output = cmd_output.strip().split(' ')[1]
      if len(stripped_output) != 64:
        raise ValueError('HMAC output is expected to be 64 characters long.')
      int(stripped_output, 16)  # Check that the HMAC is in hex format.
    except Exception as ex:
      raise exceptions.PersonalAuthError(
          'Failure due to invalid openssl output: ' + six.text_type(ex))
    return (stripped_output + '\n').encode('utf-8')

  def _DeriveHkdfKey(self, prk, info, openssl_executable):
    """Derives HMAC-based Key Derivation Function (HKDF) key through expansion on the initial pseudorandom key.

    Args:
      prk: a pseudorandom key.
      info: optional context and application specific information (can be
        empty).
      openssl_executable: The path to the openssl executable.

    Returns:
      Output keying material, expected to be of 256-bit length.
    """
    if len(prk) != 32:
      raise ValueError(
          'The given initial pseudorandom key is expected to be 32 bytes long.')
    base16_prk = base64.b16encode(prk).decode('utf-8')
    t1 = self._ComputeHmac(base16_prk, b'', openssl_executable)
    t2data = bytearray(t1)
    t2data.extend(info)
    t2data.extend(b'\x01')
    return self._ComputeHmac(base16_prk, t2data, openssl_executable)

  # It is possible (although very rare) for the random pad generated by
  # openssl to not be usable by openssl for encrypting the secret. When
  # that happens the call to openssl will raise a CalledProcessError with
  # the message "Error reading password from BIO\nError getting password".
  #
  # To account for this we retry on that error, but this is so rare that
  # a single retry should be sufficient.
  @retry.RetryOnException(max_retrials=1)
  def _EncodeTokenUsingOpenssl(self, public_key, secret, openssl_executable):
    """Encode token using OpenSSL.

    Args:
      public_key: The public key for the session/cluster.
      secret: Token to be encrypted.
      openssl_executable: The path to the openssl executable.

    Returns:
      Encrypted token.
    """
    key_hash = hashlib.sha256((public_key + '\n').encode('utf-8')).hexdigest()
    iv_bytes = base64.b16encode(os.urandom(16))
    initialization_vector = iv_bytes.decode('utf-8')
    initial_key = os.urandom(32)
    encryption_key = self._DeriveHkdfKey(initial_key,
                                         'encryption_key'.encode('utf-8'),
                                         openssl_executable)
    auth_key = base64.b16encode(
        self._DeriveHkdfKey(initial_key, 'auth_key'.encode('utf-8'),
                            openssl_executable)).decode('utf-8')
    with tempfile.NamedTemporaryFile() as kf:
      kf.write(public_key.encode('utf-8'))
      kf.seek(0)
      encrypted_key = self._RunOpensslCommand(
          openssl_executable,
          ['rsautl', '-oaep', '-encrypt', '-pubin', '-inkey', kf.name],
          stdin=base64.b64encode(initial_key))
    if len(encrypted_key) != 512:
      raise ValueError('The encrypted key is expected to be 512 bytes long.')
    encoded_key = base64.b64encode(encrypted_key).decode('utf-8')

    with tempfile.NamedTemporaryFile() as pf:
      pf.write(encryption_key)
      pf.seek(0)
      encrypt_args = [
          'enc', '-aes-256-ctr', '-salt', '-iv', initialization_vector, '-pass',
          'file:{}'.format(pf.name)
      ]
      encrypted_token = self._RunOpensslCommand(
          openssl_executable, encrypt_args, stdin=secret.encode('utf-8'))
    if len(encrypted_key) != 512:
      raise ValueError('The encrypted key is expected to be 512 bytes long.')
    encoded_token = base64.b64encode(encrypted_token).decode('utf-8')

    hmac_input = bytearray(iv_bytes)
    hmac_input.extend(encrypted_token)
    hmac_tag = self._ComputeHmac(auth_key, hmac_input,
                                 openssl_executable).decode('utf-8')[
                                     0:32]  # Truncate the HMAC tag to 128-bit
    return '{}:{}:{}:{}:{}'.format(key_hash, encoded_token, encoded_key,
                                   initialization_vector, hmac_tag)

  def EncryptWithPublicKey(self, public_key, secret, openssl_executable):
    """Encrypt secret with resource public key.

    Args:
      public_key: The public key for the session/cluster.
      secret: Token to be encrypted.
      openssl_executable: The path to the openssl executable.

    Returns:
      Encrypted token.
    """
    if openssl_executable:
      return self._EncodeTokenUsingOpenssl(public_key, secret,
                                           openssl_executable)
    try:
      # pylint: disable=g-import-not-at-top
      import tink
      from tink import hybrid
      # pylint: enable=g-import-not-at-top
    except ImportError:
      raise exceptions.PersonalAuthError(
          'Cannot load the Tink cryptography library. Either the '
          'library is not installed, or site packages are not '
          'enabled for the Google Cloud SDK. Please consult Cloud '
          'Dataproc Personal Auth documentation on adding Tink to '
          'Google Cloud SDK for further instructions.\n'
          'https://cloud.google.com/dataproc/docs/concepts/iam/personal-auth')
    hybrid.register()
    context = b''

    # Extract value of key corresponding to primary key.
    public_key_value = json.loads(public_key)['key'][0]['keyData']['value']
    key_hash = hashlib.sha256(
        (public_key_value + '\n').encode('utf-8')).hexdigest()

    # Load public key and create keyset handle.
    reader = tink.JsonKeysetReader(public_key)
    kh_pub = tink.read_no_secret_keyset_handle(reader)

    # Create encrypter instance.
    encrypter = kh_pub.primitive(hybrid.HybridEncrypt)
    ciphertext = encrypter.encrypt(secret.encode('utf-8'), context)

    encoded_token = base64.b64encode(ciphertext).decode('utf-8')
    return '{}:{}'.format(key_hash, encoded_token)

  def IsTinkLibraryInstalled(self):
    """Check if Tink cryptography library can be loaded."""
    try:
      # pylint: disable=g-import-not-at-top
      # pylint: disable=unused-import
      import tink
      from tink import hybrid
      # pylint: enable=g-import-not-at-top
      # pylint: enable=unused-import
      return True
    except ImportError:
      return False


def ReadSessionTemplate(dataproc, template_file_name=None):
  """Returns session template read from YAML file.

  Args:
    dataproc: Wrapper for dataproc resources, client and messages.
    template_file_name: If set, location of the YAML file to read from.
      Otherwise, reads from stdin.

  Raises:
    argparse.ArgumentError if duration formats are invalid or out of bounds.
  """
  data = console_io.ReadFromFileOrStdin(template_file_name or '-', binary=False)
  template = export_util.Import(
      message_type=dataproc.messages.SessionTemplate, stream=data)

  return template


def CreateSessionTemplate(dataproc, name, template):
  """Returns the server-resolved template after creating the given template.

  Args:
    dataproc: Wrapper for dataproc resources, client and messages.
    name: The session template resource name.
    template: The SessionTemplate message to create.
  """
  parent = '/'.join(name.split('/')[0:4])
  template.name = name

  request = (
      dataproc.messages.DataprocProjectsLocationsSessionTemplatesCreateRequest(
          parent=parent,
          sessionTemplate=template))
  template = dataproc.client.projects_locations_sessionTemplates.Create(request)
  log.status.Print('Created [{0}].'.format(template.name))
  return template


def UpdateSessionTemplate(dataproc, name, template):
  """Returns the server-resolved template after updating the given template.

  Args:
    dataproc: Wrapper for dataproc resources, client and messages.
    name: The session template resource name.
    template: The SessionTemplate message to create.
  """
  template.name = name

  template = dataproc.client.projects_locations_sessionTemplates.Patch(template)
  log.status.Print('Updated [{0}].'.format(template.name))
  return template


def YieldFromListWithUnreachableList(unreachable_warning_msg, *args, **kwargs):
  """Yields from paged List calls handling unreachable list."""
  unreachable = set()

  def _GetFieldFn(message, attr):
    unreachable.update(message.unreachable)
    return getattr(message, attr)

  result = list_pager.YieldFromList(get_field_func=_GetFieldFn, *args, **kwargs)
  for item in result:
    yield item
  if unreachable:
    log.warning(
        unreachable_warning_msg,
        ', '.join(sorted(unreachable)),
    )
