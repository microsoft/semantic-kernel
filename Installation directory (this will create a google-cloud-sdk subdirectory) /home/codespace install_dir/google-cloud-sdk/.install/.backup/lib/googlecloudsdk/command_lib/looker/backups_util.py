# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utility for Looker instance backups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.looker import backups
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def ModifyInstanceBackupName(unused_instance_ref, args, patch_request):
  """Create a backup of a Looker instance."""
  if args.IsSpecified('backup'):
    backup_name = args.backup
    if len(backup_name.split('/')) <= 1:
      parent = resources.REGISTRY.Parse(
          args.instance,
          params={
              'projectsId': properties.VALUES.core.project.GetOrFail,
              'locationsId': args.region,
          },
          api_version=backups.API_VERSION_DEFAULT,
          collection='looker.projects.locations.instances',
      ).RelativeName()
      patch_request.restoreInstanceRequest.backup = (
          parent + '/backups/' + backup_name
      )
    return patch_request
  return patch_request
