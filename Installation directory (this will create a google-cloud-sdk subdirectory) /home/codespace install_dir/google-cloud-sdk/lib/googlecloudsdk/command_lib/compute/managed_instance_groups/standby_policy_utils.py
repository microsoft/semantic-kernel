# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Functions for dealing with managed instances groups updates to standby policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute.health_checks import flags as health_checks_flags

HEALTH_CHECK_ARG = health_checks_flags.HealthCheckArgument(
    '', '--health-check', required=False)

# Allow only up to 1 hour initial delay
_MAX_INITIAL_DELAY_DURATION = 3600
_MAX_INITIAL_DELAY_DURATION_HUMAN_READABLE = '1h'


def _InitialDelayValidator(value):
  duration_parser = arg_parsers.Duration(parsed_unit='s')
  parsed_value = duration_parser(value)
  if parsed_value > _MAX_INITIAL_DELAY_DURATION:
    raise arg_parsers.ArgumentTypeError(
        'The value of initial delay must be between 0 and {max_value}'.format(
            max_value=_MAX_INITIAL_DELAY_DURATION_HUMAN_READABLE))
  return parsed_value


def AddStandbyPolicyArgs(standby_policy_params):
  """Adds autohealing-related commandline arguments to parser."""
  standby_policy_params.add_argument(
      '--initial-delay',
      type=_InitialDelayValidator,
      help="""\
      Initialization delay before stopping or suspending instances
      in this managed instance group. For example: 5m or 300s.
      See `gcloud topic datetimes` for information on duration formats.
      """)
