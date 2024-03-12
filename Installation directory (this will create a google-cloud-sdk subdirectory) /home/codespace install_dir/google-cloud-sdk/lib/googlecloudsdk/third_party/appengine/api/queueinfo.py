#
# Copyright 2009 Google LLC. All Rights Reserved.
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

"""QueueInfo tools.

QueueInfo is a library for working with QueueInfo records, describing task queue
entries for an application. QueueInfo loads the records from `queue.yaml`. To
learn more about the parameters you can specify in `queue.yaml`, review the
`queue.yaml reference guide`_.

.. _queue.yaml reference guide:
   https://cloud.google.com/appengine/docs/python/config/queueref
"""

from __future__ import absolute_import
from __future__ import unicode_literals
__author__ = 'arb@google.com (Anthony Baxter)'

# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

import os

# pylint: disable=g-import-not-at-top
if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import appinfo
  from google.appengine.api import validation
  from google.appengine.api import yaml_builder
  from google.appengine.api import yaml_listener
  from google.appengine.api import yaml_object
  from google.appengine.api.taskqueue import taskqueue_service_pb
else:
  from googlecloudsdk.third_party.appengine.api import appinfo
  from googlecloudsdk.third_party.appengine.api import validation
  from googlecloudsdk.third_party.appengine.api import yaml_builder
  from googlecloudsdk.third_party.appengine.api import yaml_listener
  from googlecloudsdk.third_party.appengine.api import yaml_object
  from googlecloudsdk.third_party.appengine.api.taskqueue import taskqueue_service_pb
# pylint: enable=g-import-not-at-top

# This is exactly the same regex as is in `api/taskqueue/taskqueue_service.cc`
_NAME_REGEX = r'^[A-Za-z0-9-]{0,499}$'
_RATE_REGEX = r'^(0|[0-9]+(\.[0-9]*)?/[smhd])'
_TOTAL_STORAGE_LIMIT_REGEX = r'^([0-9]+(\.[0-9]*)?[BKMGT]?)'
# The JSON parser converts all truthy/falsy values to True|False.
# See go/yamllint#truthy for more details.
_RESUME_PAUSED_QUEUES = r'(True)|(False)'
_MODE_REGEX = r'(pull)|(push)'

# we don't have to pull that file into python_lib for the taskqueue stub to work
# in production.
MODULE_ID_RE_STRING = r'(?!-)[a-z\d\-]{1,63}'
# NOTE(user): The length here must remain 100 for backwards compatibility,
# see b/5485871 for more information.
MODULE_VERSION_RE_STRING = r'(?!-)[a-z\d\-]{1,100}'
_VERSION_REGEX = r'^(?:(?:(%s)\.)?)(%s)$' % (MODULE_VERSION_RE_STRING,
                                            MODULE_ID_RE_STRING)

QUEUE = 'queue'

NAME = 'name'
RATE = 'rate'
BUCKET_SIZE = 'bucket_size'
MODE = 'mode'
TARGET = 'target'
MAX_CONCURRENT_REQUESTS = 'max_concurrent_requests'
TOTAL_STORAGE_LIMIT = 'total_storage_limit'
RESUME_PAUSED_QUEUES = 'resume_paused_queues'

BYTE_SUFFIXES = 'BKMGT'

RETRY_PARAMETERS = 'retry_parameters'
TASK_RETRY_LIMIT = 'task_retry_limit'
TASK_AGE_LIMIT = 'task_age_limit'
MIN_BACKOFF_SECONDS = 'min_backoff_seconds'
MAX_BACKOFF_SECONDS = 'max_backoff_seconds'
MAX_DOUBLINGS = 'max_doublings'

ACL = 'acl'
USER_EMAIL = 'user_email'
WRITER_EMAIL = 'writer_email'


class MalformedQueueConfiguration(Exception):
  """The configuration file for the task queue is malformed."""


class RetryParameters(validation.Validated):
  """Specifies the retry parameters for a single task queue."""
  ATTRIBUTES = {
      TASK_RETRY_LIMIT: validation.Optional(validation.TYPE_INT),
      TASK_AGE_LIMIT: validation.Optional(validation.TimeValue()),
      MIN_BACKOFF_SECONDS: validation.Optional(validation.TYPE_FLOAT),
      MAX_BACKOFF_SECONDS: validation.Optional(validation.TYPE_FLOAT),
      MAX_DOUBLINGS: validation.Optional(validation.TYPE_INT),
  }


class Acl(validation.Validated):
  """Controls the access control list for a single task queue."""
  ATTRIBUTES = {
      USER_EMAIL: validation.Optional(validation.TYPE_STR),
      WRITER_EMAIL: validation.Optional(validation.TYPE_STR),
  }


class QueueEntry(validation.Validated):
  """Describes a single task queue."""
  ATTRIBUTES = {
      NAME: _NAME_REGEX,
      RATE: validation.Optional(_RATE_REGEX),
      MODE: validation.Optional(_MODE_REGEX),
      BUCKET_SIZE: validation.Optional(validation.TYPE_INT),
      MAX_CONCURRENT_REQUESTS: validation.Optional(validation.TYPE_INT),
      RETRY_PARAMETERS: validation.Optional(RetryParameters),
      ACL: validation.Optional(validation.Repeated(Acl)),
      # TODO(user): http://b/issue?id=6231287 to split this out to engine
      # and version.
      TARGET: validation.Optional(_VERSION_REGEX),
  }


class QueueInfoExternal(validation.Validated):
  """Describes all of the queue entries for an application."""
  ATTRIBUTES = {
      appinfo.APPLICATION: validation.Optional(appinfo.APPLICATION_RE_STRING),
      TOTAL_STORAGE_LIMIT: validation.Optional(_TOTAL_STORAGE_LIMIT_REGEX),
      RESUME_PAUSED_QUEUES: validation.Optional(_RESUME_PAUSED_QUEUES),
      QUEUE: validation.Optional(validation.Repeated(QueueEntry)),
  }


def LoadSingleQueue(queue_info, open_fn=None):
  """Loads a `queue.yaml` file/string and returns a `QueueInfoExternal` object.

  Args:
    queue_info: The contents of a `queue.yaml` file, as a string.
    open_fn: Function for opening files. Unused.

  Returns:
    A `QueueInfoExternal` object.
  """
  builder = yaml_object.ObjectBuilder(QueueInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(queue_info)

  queue_info = handler.GetResults()
  if len(queue_info) < 1:
    raise MalformedQueueConfiguration('Empty queue configuration.')
  if len(queue_info) > 1:
    raise MalformedQueueConfiguration('Multiple queue: sections '
                                      'in configuration.')
  return queue_info[0]


def ParseRate(rate):
  """Parses a rate string in the form `number/unit`, or the literal `0`.

  The unit is one of `s` (seconds), `m` (minutes), `h` (hours) or `d` (days).

  Args:
    rate: The string that contains the rate.

  Returns:
    A floating point number that represents the `rate/second`.

  Raises:
    MalformedQueueConfiguration: If the rate is invalid.
  """
  if rate == "0":
    return 0.0
  elements = rate.split('/')
  if len(elements) != 2:
    raise MalformedQueueConfiguration('Rate "%s" is invalid.' % rate)
  number, unit = elements
  try:
    number = float(number)
  except ValueError:
    raise MalformedQueueConfiguration('Rate "%s" is invalid:'
                                          ' "%s" is not a number.' %
                                          (rate, number))
  if unit not in 'smhd':
    raise MalformedQueueConfiguration('Rate "%s" is invalid:'
                                          ' "%s" is not one of s, m, h, d.' %
                                          (rate, unit))
  if unit == 's':
    return number
  if unit == 'm':
    return number/60
  if unit == 'h':
    return number/(60 * 60)
  if unit == 'd':
    return number/(24 * 60 * 60)


def ParseTotalStorageLimit(limit):
  """Parses a string representing the storage bytes limit.

  Optional limit suffixes are:
      - `B` (bytes)
      - `K` (kilobytes)
      - `M` (megabytes)
      - `G` (gigabytes)
      - `T` (terabytes)

  Args:
    limit: The string that specifies the storage bytes limit.

  Returns:
    An integer that represents the storage limit in bytes.

  Raises:
    MalformedQueueConfiguration: If the limit argument isn't a valid Python
        double followed by an optional suffix.
  """
  limit = limit.strip()
  if not limit:
    raise MalformedQueueConfiguration('Total Storage Limit must not be empty.')
  try:
    if limit[-1] in BYTE_SUFFIXES:
      number = float(limit[0:-1])
      for c in BYTE_SUFFIXES:
        if limit[-1] != c:
          number = number * 1024
        else:
          return int(number)
    else:
      # We won't accept fractional bytes. If someone asks for
      # 1.1e12 bytes, too bad.
      return int(limit)
  except ValueError:
    raise MalformedQueueConfiguration('Total Storage Limit "%s" is invalid.' %
                                      limit)


def ParseTaskAgeLimit(age_limit):
  """Parses a string representing the task's age limit (maximum allowed age).

  The string must be a non-negative integer or floating point number followed by
  one of `s`, `m`, `h`, or `d` (seconds, minutes, hours, or days, respectively).

  Args:
    age_limit: The string that contains the task age limit.

  Returns:
    An integer that represents the age limit in seconds.

  Raises:
    MalformedQueueConfiguration: If the limit argument isn't a valid Python
        double followed by a required suffix.
 """
  age_limit = age_limit.strip()
  if not age_limit:
    raise MalformedQueueConfiguration('Task Age Limit must not be empty.')
  unit = age_limit[-1]
  if unit not in "smhd":
    raise MalformedQueueConfiguration('Task Age_Limit must be in s (seconds), '
                                      'm (minutes), h (hours), or d (days)')
  try:
    number = float(age_limit[0:-1])
    if unit == 's':
      return int(number)
    if unit == 'm':
      return int(number * 60)
    if unit == 'h':
      return int(number * 3600)
    if unit == 'd':
      return int(number * 86400)

  except ValueError:
    raise MalformedQueueConfiguration('Task Age_Limit "%s" is invalid.' %
                                      age_limit)


def TranslateRetryParameters(retry):
  """Populates a `TaskQueueRetryParameters` from a `queueinfo.RetryParameters`.

  Args:
    retry: A `queueinfo.RetryParameters` that is read from `queue.yaml` that
        describes the queue's retry parameters.

  Returns:
    A `taskqueue_service_pb.TaskQueueRetryParameters` proto populated with the
    data from `retry`.

  Raises:
    MalformedQueueConfiguration: If the retry parameters are invalid.
  """
  params = taskqueue_service_pb.TaskQueueRetryParameters()
  if retry.task_retry_limit is not None:
    params.set_retry_limit(int(retry.task_retry_limit))
  if retry.task_age_limit is not None:
    # This could raise MalformedQueueConfiguration.
    params.set_age_limit_sec(ParseTaskAgeLimit(retry.task_age_limit))
  if retry.min_backoff_seconds is not None:
    params.set_min_backoff_sec(float(retry.min_backoff_seconds))
  if retry.max_backoff_seconds is not None:
    params.set_max_backoff_sec(float(retry.max_backoff_seconds))
  if retry.max_doublings is not None:
    params.set_max_doublings(int(retry.max_doublings))

  # We enforce a couple of friendly rules here with `min_backoff_sec` and
  # `max_backoff_sec`. If only one is set, the other gets a default value. It
  # is not fair to users if the default (which can change) could cause their
  # parameters to violate `min_backoff_sec()` <= `max_backoff_sec()`.
  if params.has_min_backoff_sec() and not params.has_max_backoff_sec():
    if params.min_backoff_sec() > params.max_backoff_sec():
      params.set_max_backoff_sec(params.min_backoff_sec())

  if not params.has_min_backoff_sec() and params.has_max_backoff_sec():
    if params.min_backoff_sec() > params.max_backoff_sec():
      params.set_min_backoff_sec(params.max_backoff_sec())

  # Validation.
  if params.has_retry_limit() and params.retry_limit() < 0:
    raise MalformedQueueConfiguration(
        'Task retry limit must not be less than zero.')

  if params.has_age_limit_sec() and not params.age_limit_sec() > 0:
    raise MalformedQueueConfiguration(
        'Task age limit must be greater than zero.')

  if params.has_min_backoff_sec() and params.min_backoff_sec() < 0:
    raise MalformedQueueConfiguration(
        'Min backoff seconds must not be less than zero.')

  if params.has_max_backoff_sec() and params.max_backoff_sec() < 0:
    raise MalformedQueueConfiguration(
        'Max backoff seconds must not be less than zero.')

  if params.has_max_doublings() and params.max_doublings() < 0:
    raise MalformedQueueConfiguration(
        'Max doublings must not be less than zero.')

  if (params.has_min_backoff_sec() and params.has_max_backoff_sec() and
      params.min_backoff_sec() > params.max_backoff_sec()):
    raise MalformedQueueConfiguration(
        'Min backoff sec must not be greater than than max backoff sec.')

  return params
