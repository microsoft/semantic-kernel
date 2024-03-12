# Copyright 2008 Google LLC. All Rights Reserved.
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

"""CronInfo tools.

A library for working with CronInfo records, describing cron entries for an
application. Supports loading the records from yaml.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
__author__ = 'arb@google.com (Anthony Baxter)'

# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

import logging
import os
import sys
import traceback

pytz = None

# pylint: disable=g-import-not-at-top
from googlecloudsdk.third_party.appengine._internal import six_subset

# groc depends on antlr3 which is py2-only, so conditionally import based on
# python version. See comments under GrocValidator.Validate for more context.
if six_subset.PY2:
  from googlecloudsdk.third_party.appengine.googlecron import groc
  from googlecloudsdk.third_party.appengine.googlecron import groctimespecification
else:
  groc = None
  groctimespecification = None

if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import appinfo
  from google.appengine.api import validation
  from google.appengine.api import yaml_builder
  from google.appengine.api import yaml_listener
  from google.appengine.api import yaml_object
else:
  from googlecloudsdk.third_party.appengine.api import appinfo
  from googlecloudsdk.third_party.appengine.api import validation
  from googlecloudsdk.third_party.appengine.api import yaml_builder
  from googlecloudsdk.third_party.appengine.api import yaml_listener
  from googlecloudsdk.third_party.appengine.api import yaml_object
# pylint: enable=g-import-not-at-top

_URL_REGEX = r'^/.*$'
_TIMEZONE_REGEX = r'^.{0,100}$'
_DESCRIPTION_REGEX = r'^.{0,499}$'
# TODO(user): Figure out what engine-related work needs to happen here.
# http://b/issue?id=6237360
SERVER_ID_RE_STRING = r'(?!-)[a-z\d\-]{1,63}'
# NOTE(user): The length here must remain 100 for backwards compatibility,
# see b/5485871 for more information.
SERVER_VERSION_RE_STRING = r'(?!-)[a-z\d\-]{1,100}'
# This _VERSION_REGEX probably should be the same as in
# apphosting/api/queueinfo.py. See b/35767221.
_VERSION_REGEX = r'^(?:(?:(%s):)?)(%s)$' % (SERVER_ID_RE_STRING,
                                            SERVER_VERSION_RE_STRING)


# This is in groc format - see
# http://g3doc/borg/borgcron/g3doc/userguide.md
class GrocValidator(validation.Validator):
  """Checks that a schedule is in valid groc format."""

  def Validate(self, value, key=None):
    """Validates a schedule."""
    if value is None:
      raise validation.MissingAttribute('schedule must be specified')
    if not isinstance(value, six_subset.string_types):
      raise TypeError('schedule must be a string, not \'%r\''%type(value))
    # If we're running on py3 and don't have access to groctimespecification,
    # then the server will still do the validation on the schedule property.
    if groc and groctimespecification:
      try:
        groctimespecification.GrocTimeSpecification(value)
      except groc.GrocException as e:
        raise validation.ValidationError('schedule \'%s\' failed to parse: %s'%(
            value, e.args[0]))
    return value


class TimezoneValidator(validation.Validator):
  """Checks that a timezone can be correctly parsed and is known."""

  def Validate(self, value, key=None):
    """Validates a timezone."""
    if not isinstance(value, six_subset.string_types):
      raise TypeError('timezone must be a string, not \'%r\'' % type(value))
    if pytz is None:
      # pytz not installed, silently accept anything without validating
      return value
    try:
      pytz.timezone(value)
    except pytz.UnknownTimeZoneError:
      raise validation.ValidationError('timezone \'%s\' is unknown' % value)
    except IOError:
      # When running under dev_appserver, pytz can't open it's resource files.
      # I have no idea how to test this.
      return value
    except:
      # The yaml and validation code repeatedly re-raise exceptions that
      # consume tracebacks.
      unused_e, v, t = sys.exc_info()
      logging.warning('pytz raised an unexpected error: %s.\n' % (v) +
                      'Traceback:\n' + '\n'.join(traceback.format_tb(t)))
      raise
    return value


CRON = 'cron'

URL = 'url'
SCHEDULE = 'schedule'
TIMEZONE = 'timezone'
DESCRIPTION = 'description'
TARGET = 'target'

RETRY_PARAMETERS = 'retry_parameters'
JOB_RETRY_LIMIT = 'job_retry_limit'
JOB_AGE_LIMIT = 'job_age_limit'
MIN_BACKOFF_SECONDS = 'min_backoff_seconds'
MAX_BACKOFF_SECONDS = 'max_backoff_seconds'
MAX_DOUBLINGS = 'max_doublings'

class MalformedCronfigurationFile(Exception):
  """Configuration file for Cron is malformed."""
  pass


class RetryParameters(validation.Validated):
  """Retry parameters for a single cron job."""
  ATTRIBUTES = {
      JOB_RETRY_LIMIT: validation.Optional(
          validation.Range(minimum=0,
                           # Max value of 32-bit int.
                           maximum=sys.maxsize,
                           range_type=int)),
      JOB_AGE_LIMIT: validation.Optional(validation.TimeValue()),
      MIN_BACKOFF_SECONDS: validation.Optional(
          validation.Range(0.0, None, range_type=float)),
      MAX_BACKOFF_SECONDS: validation.Optional(
          validation.Range(0.0, None, range_type=float)),
      MAX_DOUBLINGS: validation.Optional(
          validation.Range(0, None, range_type=int)),
  }


class CronEntry(validation.Validated):
  """A cron entry describes a single cron job."""
  ATTRIBUTES = {
      URL: _URL_REGEX,
      SCHEDULE: GrocValidator(),
      TIMEZONE: validation.Optional(TimezoneValidator()),
      DESCRIPTION: validation.Optional(_DESCRIPTION_REGEX),
      RETRY_PARAMETERS: validation.Optional(RetryParameters),
      TARGET: validation.Optional(_VERSION_REGEX),
  }


class CronInfoExternal(validation.Validated):
  """CronInfoExternal describes all cron entries for an application."""
  ATTRIBUTES = {
      appinfo.APPLICATION: validation.Optional(appinfo.APPLICATION_RE_STRING),
      CRON: validation.Optional(validation.Repeated(CronEntry))
  }


def LoadSingleCron(cron_info, open_fn=None):
  """Load a cron.yaml file or string and return a CronInfoExternal object."""
  builder = yaml_object.ObjectBuilder(CronInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(cron_info)

  cron_info_result = handler.GetResults()
  if len(cron_info_result) < 1:
    raise MalformedCronfigurationFile('Empty cron configuration.')
  if len(cron_info_result) > 1:
    raise MalformedCronfigurationFile('Multiple cron sections '
                                      'in configuration.')
  return cron_info_result[0]
