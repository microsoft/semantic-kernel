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
"""Flags for compute queued resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.core.util.iso_duration import Duration
from googlecloudsdk.core.util.times import FormatDuration


def MakeQueuedResourcesArg(plural=False):
  return compute_flags.ResourceArgument(
      resource_name='queued resource',
      zonal_collection='compute.zoneQueuedResources',
      plural=plural,
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


DEFAULT_LIST_FORMAT = """
        table(
          name,
          location(),
          bulkInsertInstanceResource.count,
          bulkInsertInstanceResource.instanceProperties.machineType,
          bulkInsertInstanceResource.instanceProperties.guest_accelerators[0].accelerator_type,
          state,
          maxRunDuration(),
          status.queuingPolicy.validUntilTime
        )"""


def _TransformMaxRunDuration(resource):
  """Properly format max_run_duration field."""
  # This will always be present in the resource.
  bulk_resource = resource.get('bulkInsertInstanceResource')

  # Use get with dictionary optional return value to skip existence checking
  max_run_duration = bulk_resource.get('instanceProperties',
                                       {}).get('scheduling',
                                               {}).get('maxRunDuration')
  if not max_run_duration:
    return ''
  duration = Duration(seconds=int(max_run_duration.get('seconds')))
  return FormatDuration(duration, parts=4)


def AddOutputFormat(parser):
  parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)
  parser.display_info.AddTransforms({
      'maxRunDuration': _TransformMaxRunDuration,
  })
