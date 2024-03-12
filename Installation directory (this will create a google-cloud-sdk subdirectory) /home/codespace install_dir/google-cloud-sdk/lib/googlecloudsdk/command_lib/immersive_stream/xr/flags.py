# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Flags and helpers for Immersive Stream for XR commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
import six.moves.urllib.parse

_REGION_CONFIG_ARG_HELP_TEXT = """\
  Flag used to specify region and capacity required for the service instance's availability.

  'region' is the region in which the instance is deployed.

  'capacity' is the maxium number of concurrent streaming sessions that the instance can support in the given region.
"""

_FALLBACK_URL_HELP_TEXT = """\
    Flag used to specify the fallback url to redirect users to when this service instance is unable to provide the streaming experience.
"""


def RegionValidator(region):
  """RegionValidator is a no-op. The validation is handled in CLH server."""
  return region


def AddRegionConfigArg(name, parser, repeatable=True, required=True):
  capacity_validator = arg_parsers.RegexpValidator(
      r'[0-9]+', 'capacity must be a number'
  )
  repeatable_help = '\nThis is a repeatable flag.' if repeatable else ''
  parser.add_argument(
      name,
      help=_REGION_CONFIG_ARG_HELP_TEXT + repeatable_help,
      type=arg_parsers.ArgDict(
          spec={
              'region': RegionValidator,
              'capacity': capacity_validator,
              'enable_autoscaling': arg_parsers.ArgBoolean(),
              'autoscaling_buffer': arg_parsers.BoundedInt(lower_bound=1),
              'autoscaling_min_capacity': arg_parsers.BoundedInt(lower_bound=1),
          },
          required_keys=['region', 'capacity'],
      ),
      required=required,
      action='append',
  )


def ValidateUrl(url):
  """Rudimentary url validator.

  Args:
    url: String

  Returns:
    Whether the input string contains both a scheme and a network location. Note
    that this is a very rudimentary validator and does not work on all cases.
    Invalid urls may still pass this check.
  """
  parsed_url = six.moves.urllib.parse.urlsplit(url)
  if not parsed_url.scheme:
    log.error('Invalid URL - The URL must contain a scheme')
    return False
  if not parsed_url.netloc:
    log.error('Invalid URL - The URL must contain a network location')
    return False
  return True


def ValidateMode(mode):
  """Validates the mode input.

  Args:
    mode: String indicating the rendering mode of the instance. Allowed values
      are 3d and ar.

  Returns:
    True if the mode is supported by ISXR, False otherwise.
  """
  mode = mode.lower()
  if mode == '3d' or mode == 'ar':
    return True
  raise exceptions.InvalidArgumentException('--mode', 'mode must be 3d or ar')


def ValidateGpuClass(gpu_class, mode):
  """Validates the gpu_class input.

  Args:
    gpu_class: String indicating the GPU class of the instance. Allowed values
      are l4 and t4.
    mode: String indicating the rendering mode of the instance.

  Returns:
    True if the GPU class and mode combination is supported by ISXR, False
    otherwise.
  """
  gpu_class = gpu_class.lower()
  if gpu_class == 't4':
    return True
  if gpu_class == 'l4':
    if not mode or mode.lower() != '3d':
      raise exceptions.InvalidArgumentException(
          '--gpu-class', 'l4 gpu-class must have --mode=3d'
      )
    return True
  raise exceptions.InvalidArgumentException(
      '--gpu-class', 'gpu-class must be l4 or t4'
  )


def ValidateRegionConfigArgs(region_configs, operation_name):
  """Validates the region config args do not contain duplicate regions and have valid autoscaling configuration, if enabled.

  Args:
    region_configs: Either add_region or update_region ArgList from the
      instance update args
    operation_name: String indicating if operation is an add or update region
      operation

  Returns:
    True if the region_configs are valid. False if not.
  """

  regions = {}
  for region_config in region_configs:
    regions[region_config['region']] = region_config
    if region_config.get('enable_autoscaling', False) and not (
        'autoscaling_buffer' in region_config
        and 'autoscaling_min_capacity' in region_config
    ):
      log.error(
          'Must set autoscaling_buffer and autoscaling_min_capacity if'
          ' enable_autoscaling is set to true.'
      )
      return False

  if len(regions) < len(region_configs):
    log.error(
        'Duplicate regions in --{}-region arguments.'.format(operation_name)
    )
    return False

  return True
