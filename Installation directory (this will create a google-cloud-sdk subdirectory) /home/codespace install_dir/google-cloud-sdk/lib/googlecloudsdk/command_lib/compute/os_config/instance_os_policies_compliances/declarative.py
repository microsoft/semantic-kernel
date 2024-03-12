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
"""Instance OS policies compliance gcloud commands declarative functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.os_config import flags
from googlecloudsdk.core import properties

_DESCRIBE_URI = ('projects/{project}/locations/{location}'
                 '/instanceOSPoliciesCompliances/{instance}')


def SetNameOnDescribeRequestHook(unused_ref, args, request):
  """Add name field to Describe request.

  Args:
    unused_ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI
    request: Describe request for the API call

  Returns:
    Modified request that includes the name field.
  """
  instance = args.instance
  project = args.project or properties.VALUES.core.project.GetOrFail()
  location = args.location or properties.VALUES.compute.zone.Get()

  flags.ValidateInstance(instance, 'INSTANCE')
  flags.ValidateZone(location, '--location')

  request.name = _DESCRIBE_URI.format(
      project=project, location=location, instance=instance)
  return request
