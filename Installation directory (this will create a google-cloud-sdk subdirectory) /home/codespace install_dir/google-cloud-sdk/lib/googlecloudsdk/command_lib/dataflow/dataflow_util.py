# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Utilities for building the dataflow CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re

from apitools.base.py import exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.dataflow import exceptions as dataflow_exceptions

from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

# Regular expression to match only metrics from Dataflow. Currently, this should
# match at least "dataflow" and "dataflow/v1b3". User metrics have an origin set
# as /^user/.
DATAFLOW_METRICS_RE = re.compile('^dataflow')

DATAFLOW_API_DEFAULT_REGION = apis.DATAFLOW_API_DEFAULT_REGION

# Regular expression to only match watermark metrics.
WINDMILL_WATERMARK_RE = re.compile('^(.*)-windmill-(.*)-watermark')

JOBS_COLLECTION = 'dataflow.projects.locations.jobs'

DEFAULT_REGION_MESSAGE = 'Defaults to \'{0}\'.'.format(
    DATAFLOW_API_DEFAULT_REGION)


def GetErrorMessage(error):
  """Extract the error message from an HTTPError.

  Args:
    error: The error exceptions.HttpError thrown by the API client.

  Returns:
    A string describing the error.
  """
  try:
    content_obj = json.loads(error.content)
    return content_obj.get('error', {}).get('message', '')
  except ValueError:
    log.err.Print(error.response)
    return 'Unknown error'


def MakeErrorMessage(error, job_id='', project_id='', region_id=''):
  """Create a standard error message across commands.

  Args:
    error: The error exceptions.HttpError thrown by the API client.
    job_id: The job ID that was used in the command.
    project_id: The project ID that was used in the command.
    region_id: The region ID that was used in the command.

  Returns:
    str, a standard error message.
  """
  if job_id:
    job_id = ' with job ID [{0}]'.format(job_id)
  if project_id:
    project_id = ' in project [{0}]'.format(project_id)
  if region_id:
    region_id = ' in regional endpoint [{0}]'.format(region_id)
  return 'Failed operation{0}{1}{2}: {3}'.format(job_id, project_id, region_id,
                                                 GetErrorMessage(error))


def YieldExceptionWrapper(generator, job_id='', project_id='', region_id=''):
  """Wraps a generator to catch any exceptions.

  Args:
    generator: The error exceptions.HttpError thrown by the API client.
    job_id: The job ID that was used in the command.
    project_id: The project ID that was used in the command.
    region_id: The region ID that was used in the command.

  Yields:
    The generated object.

  Raises:
    dataflow_exceptions.ServiceException: An exception for errors raised by
      the service.
  """
  try:
    for x in generator:
      yield x
  except exceptions.HttpError as e:
    raise dataflow_exceptions.ServiceException(
        MakeErrorMessage(e, job_id, project_id, region_id))


def YieldFromList(service,
                  request,
                  limit=None,
                  batch_size=100,
                  field='items',
                  batch_size_attribute='maxResults',
                  predicate=None,
                  job_id='',
                  project_id='',
                  region_id=''):
  """Returns a wrapped list_page.YieldFromList to catch any exceptions.

  Args:
    service: apitools_base.BaseApiService, A service with a .List() method.
    request: protorpc.messages.Message, The request message corresponding to the
      service's .List() method, with all the attributes populated except the
      .maxResults and .pageToken attributes.
    limit: int, The maximum number of records to yield. None if all available
      records should be yielded.
    batch_size: int, The number of items to retrieve per request.
    field: str, The field in the response that will be a list of items.
    batch_size_attribute: str, The name of the attribute in a response message
      holding the maximum number of results to be returned. None if
      caller-specified batch size is unsupported.
    predicate: lambda, A function that returns true for items to be yielded.
    job_id: The job ID that was used in the command.
    project_id: The project ID that was used in the command.
    region_id: The region ID that was used in the command.

  Returns:
    The wrapped generator.

  Raises:
    dataflow_exceptions.ServiceException: if list request failed.
  """
  method = 'List'
  if not region_id:
    method = 'Aggregated'

  pager = list_pager.YieldFromList(
      service=service,
      request=request,
      limit=limit,
      batch_size=batch_size,
      field=field,
      batch_size_attribute=batch_size_attribute,
      predicate=predicate,
      method=method)
  return YieldExceptionWrapper(pager, job_id, project_id, region_id)


def JobsUriFunc(resource):
  """Transform a job resource into a URL string.

  Args:
    resource: The DisplayInfo job object

  Returns:
    URL to the job
  """

  ref = resources.REGISTRY.Parse(
      resource.id,
      params={
          'projectId': properties.VALUES.core.project.GetOrFail,
          'location': resource.location
      },
      collection=JOBS_COLLECTION)
  return ref.SelfLink()


def JobsUriFromId(job_id, region_id):
  """Transform a job ID into a URL string.

  Args:
    job_id: The job ID
    region_id: Region ID of the job's regional endpoint.

  Returns:
    URL to the job
  """
  ref = resources.REGISTRY.Parse(
      job_id,
      params={
          'projectId': properties.VALUES.core.project.GetOrFail,
          'location': region_id
      },
      collection=JOBS_COLLECTION)
  return ref.SelfLink()


# TODO(b/139889563): Remove this method when args region is changed to required
def GetRegion(args):
  """Get region to be used in Dataflow services.

  Args:
    args: Argument passed in when running gcloud dataflow command

  Returns:
    Region specified by user from --region flag in args, then fall back to
    'us-central1'.
  """
  region = args.region

  if not region:
    region = DATAFLOW_API_DEFAULT_REGION
    msg = ('`--region` not set; defaulting to \'{0}\'. In an upcoming ' +
           'release, users must specify a region explicitly. See https://' +
           'cloud.google.com/dataflow/docs/concepts/regional-endpoints ' +
           'for additional details.'
          ).format(DATAFLOW_API_DEFAULT_REGION)
    log.warning(msg)

  return region
