# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Utilities for parsing arguments to `gcloud tasks` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import encoding
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import http_encoding
import six  # pylint: disable=unused-import
from six.moves import filter  # pylint:disable=redefined-builtin
from six.moves import map  # pylint:disable=redefined-builtin


_PROJECT = properties.VALUES.core.project.GetOrFail


class NoFieldsSpecifiedError(exceptions.Error):
  """Error for when calling an update method with no fields specified."""


class FullTaskUnspecifiedError(exceptions.Error):
  """Error parsing task without specifing the queue or full path."""


class NoFieldsSpecifiedForHttpQueueError(exceptions.Error):
  """Error for calling a create-http-queue method with no override field specified.
  """


class QueueUpdatableConfiguration(object):
  """Data Class for queue configuration updates."""

  @classmethod
  def FromQueueTypeAndReleaseTrack(cls,
                                   queue_type,
                                   release_track=base.ReleaseTrack.GA):
    """Creates QueueUpdatableConfiguration from the given parameters."""
    config = cls()
    config.retry_config = {}
    config.rate_limits = {}
    config.app_engine_routing_override = {}
    config.http_target = {}
    config.stackdriver_logging_config = {}

    config.retry_config_mask_prefix = None
    config.rate_limits_mask_prefix = None
    config.app_engine_routing_override_mask_prefix = None
    config.http_target_mask_prefix = None
    config.stackdriver_logging_config_mask_prefix = None

    if queue_type == constants.PULL_QUEUE:
      config.retry_config = {
          'max_attempts': 'maxAttempts',
          'max_retry_duration': 'maxRetryDuration',
      }
      config.retry_config_mask_prefix = 'retryConfig'
    elif queue_type == constants.PUSH_QUEUE:
      if release_track == base.ReleaseTrack.ALPHA:
        config.retry_config = {
            'max_attempts': 'maxAttempts',
            'max_retry_duration': 'maxRetryDuration',
            'max_doublings': 'maxDoublings',
            'min_backoff': 'minBackoff',
            'max_backoff': 'maxBackoff',
        }
        config.rate_limits = {
            'max_tasks_dispatched_per_second': 'maxTasksDispatchedPerSecond',
            'max_concurrent_tasks': 'maxConcurrentTasks',
        }
        config.app_engine_routing_override = {
            'routing_override': 'appEngineRoutingOverride',
        }
        config.http_target = {
            'http_uri_override':
                'uriOverride',
            'http_method_override':
                'httpMethod',
            'http_header_override':
                'headerOverrides',
            'http_oauth_service_account_email_override':
                'oauthToken.serviceAccountEmail',
            'http_oauth_token_scope_override':
                'oauthToken.scope',
            'http_oidc_service_account_email_override':
                'oidcToken.serviceAccountEmail',
            'http_oidc_token_audience_override':
                'oidcToken.audience',
        }
        config.retry_config_mask_prefix = 'retryConfig'
        config.rate_limits_mask_prefix = 'rateLimits'
        config.app_engine_routing_override_mask_prefix = 'appEngineHttpTarget'
        config.http_target_mask_prefix = 'httpTarget'
      elif release_track == base.ReleaseTrack.BETA:
        config.retry_config = {
            'max_attempts': 'maxAttempts',
            'max_retry_duration': 'maxRetryDuration',
            'max_doublings': 'maxDoublings',
            'min_backoff': 'minBackoff',
            'max_backoff': 'maxBackoff',
        }
        config.rate_limits = {
            'max_dispatches_per_second': 'maxDispatchesPerSecond',
            'max_concurrent_dispatches': 'maxConcurrentDispatches',
            'max_burst_size': 'maxBurstSize',
        }
        config.app_engine_routing_override = {
            'routing_override': 'appEngineRoutingOverride',
        }
        config.http_target = {
            'http_uri_override':
                'uriOverride',
            'http_method_override':
                'httpMethod',
            'http_header_override':
                'headerOverrides',
            'http_oauth_service_account_email_override':
                'oauthToken.serviceAccountEmail',
            'http_oauth_token_scope_override':
                'oauthToken.scope',
            'http_oidc_service_account_email_override':
                'oidcToken.serviceAccountEmail',
            'http_oidc_token_audience_override':
                'oidcToken.audience',
        }
        config.stackdriver_logging_config = {
            'log_sampling_ratio': 'samplingRatio',
        }
        config.retry_config_mask_prefix = 'retryConfig'
        config.rate_limits_mask_prefix = 'rateLimits'
        config.app_engine_routing_override_mask_prefix = 'appEngineHttpQueue'
        config.http_target_mask_prefix = 'httpTarget'
        config.stackdriver_logging_config_mask_prefix = 'stackdriverLoggingConfig'
      else:
        config.retry_config = {
            'max_attempts': 'maxAttempts',
            'max_retry_duration': 'maxRetryDuration',
            'max_doublings': 'maxDoublings',
            'min_backoff': 'minBackoff',
            'max_backoff': 'maxBackoff',
        }
        config.rate_limits = {
            'max_dispatches_per_second': 'maxDispatchesPerSecond',
            'max_concurrent_dispatches': 'maxConcurrentDispatches',
        }
        config.app_engine_routing_override = {
            'routing_override': 'appEngineRoutingOverride',
        }
        config.http_target = {
            'http_uri_override':
                'uriOverride',
            'http_method_override':
                'httpMethod',
            'http_header_override':
                'headerOverrides',
            'http_oauth_service_account_email_override':
                'oauthToken.serviceAccountEmail',
            'http_oauth_token_scope_override':
                'oauthToken.scope',
            'http_oidc_service_account_email_override':
                'oidcToken.serviceAccountEmail',
            'http_oidc_token_audience_override':
                'oidcToken.audience',
        }
        config.stackdriver_logging_config = {
            'log_sampling_ratio': 'samplingRatio',
        }
        config.retry_config_mask_prefix = 'retryConfig'
        config.rate_limits_mask_prefix = 'rateLimits'
        config.app_engine_routing_override_mask_prefix = ''
        config.http_target_mask_prefix = 'httpTarget'
        config.stackdriver_logging_config_mask_prefix = 'stackdriverLoggingConfig'
    return config

  def _InitializedConfigsAndPrefixTuples(self):
    """Returns the initialized configs as a list of (config, prefix) tuples."""
    all_configs_and_prefixes = [
        (self.retry_config, self.retry_config_mask_prefix),
        (self.rate_limits, self.rate_limits_mask_prefix),
        (self.app_engine_routing_override,
         self.app_engine_routing_override_mask_prefix),
        (self.http_target, self.http_target_mask_prefix),
        (self.stackdriver_logging_config,
         self.stackdriver_logging_config_mask_prefix),
    ]
    return [(config, prefix)
            for (config, prefix) in all_configs_and_prefixes
            if config]

  def _GetSingleConfigToMaskMapping(self, config, prefix):
    """Build a map from each arg and its clear_ counterpart to a mask field."""
    fields_to_mask = dict()
    for field in config.keys():
      output_field = config[field]
      if prefix:
        fields_to_mask[field] = '{}.{}'.format(prefix, output_field)
      else:
        fields_to_mask[field] = output_field
      fields_to_mask[_EquivalentClearArg(field)] = fields_to_mask[field]
    return fields_to_mask

  def GetConfigToUpdateMaskMapping(self):
    """Builds mapping from config fields to corresponding update mask fields."""
    config_to_mask = dict()
    for (config, prefix) in self._InitializedConfigsAndPrefixTuples():
      config_to_mask.update(self._GetSingleConfigToMaskMapping(config, prefix))
    return config_to_mask

  def AllConfigs(self):
    return (list(self.retry_config.keys()) + list(self.rate_limits.keys()) +
            list(self.app_engine_routing_override.keys()) +
            list(self.http_target.keys()) +
            list(self.stackdriver_logging_config.keys()))


def ParseProject():
  return resources.REGISTRY.Parse(
      _PROJECT(),
      collection=constants.PROJECTS_COLLECTION)


def ParseLocation(location):
  return resources.REGISTRY.Parse(
      location,
      params={'projectsId': _PROJECT},
      collection=constants.LOCATIONS_COLLECTION)


def GetConsolePromptString(queue_string):
  """Parses a full queue reference and returns an abridged version.

  Args:
    queue_string: A full qualifying path for a queue which includes project and
      location, e.g. projects/PROJECT/locations/LOCATION/queues/QUEUE

  Returns:
    A shortened string for the full queue ref which has only the location and
    the queue (LOCATION/QUEUE). For example:
      'projects/myproject/location/us-east1/queue/myqueue' => 'us-east1/myqueue'
  """

  match = re.match(
      r'projects\/.*\/locations\/(?P<location>.*)\/queues\/(?P<queue>.*)',
      queue_string)
  if match:
    return '{}/{}'.format(match.group('location'), match.group('queue'))
  return queue_string


def ParseQueue(queue, location=None):
  """Parses an id or uri for a queue.

  Args:
    queue: An id, self-link, or relative path of a queue resource.
    location: The location of the app associated with the active project.

  Returns:
    A queue resource reference, or None if passed-in queue is Falsy.
  """
  if not queue:
    return None

  queue_ref = None
  try:
    queue_ref = resources.REGISTRY.Parse(queue,
                                         collection=constants.QUEUES_COLLECTION)
  except resources.RequiredFieldOmittedException:
    app_location = location or app.ResolveAppLocation(ParseProject())
    location_ref = ParseLocation(app_location)
    queue_ref = resources.REGISTRY.Parse(
        queue, params={'projectsId': location_ref.projectsId,
                       'locationsId': location_ref.locationsId},
        collection=constants.QUEUES_COLLECTION)
  return queue_ref


def ParseTask(task, queue_ref=None):
  """Parses an id or uri for a task."""
  params = queue_ref.AsDict() if queue_ref else None
  try:
    return resources.REGISTRY.Parse(task,
                                    collection=constants.TASKS_COLLECTION,
                                    params=params)
  except resources.RequiredFieldOmittedException:
    raise FullTaskUnspecifiedError(
        'Must specify either the fully qualified task path or the queue flag.')


def ParseTaskId(args):
  """Parses an id for a task."""
  return args.task_id if args.task_id else None


def ParseFullKmsKeyName(kms_key_name):
  """Parses and retrieves the segments of a full KMS key name."""
  if not kms_key_name:
    return None

  match = re.match(
      r'projects\/(?P<project>.*)\/locations\/(?P<location>.*)\/keyRings\/(?P<keyring>.*)\/cryptoKeys\/(?P<key>.*)',
      kms_key_name,
  )
  if match:
    return [
        match.group('project'),
        match.group('location'),
        match.group('keyring'),
        match.group('key'),
    ]
  return None


def ParseKmsUpdateArgs(args):
  """Parses KMS key value."""
  location_id = args.location if args.location else None
  full_kms_key_name = None
  parse_result = ParseFullKmsKeyName(args.kms_key_name)

  # Either a full kms-key-name is provided, or a short name along with other
  # params should be provided. If there is parse_reulst, then it is a full name.
  # If not, the user must provide all parts.
  if parse_result is not None:
    location_id = parse_result[1]
    full_kms_key_name = args.kms_key_name
  elif (
      args.kms_key_name
      and args.kms_keyring
      and args.location
  ):
    full_kms_key_name = 'projects/{kms_project_id}/locations/{location_id}/keyRings/{kms_keyring}/cryptoKeys/{kms_key_name}'.format(
        kms_project_id=args.kms_project if args.kms_project else _PROJECT(),
        location_id=location_id,
        kms_keyring=args.kms_keyring,
        kms_key_name=args.kms_key_name,  # short key name
    )

  return _PROJECT(), full_kms_key_name, location_id


def ParseKmsDescribeArgs(args):
  """Parses KMS describe args."""
  location_id = args.location if args.location else None
  project_id = _PROJECT()

  return project_id, location_id


def ParseKmsClearArgs(args):
  """Parses KMS clear args."""
  location_id = args.location if args.location else None

  return _PROJECT(), location_id


def ExtractLocationRefFromQueueRef(queue_ref):
  params = queue_ref.AsDict()
  del params['queuesId']
  location_ref = resources.REGISTRY.Parse(
      None, params=params, collection=constants.LOCATIONS_COLLECTION)
  return location_ref


def ParseCreateOrUpdateQueueArgs(
    args,
    queue_type,
    messages,
    is_update=False,
    release_track=base.ReleaseTrack.GA,
    http_queue=True,
):
  """Parses queue level args."""
  if release_track == base.ReleaseTrack.ALPHA:
    app_engine_http_target = _ParseAppEngineHttpTargetArgs(
        args, queue_type, messages
    )
    http_target = (
        _ParseHttpTargetArgs(args, queue_type, messages) if http_queue else None
    )

    return messages.Queue(
        retryConfig=_ParseRetryConfigArgs(
            args, queue_type, messages, is_update, is_alpha=True
        ),
        rateLimits=_ParseAlphaRateLimitsArgs(
            args, queue_type, messages, is_update
        ),
        pullTarget=_ParsePullTargetArgs(args, queue_type, messages, is_update),
        appEngineHttpTarget=app_engine_http_target,
        httpTarget=http_target,
    )
  elif release_track == base.ReleaseTrack.BETA:
    http_target = (
        _ParseHttpTargetArgs(args, queue_type, messages) if http_queue else None
    )

    return messages.Queue(
        retryConfig=_ParseRetryConfigArgs(
            args, queue_type, messages, is_update, is_alpha=False
        ),
        rateLimits=_ParseRateLimitsArgs(args, queue_type, messages, is_update),
        stackdriverLoggingConfig=_ParseStackdriverLoggingConfigArgs(
            args, queue_type, messages, is_update
        ),
        appEngineHttpQueue=_ParseAppEngineHttpQueueArgs(
            args, queue_type, messages
        ),
        httpTarget=http_target,
        type=_ParseQueueType(args, queue_type, messages, is_update),
    )
  else:
    http_target = (
        _ParseHttpTargetArgs(args, queue_type, messages) if http_queue else None
    )
    return messages.Queue(
        retryConfig=_ParseRetryConfigArgs(
            args, queue_type, messages, is_update, is_alpha=False
        ),
        rateLimits=_ParseRateLimitsArgs(args, queue_type, messages, is_update),
        stackdriverLoggingConfig=_ParseStackdriverLoggingConfigArgs(
            args, queue_type, messages, is_update
        ),
        appEngineRoutingOverride=_ParseAppEngineRoutingOverrideArgs(
            args, queue_type, messages
        ),
        httpTarget=http_target,
    )


def GetHttpTargetArgs(queue_config):
  """Returns a pair of each http target attribute and its value in the queue."""
  # pylint: disable=g-long-ternary
  http_uri_override = (
      queue_config.httpTarget.uriOverride
      if queue_config.httpTarget is not None
      else None
  )
  http_method_override = (
      queue_config.httpTarget.httpMethod
      if queue_config.httpTarget is not None
      else None
  )
  http_header_override = (
      queue_config.httpTarget.headerOverrides
      if queue_config.httpTarget is not None
      else None
  )
  http_oauth_email_override = (
      queue_config.httpTarget.oauthToken.serviceAccountEmail
      if (
          queue_config.httpTarget is not None
          and queue_config.httpTarget.oauthToken is not None
      )
      else None
  )
  http_oauth_scope_override = (
      queue_config.httpTarget.oauthToken.scope
      if (
          queue_config.httpTarget is not None
          and queue_config.httpTarget.oauthToken is not None
      )
      else None
  )
  http_oidc_email_override = (
      queue_config.httpTarget.oidcToken.serviceAccountEmail
      if (
          queue_config.httpTarget is not None
          and queue_config.httpTarget.oidcToken is not None
      )
      else None
  )
  http_oidc_audience_override = (
      queue_config.httpTarget.oidcToken.audience
      if (
          queue_config.httpTarget is not None
          and queue_config.httpTarget.oidcToken is not None
      )
      else None
  )

  return {
      'http_uri_override': http_uri_override,
      'http_method_override': http_method_override,
      'http_header_override': http_header_override,
      'http_oauth_email_override': http_oauth_email_override,
      'http_oauth_scope_override': http_oauth_scope_override,
      'http_oidc_email_override': http_oidc_email_override,
      'http_oidc_audience_override': http_oidc_audience_override,
  }


def ExtractTargetFromAppEngineHostUrl(job, project):
  """Extracts any target (service) if it exists in the appEngineRouting field.

  Args:
    job: An instance of job fetched from the backend.
    project: The base name of the project.

  Returns:
    The target if it exists in the URL, or if it is present in the service
    attribute of the appEngineRouting field, returns None otherwise.
    Some examples are:
      'alpha.some_project.uk.r.appspot.com' => 'alpha'
      'some_project.uk.r.appspot.com' => None
  """
  # For cron jobs created with the new scheduler FE API, target is stored as a
  # service attribute in the appEngineRouting field
  target = None
  try:
    target = job.appEngineHttpTarget.appEngineRouting.service
  except AttributeError:
    pass
  if target:
    return target

  # For cron jobs created using admin-console-hr, target is prepended to the
  # host url
  host_url = None
  try:
    host_url = job.appEngineHttpTarget.appEngineRouting.host
  except AttributeError:
    pass
  if not host_url:
    return None
  delimiter = '.{}.'.format(project)
  return host_url.split(delimiter, 1)[0] if delimiter in host_url else None


def ParseCreateTaskArgs(args, task_type, messages,
                        release_track=base.ReleaseTrack.GA):
  """Parses task level args."""
  if release_track == base.ReleaseTrack.ALPHA:
    return messages.Task(
        scheduleTime=args.schedule_time,
        pullMessage=_ParsePullMessageArgs(args, task_type, messages),
        appEngineHttpRequest=_ParseAlphaAppEngineHttpRequestArgs(
            args, task_type, messages))
  else:
    return messages.Task(
        scheduleTime=args.schedule_time,
        appEngineHttpRequest=_ParseAppEngineHttpRequestArgs(args, task_type,
                                                            messages),
        httpRequest=_ParseHttpRequestArgs(args, task_type, messages))


def CheckUpdateArgsSpecified(args, queue_type,
                             release_track=base.ReleaseTrack.GA):
  """Verifies that args are valid for updating a queue."""
  updatable_config = QueueUpdatableConfiguration.FromQueueTypeAndReleaseTrack(
      queue_type, release_track)

  if _AnyArgsSpecified(args, updatable_config.AllConfigs(), clear_args=True):
    return
  raise NoFieldsSpecifiedError('Must specify at least one field to update.')


def GetSpecifiedFieldsMask(args, queue_type,
                           release_track=base.ReleaseTrack.GA):
  """Returns the mask fields to use with the given args."""
  updatable_config = QueueUpdatableConfiguration.FromQueueTypeAndReleaseTrack(
      queue_type, release_track)

  specified_args = _SpecifiedArgs(
      args, updatable_config.AllConfigs(), clear_args=True)

  args_to_mask = updatable_config.GetConfigToUpdateMaskMapping()
  masks_field = [args_to_mask[arg] for arg in specified_args]
  if hasattr(args, 'type') and args.type == constants.PULL_TASK:
    masks_field.append('type')
  return sorted(set(masks_field))


def _SpecifiedArgs(specified_args_object, args_list, clear_args=False):
  """Returns the list of known arguments in the specified list."""

  def _IsSpecifiedWrapper(arg):
    """Wrapper function for Namespace.IsSpecified function.

    We need this function to be support being able to modify certain queue
    attributes internally using `gcloud app deploy queue.yaml` without exposing
    the same functionality via `gcloud tasks queues create/update`.

    Args:
      arg: The argument we are trying to check if specified.

    Returns:
      True if the argument was specified at CLI invocation, False otherwise.
    """
    # HTTP queue overrides should be ignored when running 'app deploy'
    http_queue_args = [
        'http_uri_override',
        'http_method_override',
        'http_header_override',
        'http_oauth_service_account_email_override',
        'http_oauth_token_scope_override',
        'http_oidc_service_account_email_override',
        'http_oidc_token_audience_override',
    ]
    try:
      return specified_args_object.IsSpecified(arg)
    except parser_errors.UnknownDestinationException:
      if arg in ('max_burst_size', 'clear_max_burst_size') or any(
          flag in arg for flag in http_queue_args
      ):
        return False
      raise

  clear_args_list = []
  if clear_args:
    clear_args_list = [_EquivalentClearArg(a) for a in args_list]
  return filter(_IsSpecifiedWrapper, args_list + clear_args_list)


def _AnyArgsSpecified(specified_args_object, args_list, clear_args=False):
  """Returns whether there are known arguments in the specified list."""
  return any(_SpecifiedArgs(specified_args_object, args_list, clear_args))


def _EquivalentClearArg(arg):
  return 'clear_{}'.format(arg)


def _ParseRetryConfigArgs(args, queue_type, messages, is_update,
                          is_alpha=False):
  """Parses the attributes of 'args' for Queue.retryConfig."""
  if (queue_type == constants.PULL_QUEUE and
      _AnyArgsSpecified(args, ['max_attempts', 'max_retry_duration'],
                        clear_args=is_update)):
    retry_config = messages.RetryConfig(
        maxRetryDuration=args.max_retry_duration)
    _AddMaxAttemptsFieldsFromArgs(args, retry_config, is_alpha)
    return retry_config

  if (queue_type == constants.PUSH_QUEUE and
      _AnyArgsSpecified(args, ['max_attempts', 'max_retry_duration',
                               'max_doublings', 'min_backoff', 'max_backoff'],
                        clear_args=is_update)):
    retry_config = messages.RetryConfig(
        maxRetryDuration=args.max_retry_duration,
        maxDoublings=args.max_doublings, minBackoff=args.min_backoff,
        maxBackoff=args.max_backoff)
    _AddMaxAttemptsFieldsFromArgs(args, retry_config, is_alpha)
    return retry_config


def _AddMaxAttemptsFieldsFromArgs(args, config_object, is_alpha=False):
  if args.IsSpecified('max_attempts'):
    # args.max_attempts is a BoundedInt and so None means unlimited
    if args.max_attempts is None:
      if is_alpha:
        config_object.unlimitedAttempts = True
      else:
        config_object.maxAttempts = -1
    else:
      config_object.maxAttempts = args.max_attempts


def _ParseAlphaRateLimitsArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.rateLimits."""
  if (queue_type == constants.PUSH_QUEUE and
      _AnyArgsSpecified(args, ['max_tasks_dispatched_per_second',
                               'max_concurrent_tasks'],
                        clear_args=is_update)):
    return messages.RateLimits(
        maxTasksDispatchedPerSecond=args.max_tasks_dispatched_per_second,
        maxConcurrentTasks=args.max_concurrent_tasks)


def _ParseRateLimitsArgs(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.rateLimits."""
  if (
      queue_type == constants.PUSH_QUEUE and
      _AnyArgsSpecified(
          args,
          ['max_dispatches_per_second', 'max_concurrent_dispatches',
           'max_burst_size'],
          clear_args=is_update)):
    max_burst_size = (
        args.max_burst_size if hasattr(args, 'max_burst_size') else None)
    return messages.RateLimits(
        maxDispatchesPerSecond=args.max_dispatches_per_second,
        maxConcurrentDispatches=args.max_concurrent_dispatches,
        maxBurstSize=max_burst_size)


def _ParseStackdriverLoggingConfigArgs(args, queue_type, messages,
                                       is_update):
  """Parses the attributes of 'args' for Queue.stackdriverLoggingConfig."""
  if (queue_type != constants.PULL_QUEUE and
      _AnyArgsSpecified(args, ['log_sampling_ratio'], clear_args=is_update)):
    return messages.StackdriverLoggingConfig(
        samplingRatio=args.log_sampling_ratio)


def _ParsePullTargetArgs(unused_args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.pullTarget."""
  if queue_type == constants.PULL_QUEUE and not is_update:
    return messages.PullTarget()


def _ParseQueueType(args, queue_type, messages, is_update):
  """Parses the attributes of 'args' for Queue.type."""
  if (
      (hasattr(args, 'type') and args.type == constants.PULL_QUEUE) or
      (queue_type == constants.PULL_QUEUE and not is_update)
  ):
    return messages.Queue.TypeValueValuesEnum.PULL
  return messages.Queue.TypeValueValuesEnum.PUSH


def _ParseAppEngineHttpTargetArgs(args, queue_type, messages):
  """Parses the attributes of 'args' for Queue.appEngineHttpTarget."""
  if queue_type == constants.PUSH_QUEUE:
    routing_override = _ParseAppEngineRoutingOverrideArgs(
        args, queue_type, messages)
    if routing_override is None:
      return None
    return messages.AppEngineHttpTarget(
        appEngineRoutingOverride=routing_override)


def _ParseHttpTargetArgs(args, queue_type, messages):
  """Parses the attributes of 'args' for Queue.HttpTarget."""
  if queue_type == constants.PUSH_QUEUE:
    uri_override = _ParseHttpRoutingOverrideArgs(args, messages)

    http_method = (
        messages.HttpTarget.HttpMethodValueValuesEnum(
            args.http_method_override.upper())
        if args.IsSpecified('http_method_override') else None)

    oauth_token = _ParseHttpTargetOAuthArgs(args, messages)
    oidc_token = _ParseHttpTargetOidcArgs(args, messages)

    if (
        uri_override is None
        and http_method is None
        and oauth_token is None
        and oidc_token is None
    ):
      return None

    return messages.HttpTarget(
        uriOverride=uri_override,
        headerOverrides=_ParseHttpTargetHeaderArg(args, messages),
        httpMethod=http_method,
        oauthToken=oauth_token,
        oidcToken=oidc_token)


def _ParseAppEngineHttpQueueArgs(args, queue_type, messages):
  """Parses the attributes of 'args' for Queue.appEngineHttpQueue."""
  if queue_type == constants.PUSH_QUEUE:
    routing_override = _ParseAppEngineRoutingOverrideArgs(
        args, queue_type, messages
    )
    return messages.AppEngineHttpQueue(
        appEngineRoutingOverride=routing_override
    )


def _ParseAppEngineRoutingOverrideArgs(args, queue_type, messages):
  """Parses the attributes of 'args' for AppEngineRouting."""
  if queue_type == constants.PUSH_QUEUE:
    if args.IsSpecified('routing_override'):
      return messages.AppEngineRouting(**args.routing_override)
    return None


def _ParseHttpRoutingOverrideArgs(args, messages):
  """Parses the attributes of 'args' for HTTP Routing."""
  if args.IsSpecified('http_uri_override'):
    return _ParseUriOverride(messages=messages, **args.http_uri_override)
  return None


def _ParseUriOverride(messages,
                      scheme=None,
                      host=None,
                      port=None,
                      path=None,
                      query=None,
                      mode=None):
  """Parses the attributes of 'args' for URI Override."""
  scheme = (
      messages.UriOverride.SchemeValueValuesEnum(scheme.upper())
      if scheme else None)
  port = int(port) if port else None
  uri_override_enforce_mode = (
      messages.UriOverride.UriOverrideEnforceModeValueValuesEnum(mode.upper())
      if mode else None)
  return messages.UriOverride(
      scheme=scheme,
      host=host,
      port=port,
      pathOverride=messages.PathOverride(path=path),
      queryOverride=messages.QueryOverride(queryParams=query),
      uriOverrideEnforceMode=uri_override_enforce_mode)


def _ParsePullMessageArgs(args, task_type, messages):
  if task_type == constants.PULL_TASK:
    return messages.PullMessage(payload=_ParsePayloadArgs(args), tag=args.tag)


def _ParseAlphaAppEngineHttpRequestArgs(args, task_type, messages):
  """Parses the attributes of 'args' for Task.appEngineHttpRequest."""
  if task_type == constants.APP_ENGINE_TASK:
    routing = (
        messages.AppEngineRouting(**args.routing) if args.routing else None)
    http_method = (messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        args.method.upper()) if args.IsSpecified('method') else None)
    return messages.AppEngineHttpRequest(
        appEngineRouting=routing, httpMethod=http_method,
        payload=_ParsePayloadArgs(args), relativeUrl=args.url,
        headers=_ParseHeaderArg(args,
                                messages.AppEngineHttpRequest.HeadersValue))


def _ParsePayloadArgs(args):
  if args.IsSpecified('payload_file'):
    payload = console_io.ReadFromFileOrStdin(args.payload_file, binary=False)
  elif args.IsSpecified('payload_content'):
    payload = args.payload_content
  else:
    return None
  return http_encoding.Encode(payload)


def _ParseAppEngineHttpRequestArgs(args, task_type, messages):
  """Parses the attributes of 'args' for Task.appEngineHttpRequest."""
  if task_type == constants.APP_ENGINE_TASK:
    routing = (
        messages.AppEngineRouting(**args.routing) if args.routing else None)
    http_method = (messages.AppEngineHttpRequest.HttpMethodValueValuesEnum(
        args.method.upper()) if args.IsSpecified('method') else None)
    return messages.AppEngineHttpRequest(
        appEngineRouting=routing, httpMethod=http_method,
        body=_ParseBodyArgs(args), relativeUri=args.relative_uri,
        headers=_ParseHeaderArg(args,
                                messages.AppEngineHttpRequest.HeadersValue))


def _ParseHttpRequestArgs(args, task_type, messages):
  """Parses the attributes of 'args' for Task.httpRequest."""
  if task_type == constants.HTTP_TASK:
    http_method = (messages.HttpRequest.HttpMethodValueValuesEnum(
        args.method.upper()) if args.IsSpecified('method') else None)
    return messages.HttpRequest(
        headers=_ParseHeaderArg(args, messages.HttpRequest.HeadersValue),
        httpMethod=http_method, body=_ParseBodyArgs(args), url=args.url,
        oauthToken=_ParseOAuthArgs(args, messages),
        oidcToken=_ParseOidcArgs(args, messages))


def _ParseBodyArgs(args):
  if args.IsSpecified('body_file'):
    body = console_io.ReadFromFileOrStdin(args.body_file, binary=False)
  elif args.IsSpecified('body_content'):
    body = args.body_content
  else:
    return None
  return http_encoding.Encode(body)


def _ParseOAuthArgs(args, messages):
  if args.IsSpecified('oauth_service_account_email'):
    return messages.OAuthToken(
        serviceAccountEmail=args.oauth_service_account_email,
        scope=args.oauth_token_scope)
  else:
    return None


def _ParseOidcArgs(args, messages):
  if args.IsSpecified('oidc_service_account_email'):
    return messages.OidcToken(
        serviceAccountEmail=args.oidc_service_account_email,
        audience=args.oidc_token_audience)
  else:
    return None


def _ParseHttpTargetOAuthArgs(args, messages):
  if args.IsSpecified('http_oauth_service_account_email_override'):
    return messages.OAuthToken(
        serviceAccountEmail=args.http_oauth_service_account_email_override,
        scope=args.http_oauth_token_scope_override)
  else:
    return None


def _ParseHttpTargetOidcArgs(args, messages):
  if args.IsSpecified('http_oidc_service_account_email_override'):
    return messages.OidcToken(
        serviceAccountEmail=args.http_oidc_service_account_email_override,
        audience=args.http_oidc_token_audience_override)
  else:
    return None


def _ParseHeaderArg(args, headers_value):
  if args.header:
    headers_dict = {k: v for k, v in map(_SplitHeaderArgValue, args.header)}
    return encoding.DictToAdditionalPropertyMessage(headers_dict, headers_value)


def _SplitHeaderArgValue(header_arg_value):
  key, value = header_arg_value.split(':', 1)
  return key, value.lstrip()


def _ParseHttpTargetHeaderArg(args, messages):
  """Converts header values into a list of headers and returns the list."""
  map_ = []
  if args.IsSpecified('http_header_override'):
    headers_dict = {
        k: v for k, v in map(_SplitHeaderArgValue, args.http_header_override)
    }

    items = sorted(headers_dict.items())
    for key, value in items:
      header_override = messages.HeaderOverride(
          header=messages.Header(key=key.encode(), value=value.encode()))
      map_.append(header_override)

  return map_


def FormatLeaseDuration(lease_duration):
  return '{}s'.format(lease_duration)


def ParseTasksLeaseFilterFlags(args):
  if args.oldest_tag:
    return 'tag_function=oldest_tag()'
  if args.IsSpecified('tag'):
    return 'tag="{}"'.format(args.tag)


def QueuesUriFunc(queue):
  return resources.REGISTRY.Parse(
      queue.name,
      params={'projectsId': _PROJECT},
      collection=constants.QUEUES_COLLECTION).SelfLink()


def TasksUriFunc(task):
  return resources.REGISTRY.Parse(
      task.name,
      params={'projectsId': _PROJECT},
      collection=constants.TASKS_COLLECTION).SelfLink()


def LocationsUriFunc(task):
  return resources.REGISTRY.Parse(
      task.name,
      params={'projectsId': _PROJECT},
      collection=constants.LOCATIONS_COLLECTION).SelfLink()
