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
"""Jobs client for Faultinjectiontesting Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.fault_injection import utils as api_lib_utils


class JobsClient(object):
  """Client for Jobs in Faultinjection Testing API."""

  def __init__(self, client=None, messages=None):
    self.client = client or api_lib_utils.GetClientInstance()
    self.messages = messages or api_lib_utils.GetMessagesModule()
    self._jobs_client = self.client.projects_locations_jobs

  def Describe(self, job):
    """Describe a job in the Project/location.

    Args:
      job: str, the name for the job being described.

    Returns:
      Described Job Resource.
    """
    describe_req = (
        self.messages.FaultinjectiontestingProjectsLocationsJobsGetRequest(
            name=job
        )
    )
    return self._jobs_client.Get(describe_req)

  def List(
      self,
      parent,
      limit=None,
      page_size=100,
  ):
    """List Jobs in the Projects/Location.

    Args:
      parent: str, projects/{projectId}/locations/{location}
      limit: int or None, the total number of results to return.
      page_size: int, the number of entries in each batch (affects requests
        made, but not the yielded results).

    Returns:
      Generator of matching jobs.
    """
    list_req = (
        self.messages.FaultinjectiontestingProjectsLocationsJobsListRequest(
            parent=parent
        )
    )
    return list_pager.YieldFromList(
        self._jobs_client,
        list_req,
        field='jobs',
        batch_size=page_size,
        limit=limit,
        batch_size_attribute='pageSize',
    )

  def Create(self, job_id, experiment_id, fault_targets, dry_run, parent):
    """Create a job in the Project/location.

    Args:
      job_id: str, the name for the job being created
      experiment_id: str, name of the experiment
      fault_targets: targets for the faults
      dry_run: Boolean value for dry-run
      parent: parent for fault resource

    Returns:
      Job.
    """
    targets = []
    # For MVP, we are supporting only service names as targets
    for fault_target in fault_targets:
      targets.append(
          self.messages.FaultInjectionTargetMatcher(service=fault_target)
          )

    job = self.messages.Job(experiment=experiment_id, faultTargets=targets)
    create_req = (
        self.messages.FaultinjectiontestingProjectsLocationsJobsCreateRequest(
            jobId=job_id,
            job=job,
            validateOnly=dry_run,
            parent=parent,
        )
    )

    return self._jobs_client.Create(create_req)

  def Delete(self, job):
    """Delete a Job in the Project/location.

    Args:
      job: str, the name for the job being deleted

    Returns:
      Empty Response Message.
    """
    delete_req = (
        self.messages.FaultinjectiontestingProjectsLocationsJobsDeleteRequest(
            name=job
        )
    )
    return self._jobs_client.Delete(delete_req)
