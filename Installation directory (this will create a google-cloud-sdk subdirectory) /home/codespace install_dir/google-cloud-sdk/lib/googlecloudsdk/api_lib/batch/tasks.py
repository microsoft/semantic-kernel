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

"""Utilities for Cloud Batch tasks API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.batch import util as batch_api_util


class TasksClient(object):
  """Client for tasks service in the Cloud Batch API."""

  def __init__(self, release_track, client=None, messages=None):
    self.client = client or batch_api_util.GetClientInstance(release_track)
    self.messages = messages or self.client.MESSAGES_MODULE
    self.service = self.client.projects_locations_jobs_taskGroups_tasks

  def Get(self, task_ref):
    get_req_type = (
        self.messages.BatchProjectsLocationsJobsTaskGroupsTasksGetRequest)
    get_req = get_req_type(name=task_ref.RelativeName())
    return self.service.Get(get_req)
