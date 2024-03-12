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
"""Utilities for "gcloud metastore services backups" commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources


def UpdateBackupV1Alpha(ref, args, request):
  return _UpdateBackup(ref, args, request, api_version='v1alpha')


def UpdateBackupV1Beta(ref, args, request):
  return _UpdateBackup(ref, args, request, api_version='v1beta')


def UpdateBackupV1(ref, args, request):
  return _UpdateBackup(ref, args, request, api_version='v1')


def _UpdateBackup(ref, args, request, api_version):
  """Returns a modified create request with the `backup` field updated if the `backup` is passed.

  If the user passes in a single resource like `my-backup`, convert it to a
  relative resource name. If the user passes in a relative resource name, parse
  to make sure it's valid. This will always overwrite the `backup` field in the
  request, however, it might be overwritten with the same value.

  Args:
    ref: A resource ref to the parsed Service resource.
    args: The parsed args namespace from CLI.
    request: The framework generated request to modify.
    api_version: The API version of the backup.
  """
  if args.backup is None:
    return request
  request.restoreServiceRequest.backup = resources.REGISTRY.Parse(
      args.backup,
      params={
          'projectsId': ref.projectsId,
          'locationsId': ref.locationsId,
          'servicesId': ref.servicesId,
      },
      api_version=api_version,
      collection='metastore.projects.locations.services.backups').RelativeName(
      )
  return request
