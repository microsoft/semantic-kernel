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

"""Utilities for Cloud Batch jobs API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.batch import util as batch_api_util


class JobsClient(object):
  """Client for jobs service in the Cloud Batch API."""

  def __init__(self, release_track, client=None, messages=None):
    self.client = client or batch_api_util.GetClientInstance(release_track)
    self.messages = messages or self.client.MESSAGES_MODULE
    self.service = self.client.projects_locations_jobs

  def Create(self, job_id, location_ref, job_config):
    create_req_type = (
        self.messages.BatchProjectsLocationsJobsCreateRequest)
    create_req = create_req_type(
        jobId=job_id,
        parent=location_ref.RelativeName(),
        job=job_config)
    return self.service.Create(create_req)

  def Get(self, job_ref):
    get_req_type = (
        self.messages.BatchProjectsLocationsJobsGetRequest)
    get_req = get_req_type(name=job_ref.RelativeName())
    return self.service.Get(get_req)

  def Delete(self, job_ref):
    delete_req_type = (
        self.messages.BatchProjectsLocationsJobsDeleteRequest)
    delete_req = delete_req_type(name=job_ref.RelativeName())
    return self.service.Delete(delete_req)
