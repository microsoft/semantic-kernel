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
"""A library containing flags used by Transcoder commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions


def AddCreateJobFlags(parser):
  """Add a list of flags for create jobs."""
  job_config = parser.add_mutually_exclusive_group()
  job_config.add_argument('--json', help='Job config in json format.')
  job_config.add_argument('--file', help='Path to job config.')
  job_config.add_argument('--template-id', help='Job template id.')

  parser.add_argument(
      '--input-uri',
      help=(
          'Google Cloud Storage URI. This value '
          'will override input URI in job config.'
      ),
  )
  parser.add_argument(
      '--output-uri',
      help=(
          'Google Cloud Storage directory URI '
          '(followed by a trailing forward slash). This value '
          'will override output URI in job config.'
      ),
  )
  parser.add_argument(
      '--mode',
      choices=['PROCESSING_MODE_INTERACTIVE', 'PROCESSING_MODE_BATCH'],
      help=(
          'Processing mode of transcode job. This value '
          'will override mode in job config.'
      ),
  )
  parser.add_argument(
      '--batch-mode-priority',
      type=int,
      help=(
          'Processing priority of a batch mode transcoder job. This value '
          'will override batch mode priority in job config.'
      ),
  )
  parser.add_argument(
      '--optimization',
      choices=['AUTODETECT', 'DISABLED'],
      help=(
          'Optimization strategy of transcode job. This value '
          'will override optimization in job config.'
      ),
  )
  parser.add_argument(
      '--priority',
      help='Job priority, default 0.',
      hidden=True,
      action=actions.DeprecationAction(
          '--region',
          warn='The {flag_name} option is deprecated.',
          error='The {flag_name} option is removed.',
          removed=True,
      ),
  )


def AddCreateTemplateFlags(parser):
  """Add a list of flags for create job templates."""
  template_config = parser.add_mutually_exclusive_group(required=True)
  template_config.add_argument('--json', help='Job template in json format.')
  template_config.add_argument('--file', help='Path to job template.')
