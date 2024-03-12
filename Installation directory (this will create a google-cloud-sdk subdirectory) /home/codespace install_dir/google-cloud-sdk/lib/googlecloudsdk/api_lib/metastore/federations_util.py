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
"""Utilities for calling the Metastore Federations API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.calliope import base


def GetFederation(release_track=base.ReleaseTrack.GA):
  return api_util.GetClientInstance(
      release_track=release_track).projects_locations_federations


def Delete(relative_resource_name, release_track=base.ReleaseTrack.GA):
  """Calls the Metastore Federations.Delete method.

  Args:
    relative_resource_name: str, the relative resource name of the Metastore
      federation to delete.
    release_track: base.ReleaseTrack, the release track of command. Will dictate
      which Metastore client library will be used.

  Returns:
    Operation: the operation corresponding to the deletion of the federation.
  """
  return GetFederation(release_track=release_track).Delete(
      api_util.GetMessagesModule(release_track=release_track)
      .MetastoreProjectsLocationsFederationsDeleteRequest(
          name=relative_resource_name))
