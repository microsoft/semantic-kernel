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
"""Functions for dealing with managed instances groups updates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.health_checks import flags as health_checks_flags


HEALTH_CHECK_ARG = health_checks_flags.HealthCheckArgument(
    '',
    '--health-check',
    required=False,
    include_regional_health_check=True,
    scope_flags_usage=compute_flags.ScopeFlagsUsage.DONT_USE_SCOPE_FLAGS)


# Allow only up to 1 year initial delay
# 31536000 == 1y in seconds
# Modify both of these together.
_MAX_INITIAL_DELAY_DURATION = 31536000
_MAX_INITIAL_DELAY_DURATION_HUMAN_READABLE = '1y'


def _InitialDelayValidator(value):
  duration_parser = arg_parsers.Duration(parsed_unit='s')
  parsed_value = duration_parser(value)
  if parsed_value > _MAX_INITIAL_DELAY_DURATION:
    raise arg_parsers.ArgumentTypeError(
        'The value of initial delay must be between 0 and {max_value}'.format(
            max_value=_MAX_INITIAL_DELAY_DURATION_HUMAN_READABLE))
  return parsed_value


def AddAutohealingArgs(autohealing_params_group):
  """Adds autohealing-related commandline arguments to parser."""
  autohealing_params_group.add_argument(
      '--initial-delay',
      type=_InitialDelayValidator,
      help="""\
      Specifies the number of seconds that a new VM takes to initialize and run
      its startup script. During a VM's initial delay period, the MIG ignores
      unsuccessful health checks because the VM might be in the startup process.
      This prevents the MIG from prematurely recreating a VM. If the health
      check receives a healthy response during the initial delay, it indicates
      that the startup process is complete and the VM is ready. The value of
      initial delay must be between 0 and 3600 seconds. The default value is 0.
      See $ gcloud topic datetimes for information on duration formats.
      """)
  health_check_group = autohealing_params_group.add_mutually_exclusive_group()
  health_check_group.add_argument(
      '--http-health-check',
      help=('HTTP health check object used for autohealing instances in this '
            'group.'),
      action=actions.DeprecationAction(
          'http-health-check',
          warn='HttpHealthCheck is deprecated. Use --health-check instead.'))
  health_check_group.add_argument(
      '--https-health-check',
      help=('HTTPS health check object used for autohealing instances in this '
            'group.'),
      action=actions.DeprecationAction(
          'https-health-check',
          warn='HttpsHealthCheck is deprecated. Use --health-check instead.'))
  HEALTH_CHECK_ARG.AddArgument(health_check_group)
