# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""General BQ surface command utilites for python commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import waiter


DEFAULT_MAX_QUERY_RESULTS = 1000


class BqJobPoller(waiter.OperationPoller):
  """Poller for managing Bq Jobs."""

  def __init__(self, job_service, result_service,
               max_query_results=DEFAULT_MAX_QUERY_RESULTS):
    """Sets up poller for generic long running processes.

    Args:
      job_service: apitools.base.py.base_api.BaseApiService, api service
        for retrieving information about ongoing job.
      result_service: apitools.base.py.base_api.BaseApiService, api service for
        retrieving created result of initiated operation.
      max_query_results: maximum number of records to return from a query job.
    """
    self.result_service = result_service
    self.job_service = job_service
    self.max_query_results = max_query_results

  def IsDone(self, job):
    """Overrides."""
    if job.status.state == 'DONE':
      if job.status.errorResult:
        raise waiter.OperationError(job.status.errorResult.message)
      return True
    return False

  def Poll(self, job_ref):
    """Overrides.

    Args:
      job_ref: googlecloudsdk.core.resources.Resource.

    Returns:
      fetched operation message.
    """
    request_type = self.job_service.GetRequestType('Get')
    return self.job_service.Get(
        request_type(jobId=job_ref.Name(), projectId=job_ref.Parent().Name()))

  def GetResult(self, job):
    """Overrides to get the response from the completed job by job type.

    Args:
      job: api_name_messages.Job.

    Returns:
      the 'response' field of the Operation.
    """
    request_type = self.result_service.GetRequestType('Get')
    job_type = job.configuration.jobType

    if job_type == 'COPY':
      result_table = job.configuration.copy.destinationTable
      request = request_type(datasetId=result_table.datasetId,
                             tableId=result_table.tableId,
                             projectId=result_table.projectId)
    elif job_type == 'LOAD':
      result_table = job.configuration.load.destinationTable
      request = request_type(datasetId=result_table.datasetId,
                             tableId=result_table.tableId,
                             projectId=result_table.projectId)
    elif job_type == 'QUERY':
      request_type = self.result_service.GetRequestType('GetQueryResults')
      request = request_type(jobId=job.jobReference.jobId,
                             maxResults=self.max_query_results,
                             projectId=job.jobReference.projectId)
      return self.result_service.GetQueryResults(request)
    else:  # EXTRACT OR UNKNOWN type
      return job

    return self.result_service.Get(request)
