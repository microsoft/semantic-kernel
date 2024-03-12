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

"""Utilities for `gcloud app deploy <queue|cron>.yaml` deployments.

Functions defined here are used to migrate away from soon to be deprecated
admin-console-hr superapp. Instead we will be using Cloud Tasks APIs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.tasks import task_queues_convertors as convertors
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.command_lib.tasks import flags
from googlecloudsdk.command_lib.tasks import parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

import six
from six.moves import urllib

# Some values still need to be further processed and can not be used as is for
# CT APIs. One example is 'task retry limit' where the value stored in the
# backend is always x + 1 where x is the value in the YAML file.
CONVERSION_FUNCTIONS = {
    'max_concurrent_requests': lambda x: min(5000, max(1, int(x))),
    'rate': convertors.ConvertRate,
    'retry_parameters.min_backoff_seconds': convertors.ConvertBackoffSeconds,
    'retry_parameters.max_backoff_seconds': convertors.ConvertBackoffSeconds,
    'retry_parameters.task_age_limit': convertors.ConvertTaskAgeLimit,
    'retry_parameters.task_retry_limit': lambda x: int(x) + 1,
    'target': convertors.ConvertTarget
}


def IsClose(a, b, rel_tol=1e-09, abs_tol=0.0):
  """Checks if two numerical values are same or almost the same.

  This function is only created to provides backwards compatability for python2
  which does not support 'math.isclose(...)' function. The output of this
  function mimicks exactly the behavior of math.isclose.

  Args:
    a: One of the values to be tested for relative closeness.
    b: One of the values to be tested for relative closeness.
    rel_tol: Relative tolerance allowed. Default value is set so that the two
      values must be equivalent to 9 decimal digits.
    abs_tol: The minimum absoulute tolerance difference. Useful for
      comparisons near zero.

  Returns:
    True if the attribute needs to be updated to the new value, False otherwise.
  """
  return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def _DoesAttributeNeedToBeUpdated(cur_queue_state, attribute, new_value):
  """Checks whether the attribute & value provided need to be updated.

  Note: We only check if the attribute exists in `queue.rateLimits` and
  `queue.retryConfig` since those are the only attributes we verify here. The
  only attribute we do not verify here is app-engine routing override which we
  handle separately.

  Args:
    cur_queue_state: apis.cloudtasks.<ver>.cloudtasks_<ver>_messages.Queue,
      The Queue instance fetched from the backend.
    attribute: Snake case representation of the CT API attribute name. One
      example is 'max_burst_size'.
    new_value: The value we are trying to set this attribute to.

  Returns:
    True if the attribute needs to be updated to the new value, False otherwise.
  """
  proto_attribute_name = convertors.ConvertStringToCamelCase(attribute)
  if (
      hasattr(cur_queue_state, 'rateLimits') and
      hasattr(cur_queue_state.rateLimits, proto_attribute_name)
  ):
    old_value = getattr(cur_queue_state.rateLimits, proto_attribute_name)
  elif hasattr(cur_queue_state.retryConfig, proto_attribute_name):
    old_value = getattr(cur_queue_state.retryConfig, proto_attribute_name)
  else:
    # Unable to get old attribute value.
    return True
  if old_value == new_value:
    return False
  if (
      old_value is None and
      attribute != 'max_concurrent_dispatches' and
      attribute in constants.PUSH_QUEUES_APP_DEPLOY_DEFAULT_VALUES and
      new_value == constants.PUSH_QUEUES_APP_DEPLOY_DEFAULT_VALUES[attribute]
  ):
    return False
  if attribute == 'max_dispatches_per_second' and not new_value:
    # No need to set rate if rate specified is 0. Instead, we will pause the
    # queue if it is not already paused or blocked.
    return False
  if old_value is None or new_value is None:
    return True
  old_value = convertors.CheckAndConvertStringToFloatIfApplicable(old_value)
  new_value = convertors.CheckAndConvertStringToFloatIfApplicable(new_value)
  if (
      isinstance(old_value, float) and
      isinstance(new_value, float)
  ):
    return not IsClose(old_value, new_value)
  return old_value != new_value


def _SetSpecifiedArg(cloud_task_args, key, value):
  """Sets the specified key, value pair in the namespace provided.

  The main reason to have this function is to centralize all the protected
  access to _specified_args

  Args:
    cloud_task_args: argparse.Namespace, A placeholder args namespace built to
      pass on forwards to Cloud Tasks API.
    key: The attribute key we are trying to set.
    value: The attribute value we are trying to set.
  """
  # pylint: disable=protected-access
  cloud_task_args._specified_args[key] = value


def _DeleteSpecifiedArg(cloud_task_args, key):
  """Deletes the specified key in the namespace provided.

  Args:
    cloud_task_args: argparse.Namespace, A placeholder args namespace built to
      pass on forwards to Cloud Tasks API.
    key: The attribute key we are trying to set.
  """
  # pylint: disable=protected-access
  del cloud_task_args._specified_args[key]


def _PostProcessMinMaxBackoff(
    cloud_task_args, used_default_value_for_min_backoff, cur_queue_state):
  """Checks min and max backoff values and updates the other value if needed.

  When uploading via queue.yaml files, if only one of the backoff values is
  specified, the other value will automatically be updated to the default
  value. If the default value does not satisfy the condition
  min_backoff <= max_backoff, then it is set equal to the other backoff value.

  Args:
    cloud_task_args: argparse.Namespace, A placeholder args namespace built to
      pass on forwards to Cloud Tasks API.
    used_default_value_for_min_backoff: A boolean value telling us if we used
      a default value for min_backoff or if it was specified explicitly in the
      YAML file.
    cur_queue_state: apis.cloudtasks.<ver>.cloudtasks_<ver>_messages.Queue,
      The Queue instance fetched from the backend if it exists, None otherwise.
  """
  if cloud_task_args.type == 'pull':
    return
  min_backoff = convertors.CheckAndConvertStringToFloatIfApplicable(
      cloud_task_args.min_backoff)
  max_backoff = convertors.CheckAndConvertStringToFloatIfApplicable(
      cloud_task_args.max_backoff)
  if min_backoff > max_backoff:
    if used_default_value_for_min_backoff:
      min_backoff = max_backoff
      cloud_task_args.min_backoff = cloud_task_args.max_backoff
      _SetSpecifiedArg(
          cloud_task_args, 'min_backoff', cloud_task_args.max_backoff)
    else:
      max_backoff = min_backoff
      cloud_task_args.max_backoff = cloud_task_args.min_backoff
      _SetSpecifiedArg(
          cloud_task_args, 'max_backoff', cloud_task_args.min_backoff)

  # Check if the backend values match with what we are trying to set
  if cur_queue_state and cur_queue_state.retryConfig:
    old_min_backoff = convertors.CheckAndConvertStringToFloatIfApplicable(
        cur_queue_state.retryConfig.minBackoff)
    old_max_backoff = convertors.CheckAndConvertStringToFloatIfApplicable(
        cur_queue_state.retryConfig.maxBackoff)
    if max_backoff == old_max_backoff and min_backoff == old_min_backoff:
      _DeleteSpecifiedArg(cloud_task_args, 'min_backoff')
      cloud_task_args.min_backoff = None
      _DeleteSpecifiedArg(cloud_task_args, 'max_backoff')
      cloud_task_args.max_backoff = None


def _PostProcessRoutingOverride(cloud_task_args, cur_queue_state):
  """Checks if service and target values need to be updated for host URL.

  An app engine host URL may have optionally version_dot_service appended to
  the URL if specified via 'routing_override'. Here we check the existing URL
  and make sure the service & target values are only updated when need be.

  Args:
    cloud_task_args: argparse.Namespace, A placeholder args namespace built to
      pass on forwards to Cloud Tasks API.
    cur_queue_state: apis.cloudtasks.<ver>.cloudtasks_<ver>_messages.Queue,
      The Queue instance fetched from the backend if it exists, None otherwise.
  """
  try:
    host_url = cur_queue_state.appEngineHttpQueue.appEngineRoutingOverride.host
  except AttributeError:
    # The queue does not exist or had no override set before.
    return
  if cloud_task_args.IsSpecified('routing_override'):
    targets = []
    if 'version' in cloud_task_args.routing_override:
      targets.append(cloud_task_args.routing_override['version'])
    if 'service' in cloud_task_args.routing_override:
      targets.append(cloud_task_args.routing_override['service'])
    targets_sub_url = '.'.join(targets)
    targets_sub_url_and_project = '{}.{}.'.format(
        targets_sub_url, properties.VALUES.core.project.Get())
    if host_url.startswith(targets_sub_url_and_project):
      # pylint: disable=protected-access
      del cloud_task_args._specified_args['routing_override']
      cloud_task_args.routing_override = None


def _PopulateCloudTasksArgs(queue, cur_queue_state, ct_expected_args):
  """Builds placeholder command line args to pass on to Cloud Tasks API.

  Most of Cloud Tasks functions use args passed in during CLI invocation. To
  reuse those functions without extensive rework on their implementation, we
  recreate the args in the format that those functions expect.

  Args:
    queue: third_party.appengine.api.queueinfo.QueueEntry, The QueueEntry
      instance generated from the parsed YAML file.
    cur_queue_state: apis.cloudtasks.<ver>.cloudtasks_<ver>_messages.Queue,
      The Queue instance fetched from the backend if it exists, None otherwise.
    ct_expected_args: A list of expected args that we need to initialize before
      forwarding to Cloud Tasks APIs.

  Returns:
    argparse.Namespace, A placeholder args namespace built to pass on forwards
    to Cloud Tasks API.
  """

  cloud_task_args = parser_extensions.Namespace()
  for task_flag in ct_expected_args:
    setattr(cloud_task_args, task_flag, None)

  used_default_value_for_min_backoff = False
  for old_arg, new_arg in constants.APP_TO_TASKS_ATTRIBUTES_MAPPING.items():
    # e.g. old_arg, new_arg = 'retry_parameters.max_doublings', 'max_doublings'
    old_arg_list = old_arg.split('.')
    value = queue
    for old_arg_sub in old_arg_list:
      if not hasattr(value, old_arg_sub):
        value = None
        break
      value = getattr(value, old_arg_sub)
    # Max attempts is a special case because 0 is actually stored as 1.
    if value or (value is not None and new_arg in ('max_attempts',)):
      # Some values need to be converted to a format that CT APIs accept
      if old_arg in CONVERSION_FUNCTIONS:
        value = CONVERSION_FUNCTIONS[old_arg](value)
      if (
          not cur_queue_state or
          new_arg in ('name', 'type', 'min_backoff', 'max_backoff') or
          _DoesAttributeNeedToBeUpdated(cur_queue_state, new_arg, value)
      ):
        # Attributes specified here are forwarded to CT APIs. We always forward
        # 'name' and 'type' attributes and we forward any other attributes if
        # they have changed from before or if this is a brand new queue.
        _SetSpecifiedArg(cloud_task_args, new_arg, value)
    else:
      # Set default values for some of the attributes if no value is present
      if queue.mode == constants.PULL_QUEUE:
        default_values = constants.PULL_QUEUES_APP_DEPLOY_DEFAULT_VALUES
      else:
        default_values = constants.PUSH_QUEUES_APP_DEPLOY_DEFAULT_VALUES
      if new_arg in default_values:
        if new_arg == 'min_backoff':
          used_default_value_for_min_backoff = True
        value = default_values[new_arg]
        if (
            not cur_queue_state or
            new_arg in ('min_backoff', 'max_backoff') or
            _DoesAttributeNeedToBeUpdated(cur_queue_state, new_arg, value)
        ):
          _SetSpecifiedArg(cloud_task_args, new_arg, value)
    setattr(cloud_task_args, new_arg, value)
  _PostProcessMinMaxBackoff(
      cloud_task_args, used_default_value_for_min_backoff, cur_queue_state)
  _PostProcessRoutingOverride(cloud_task_args, cur_queue_state)
  return cloud_task_args


def _AnyUpdatableFields(args):
  """Check whether the queue has any changed attributes based on args provided.

  Args:
    args: argparse.Namespace, A placeholder args namespace built to pass on
      forwards to Cloud Tasks API.

  Returns:
    True if any of the queue attributes have changed from the attributes stored
    in the backend, False otherwise.
  """
  # pylint: disable=protected-access
  modifiable_args = [
      x for x in args._specified_args if x not in ('name', 'type')]
  return True if modifiable_args else False


def _RaiseHTTPException(msg_body):
  """Raises an HTTP exception with status code 400.

  This function is used to raise the same exceptions generated by the older
  implementation of `gcloud app delpoy queue.yaml` when it communicated with
  the Zeus backend over HTTP.

  Args:
    msg_body: A string providing more information about the error being raised.

  Raises:
    HTTPError: Based on the inputs provided.
  """
  exc_msg = 'Bad Request Unexpected HTTP status 400'
  error = urllib.error.HTTPError(None, six.moves.http_client.BAD_REQUEST,
                                 exc_msg, None, None)
  msg_body = six.ensure_binary(msg_body)
  exceptions.reraise(util.RPCError(error, body=msg_body))


def _ValidateTaskRetryLimit(queue):
  """Validates task retry limit input values for both queues in the YAML file.

  Args:
    queue: third_party.appengine.api.queueinfo.QueueEntry, The QueueEntry
      instance generated from the parsed YAML file.

  Raises:
    HTTPError: Based on the inputs provided if value specified is negative.
  """
  if (
      queue.retry_parameters.task_retry_limit and
      queue.retry_parameters.task_retry_limit < 0
  ):
    _RaiseHTTPException(
        'Invalid queue configuration. Task retry limit must not be less '
        'than zero.')


def ValidateCronYamlFileConfig(config):
  """Validates jobs configuration parameters in the cron YAML file.

  The purpose of this function is to mimick the behaviour of the old
  implementation of `gcloud app deploy cron.yaml` before migrating away
  from console-admin-hr. The errors generated are the same as the ones
  previously seen when gcloud sent the batch-request for updating jobs to the
  Zeus backend.

  Args:
     config: A yaml_parsing.ConfigYamlInfo object for the parsed YAML file we
      are going to process.

  Raises:
    HTTPError: Various different scenarios defined in the function can cause
      this exception to be raised.
  """
  cron_yaml = config.parsed
  if not cron_yaml.cron:
    return
  for job in cron_yaml.cron:

    # Retry Parameters
    if job.retry_parameters:

      # Job Retry Limit
      if (
          job.retry_parameters.job_retry_limit and
          job.retry_parameters.job_retry_limit > 5
      ):
        _RaiseHTTPException(
            'Invalid Cron retry parameters: Cannot set retry limit to more '
            'than 5 (currently set to {}).'.format(
                job.retry_parameters.job_retry_limit))

      # Job Age Limit
      if (
          job.retry_parameters.job_age_limit and
          int(convertors.CheckAndConvertStringToFloatIfApplicable(
              job.retry_parameters.job_age_limit)) <= 0
      ):
        _RaiseHTTPException(
            'Invalid Cron retry parameters: Job age limit must be greater '
            'than zero seconds.')

      # Min & Max backoff comparison
      if (
          job.retry_parameters.min_backoff_seconds is not None and
          job.retry_parameters.max_backoff_seconds is not None
      ):
        min_backoff = job.retry_parameters.min_backoff_seconds
        max_backoff = job.retry_parameters.max_backoff_seconds
        if max_backoff < min_backoff:
          _RaiseHTTPException(
              'Invalid Cron retry parameters: Min backoff sec must not be '
              'greater than than max backoff sec.')


def ValidateQueueYamlFileConfig(config):
  """Validates queue configuration parameters in the queue YAML file.

  The purpose of this function is to mimick the behaviour of the old
  implementation of `gcloud app deploy queue.yaml` before migrating away
  from console-admin-hr. The errors generated are the same as the ones
  previously seen when gcloud sent the batch-request for updating queues to the
  Zeus backend.

  Args:
     config: A yaml_parsing.ConfigYamlInfo object for the parsed YAML file we
      are going to process.

  Raises:
    HTTPError: Various different scenarios defined in the function can cause
      this exception to be raised.
  """
  queue_yaml = config.parsed
  if not queue_yaml.queue:
    return
  for queue in queue_yaml.queue:
    # Push queues
    if not queue.mode or queue.mode == constants.PUSH_QUEUE:

      # Rate
      if not queue.rate:
        _RaiseHTTPException(
            'Invalid queue configuration. Refill rate must be specified for '
            'push-based queue.')
      else:
        rate_in_seconds = convertors.ConvertRate(queue.rate)
        if rate_in_seconds > constants.MAX_RATE:
          _RaiseHTTPException(
              'Invalid queue configuration. Refill rate must not exceed '
              '{} per second (is {:.1f}).'.format(
                  constants.MAX_RATE, rate_in_seconds))

      # Retry Parameters
      if queue.retry_parameters:
        # Task Retry Limit
        _ValidateTaskRetryLimit(queue)

        # Task Age Limit
        if (
            queue.retry_parameters.task_age_limit and
            int(convertors.CheckAndConvertStringToFloatIfApplicable(
                queue.retry_parameters.task_age_limit)) <= 0
        ):
          _RaiseHTTPException(
              'Invalid queue configuration. Task age limit must be greater '
              'than zero.')

        # Min backoff
        if (
            queue.retry_parameters.min_backoff_seconds and
            queue.retry_parameters.min_backoff_seconds < 0
        ):
          _RaiseHTTPException(
              'Invalid queue configuration. Min backoff seconds must not be '
              'less than zero.')

        # Max backoff
        if (
            queue.retry_parameters.max_backoff_seconds and
            queue.retry_parameters.max_backoff_seconds < 0
        ):
          _RaiseHTTPException(
              'Invalid queue configuration. Max backoff seconds must not be '
              'less than zero.')

        # Max Doublings
        if (
            queue.retry_parameters.max_doublings and
            queue.retry_parameters.max_doublings < 0
        ):
          _RaiseHTTPException(
              'Invalid queue configuration. Max doublings must not be less '
              'than zero.')

        # Min & Max backoff comparison
        if (
            queue.retry_parameters.min_backoff_seconds is not None and
            queue.retry_parameters.max_backoff_seconds is not None
        ):
          min_backoff = queue.retry_parameters.min_backoff_seconds
          max_backoff = queue.retry_parameters.max_backoff_seconds
          if max_backoff < min_backoff:
            _RaiseHTTPException(
                'Invalid queue configuration. Min backoff sec must not be '
                'greater than than max backoff sec.')

      # Bucket size
      if queue.bucket_size:
        if queue.bucket_size < 0:
          _RaiseHTTPException(
              'Error updating queue "{}": The queue rate is invalid.'.format(
                  queue.name))
        elif queue.bucket_size > constants.MAX_BUCKET_SIZE:
          _RaiseHTTPException(
              'Error updating queue "{}": Maximum bucket size is {}.'.format(
                  queue.name, constants.MAX_BUCKET_SIZE))

    # Pull Queues
    else:
      # Rate
      if queue.rate:
        _RaiseHTTPException(
            'Invalid queue configuration. Refill rate must not be specified '
            'for pull-based queue.')

      # Retry Parameters
      if queue.retry_parameters:
        # Task Retry Limit
        _ValidateTaskRetryLimit(queue)

        # Task Age Limit
        if queue.retry_parameters.task_age_limit is not None:
          _RaiseHTTPException(
              "Invalid queue configuration. Can't specify task_age_limit "
              "for a pull queue.")

        # Min backoff
        if queue.retry_parameters.min_backoff_seconds is not None:
          _RaiseHTTPException(
              "Invalid queue configuration. Can't specify min_backoff_seconds "
              "for a pull queue.")

        # Max backoff
        if queue.retry_parameters.max_backoff_seconds is not None:
          _RaiseHTTPException(
              "Invalid queue configuration. Can't specify max_backoff_seconds "
              "for a pull queue.")

        # Max doublings
        if queue.retry_parameters.max_doublings is not None:
          _RaiseHTTPException(
              "Invalid queue configuration. Can't specify max_doublings "
              "for a pull queue.")

      # Max concurrent requests
      if queue.max_concurrent_requests is not None:
        _RaiseHTTPException(
            'Invalid queue configuration. Max concurrent requests must not '
            'be specified for pull-based queue.')

      # Bucket size
      if queue.bucket_size is not None:
        _RaiseHTTPException(
            'Invalid queue configuration. Bucket size must not be specified '
            'for pull-based queue.')

      # Target
      if queue.target:
        _RaiseHTTPException(
            'Invalid queue configuration. Target must not be specified for '
            'pull-based queue.')


def FetchCurrentQueuesData(tasks_api):
  """Fetches the current queues data stored in the database.

  Args:
    tasks_api: api_lib.tasks.<Alpha|Beta|GA>ApiAdapter, Cloud Tasks API needed
      for doing queue based operations.

  Returns:
    A dictionary with queue names as keys and corresponding protobuf Queue
    objects as values apis.cloudtasks.<ver>.cloudtasks_<ver>_messages.Queue
  """
  queues_client = tasks_api.queues
  app_location = app.ResolveAppLocation(parsers.ParseProject())
  region_ref = parsers.ParseLocation(app_location)
  all_queues_in_db_dict = {
      os.path.basename(x.name): x for x in queues_client.List(region_ref)
  }
  return all_queues_in_db_dict


def FetchCurrentJobsData(scheduler_api):
  """Fetches the current jobs data stored in the database.

  Args:
    scheduler_api: api_lib.scheduler.<Alpha|Beta|GA>ApiAdapter, Cloud Scheduler
      API needed for doing jobs based operations.

  Returns:
    A list of currently existing jobs in the backend.
  """
  jobs_client = scheduler_api.jobs
  app_location = app.ResolveAppLocation(
      parsers.ParseProject(), locations_client=scheduler_api.locations)
  region_ref = parsers.ParseLocation(app_location).RelativeName()
  return list(x for x in jobs_client.List(region_ref))


def DeployQueuesYamlFile(
    tasks_api,
    config,
    all_queues_in_db_dict,
    ct_api_version=base.ReleaseTrack.BETA
):
  """Perform a deployment based on the parsed 'queue.yaml' file.

  Args:
    tasks_api: api_lib.tasks.<Alpha|Beta|GA>ApiAdapter, Cloud Tasks API needed
      for doing queue based operations.
    config: A yaml_parsing.ConfigYamlInfo object for the parsed YAML file we
      are going to process.
    all_queues_in_db_dict: A dictionary with queue names as keys and
      corresponding apis.cloudtasks.<ver>.cloudtasks_<ver>_messages.Queue
      objects as values
    ct_api_version: The Cloud Tasks API version we want to use.

  Returns:
    A list of responses received from the Cloud Tasks APIs representing queue
    states for every call made to modify the attributes of a queue.
  """

  class _PlaceholderQueueRef:
    """A placeholder class to simulate queue_ref resource objects used in CT APIs.

    This class simulates the behaviour of the resource object returned by
    tasks.parsers.ParseQueue(...) function. We use this placeholder class
    instead of creating an actual resource instance because otherwise it takes
    roughly 2 minutes to create resource instances for a 1000 queues.

    Attributes:
      _relative_path: A string representing the full path for a queue in the
        format: 'projects/<project>/locations/<location>/queues/<queue>'
    """

    def __init__(self, relative_path):
      """Initializes the instance and sets the relative path."""
      self._relative_path = relative_path

    def RelativeName(self):
      """Gets the string representing the full path for a queue.

      This is the only function we are currently using in CT APIs for the
      queue_ref resource object.

      Returns:
        A string representing the full path for a queue in the following
        format: 'projects/<project>/locations/<location>/queues/<queue>'
      """
      return self._relative_path

  queue_yaml = config.parsed
  resume_paused_queues = queue_yaml.resume_paused_queues != 'False'
  queues_client = tasks_api.queues
  queues_not_present_in_yaml = set(all_queues_in_db_dict.keys())

  # Just need to create one real instance of queue_ref. After that we can
  # create placeholder queue_ref objects based on this instance.
  queue_ref = parsers.ParseQueue('a')
  queue_ref_stub = queue_ref.RelativeName()[:-1]

  # Get the arg values that we need to fill up for each queue using CT APIs
  # pylint: disable=protected-access
  task_args = flags._PushQueueFlags(release_track=ct_api_version)
  # TODO(b/169069379) Remove max_burst_size when/if API is exposed via `gcloud
  # tasks queues` CLI invocation.
  task_args.append(base.Argument('--max_burst_size', type=int, help=''))
  expected_args = []
  for task_flag in task_args:
    new_arg = task_flag.args[0][2:].replace('-', '_')
    expected_args.extend((new_arg, 'clear_{}'.format(new_arg)))

  responses = []
  if queue_yaml.queue is None:
    queue_yaml.queue = []
  for queue in queue_yaml.queue:
    if queue.name in queues_not_present_in_yaml:
      queues_not_present_in_yaml.remove(queue.name)

    queue_ref = _PlaceholderQueueRef('{}{}'.format(queue_ref_stub, queue.name))
    cur_queue_object = all_queues_in_db_dict.get(queue.name, None)
    cloud_task_args = _PopulateCloudTasksArgs(queue, cur_queue_object,
                                              expected_args)
    rate_to_set = cloud_task_args.GetValue('max_dispatches_per_second')

    if (
        resume_paused_queues and
        cur_queue_object and
        (rate_to_set or queue.mode == constants.PULL_QUEUE) and
        cur_queue_object.state in (cur_queue_object.state.DISABLED,
                                   cur_queue_object.state.PAUSED)
    ):
      # Resume queue if it exists, was previously disabled/paused, the new
      # rate > 0 and if there is no global flag to skip resuming paused queues.
      queues_client.Resume(queue_ref)
    elif (
        cur_queue_object and
        not rate_to_set and
        cur_queue_object.state == cur_queue_object.state.RUNNING and
        queue.mode in (None, constants.PUSH_QUEUE)
    ):
      queues_client.Pause(queue_ref)

    if not _AnyUpdatableFields(cloud_task_args):
      # Queue attributes in DB == Queue attributes in YAML
      continue

    queue_config = parsers.ParseCreateOrUpdateQueueArgs(
        cloud_task_args,
        # Deliberately hardcoding push queues because we want to be able to
        # modify all attributes even for pull queues.
        constants.PUSH_QUEUE,
        tasks_api.messages,
        release_track=ct_api_version,
        http_queue=False,
    )
    updated_fields = parsers.GetSpecifiedFieldsMask(
        cloud_task_args, constants.PUSH_QUEUE, release_track=ct_api_version)
    # TaskTTL and TombstoneTTL are both immutable so we only set them upon
    # queue creation. The values set here are as close as possible to the
    # default values used with legacy app deploy which used superapps.
    if not cur_queue_object:
      updated_fields.extend(['taskTtl', 'tombstoneTtl'])
    app_engine_routing_override = (
        queue_config.appEngineHttpQueue.appEngineRoutingOverride
        if queue_config.appEngineHttpQueue is not None else None)
    response = queues_client.Patch(
        queue_ref,
        updated_fields,
        retry_config=queue_config.retryConfig,
        rate_limits=queue_config.rateLimits,
        app_engine_routing_override=app_engine_routing_override,
        task_ttl=constants.MAX_TASK_TTL if not cur_queue_object else None,
        task_tombstone_ttl=(
            constants.MAX_TASK_TOMBSTONE_TTL if not cur_queue_object else None),
        queue_type=queue_config.type
    )
    responses.append(response)

    if (
        not cur_queue_object and
        not rate_to_set and
        queue.mode == constants.PUSH_QUEUE
    ):
      # Pause queue if its a new push-queue and rate is zero.
      queues_client.Pause(queue_ref)

  for queue_name in queues_not_present_in_yaml:
    # Skipping 'default' queue to retain backwards compatability with legacy
    # behaviour where admin-console-hr would not DISABLE queues named 'default'.
    if queue_name == 'default':
      continue
    queue = all_queues_in_db_dict[queue_name]
    if queue.state in (queue.state.PAUSED, queue.state.DISABLED):
      continue
    queue_ref = _PlaceholderQueueRef('{}{}'.format(queue_ref_stub, queue_name))
    queues_client.Pause(queue_ref)
  return responses


def _CreateUniqueJobKeyForExistingJob(job, project):
  """Creates a key from the proto job instance's attributes passed as input.

  Args:
    job: An instance of job fetched from the backend.
    project: The base name of the project.
  Returns:
    A tuple of attributes used as a key to identify this job.
  """
  return (
      job.schedule,
      job.timeZone,
      job.appEngineHttpTarget.relativeUri,
      job.description,
      convertors.CheckAndConvertStringToFloatIfApplicable(
          job.retryConfig.minBackoffDuration) if job.retryConfig else None,
      convertors.CheckAndConvertStringToFloatIfApplicable(
          job.retryConfig.maxBackoffDuration) if job.retryConfig else None,
      job.retryConfig.maxDoublings if job.retryConfig else None,
      convertors.CheckAndConvertStringToFloatIfApplicable(
          job.retryConfig.maxRetryDuration) if job.retryConfig else None,
      job.retryConfig.retryCount if job.retryConfig else None,
      parsers.ExtractTargetFromAppEngineHostUrl(job, project),
    )


def _ReplaceDefaultRetryParamsForYamlJob(job):
  """Replaces default values for retry parameters.

  Retry parameters are set to their default values if not already user defined.
  These values are only set if the user has defined at least one retry
  parameter. Also we are limiting min_backoff to a minimum value of 5.0s since
  the new scheduler API does not support setting a lower value than this.
  Modifies input `job` argument directly.

  Args:
    job: An instance of a parsed YAML job object.
  """
  defaults = constants.CRON_JOB_LEGACY_DEFAULT_VALUES
  retry_data = job.retry_parameters
  if retry_data:
    # Min max backoff is a special case. If only one is specified, the other
    # value is set to its default value as long as this condition is satisfied:
    # 'min_backoff <= max_backoff'. Otherwise, the unspecified value is set
    # equal to the specified value.
    if (
        retry_data.min_backoff_seconds is None and
        retry_data.max_backoff_seconds is None
    ):
      # Both values are None so we should set them to defaults.
      retry_data.min_backoff_seconds = defaults['min_backoff']
      retry_data.max_backoff_seconds = defaults['max_backoff']
    elif (
        retry_data.min_backoff_seconds is None or
        retry_data.max_backoff_seconds is None
    ):
      # Only one of the backoff values is None. We need to ensure that
      # min_backoff <= max_backoff.
      if not retry_data.min_backoff_seconds:
        retry_data.min_backoff_seconds = defaults['min_backoff']
      if retry_data.max_backoff_seconds:
        retry_data.min_backoff_seconds = min(retry_data.min_backoff_seconds,
                                             retry_data.max_backoff_seconds)
      if retry_data.max_backoff_seconds is None:
        retry_data.max_backoff_seconds = defaults['max_backoff']
      retry_data.max_backoff_seconds = max(retry_data.min_backoff_seconds,
                                           retry_data.max_backoff_seconds)

    # Max Doublings
    if retry_data.max_doublings is None:
      retry_data.max_doublings = defaults['max_doublings']

    # Job Age Limit
    if retry_data.job_age_limit is None:
      retry_data.job_age_limit = defaults['max_retry_duration']


def _CreateUniqueJobKeyForYamlJob(job):
  """Creates a key from the YAML job instance's attributes passed as input.

  Args:
    job: An instance of a parsed YAML job object.
  Returns:
    A tuple of attributes used as a key to identify this job.
  """
  retry_params = job.retry_parameters
  return (
      job.schedule,
      job.timezone if job.timezone else 'UTC',
      job.url,
      job.description,
      retry_params.min_backoff_seconds if retry_params else None,
      retry_params.max_backoff_seconds if retry_params else None,
      retry_params.max_doublings if retry_params else None,
      convertors.CheckAndConvertStringToFloatIfApplicable(
          retry_params.job_age_limit) if retry_params else None,
      retry_params.job_retry_limit if retry_params else None,
      job.target,
  )


def _BuildJobsMappingDict(existing_jobs, project):
  """Builds a dictionary of unique jobs by attributes.

  Each key is in this dictionary is based on all the existing attributes of a
  job. Multiple jobs can map to the same key if all their attributes (schedule,
  url, timezone, description, etc.) match.

  Args:
    existing_jobs: A list of jobs that already exist in the backend. Each job
      maps to an apis.cloudscheduler.<ver>.cloudscheduler<ver>_messages.Job
      instance.
    project: The base name of the project.
  Returns:
    A dictionary where a key is built based on a all the job attributes and the
    value is an apis.cloudscheduler.<ver>.cloudscheduler<ver>_messages.Job
    instance.
  """
  jobs_indexed_dict = {}
  for job in existing_jobs:
    key = _CreateUniqueJobKeyForExistingJob(job, project)
    if key not in jobs_indexed_dict:
      jobs_indexed_dict[key] = []
    jobs_indexed_dict[key].append(job)
  return jobs_indexed_dict


def CreateJobInstance(scheduler_api, yaml_job):
  """Build a proto format job instance  matching the input YAML based job.

  Args:
    scheduler_api: api_lib.scheduler.<Alpha|Beta|GA>ApiAdapter, Cloud Scheduler
      API needed for doing jobs based operations.
    yaml_job: A parsed yaml_job entry read from the 'cron.yaml' file.
  Returns:
    An cloudscheduler.<ver>.cloudscheduler_<ver>_messages.Job instance.
  """
  messages = scheduler_api.messages
  if yaml_job.retry_parameters:
    retry_config = messages.RetryConfig(
        maxBackoffDuration=convertors.ConvertBackoffSeconds(
            yaml_job.retry_parameters.max_backoff_seconds),
        maxDoublings=yaml_job.retry_parameters.max_doublings,
        maxRetryDuration=convertors.ConvertTaskAgeLimit(
            yaml_job.retry_parameters.job_age_limit),
        minBackoffDuration=convertors.ConvertBackoffSeconds(
            yaml_job.retry_parameters.min_backoff_seconds),
        retryCount=yaml_job.retry_parameters.job_retry_limit
    )
  else:
    retry_config = None
  return messages.Job(
      appEngineHttpTarget=messages.AppEngineHttpTarget(
          httpMethod=messages.AppEngineHttpTarget.HttpMethodValueValuesEnum.GET,
          relativeUri=yaml_job.url,
          appEngineRouting=messages.AppEngineRouting(service=yaml_job.target)),
      retryConfig=retry_config,
      description=yaml_job.description,
      legacyAppEngineCron=scheduler_api.jobs.legacy_cron,
      schedule=yaml_job.schedule,
      timeZone=yaml_job.timezone if yaml_job.timezone else 'UTC')


def DeployCronYamlFile(scheduler_api, config, existing_jobs):
  """Perform a deployment based on the parsed 'cron.yaml' file.

  For every job defined in the cron.yaml file, we will create a new cron job
  for any job that did not already exist in our backend. We will also delete
  those jobs which are not present in the YAML file but exist in our backend.
  Note: We do not update any jobs. The only operations are Create and Delete.
  So if we modify any attribute of an existing job in the YAML file, the old
  job gets deleted and a new job is created based on the new attributes.

  Args:
    scheduler_api: api_lib.scheduler.<Alpha|Beta|GA>ApiAdapter, Cloud Scheduler
      API needed for doing jobs based operations.
    config: A yaml_parsing.ConfigYamlInfo object for the parsed YAML file we
      are going to process.
   existing_jobs: A list of jobs that already exist in the backend. Each job
      maps to an apis.cloudscheduler.<ver>.cloudscheduler<ver>_messages.Job
      instance.
  Returns:
    A list of responses received from the Cloud Scheduler APIs representing job
    states for every call made to create a job.
  """
  cron_yaml = config.parsed
  jobs_client = scheduler_api.jobs
  app_location = app.ResolveAppLocation(
      parsers.ParseProject(), locations_client=scheduler_api.locations)
  region_ref = parsers.ParseLocation(app_location).RelativeName()
  project = os.path.basename(str(parsers.ParseProject()))
  existing_jobs_dict = _BuildJobsMappingDict(existing_jobs, project)

  # Create a new job for any job that does not map exactly to jobs that already
  # exist in the backend.
  responses = []
  if cron_yaml.cron:
    for yaml_job in cron_yaml.cron:
      _ReplaceDefaultRetryParamsForYamlJob(yaml_job)
      job_key = _CreateUniqueJobKeyForYamlJob(yaml_job)
      if job_key in existing_jobs_dict and existing_jobs_dict[job_key]:
        # If the job already exists then we do not need to do anything.
        # TODO(b/169069379): Enhance to pop based on oldest/newest
        existing_jobs_dict[job_key].pop()
        continue
      job = CreateJobInstance(scheduler_api, yaml_job)
      responses.append(jobs_client.Create(region_ref, job))

  # TODO(b/169069379): Preserve next job execution for jobs whose only change
  # is description

  # Delete the jobs which are no longer in the YAML file
  for jobs_list in existing_jobs_dict.values():
    for yaml_job in jobs_list:
      jobs_client.Delete(yaml_job.name)

  return responses
