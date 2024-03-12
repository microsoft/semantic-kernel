# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utilities for "gcloud scheduler" commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.tasks import app
from googlecloudsdk.command_lib.tasks import constants
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import http_encoding

_LOCATION_LIST_FORMAT = '''table(
     locationId:label="NAME",
     name:label="FULL_NAME")'''
_PUBSUB_MESSAGE_URL = 'type.googleapis.com/google.pubsub.v1.PubsubMessage'
PROJECTS_COLLECTION = 'cloudscheduler.projects'
LOCATIONS_COLLECTION = 'cloudscheduler.projects.locations'


def _GetPubsubMessages():
  return apis.GetMessagesModule('pubsub', apis.ResolveVersion('pubsub'))


def _GetSchedulerClient():
  return apis.GetClientInstance('cloudscheduler', 'v1')


def _GetSchedulerMessages():
  return apis.GetMessagesModule('cloudscheduler', 'v1')


def ClearFlag(arg):
  """Clear the value for a flag."""
  del arg
  return None


def LogPauseSuccess(unused_response, unused_args):
  """Log message if job was successfully paused."""
  _LogSuccessMessage('paused')


def LogResumeSuccess(unused_response, unused_args):
  """Log message if job was successfully resumed."""
  _LogSuccessMessage('resumed')


def _LogSuccessMessage(action):
  log.status.Print('Job has been {0}.'.format(action))


def ParseProject():
  return resources.REGISTRY.Parse(
      properties.VALUES.core.project.GetOrFail(),
      collection=PROJECTS_COLLECTION)


def LocationsUriFunc(task):
  return resources.REGISTRY.Parse(
      task.name,
      params={'projectId': properties.VALUES.core.project.GetOrFail()},
      collection=LOCATIONS_COLLECTION).SelfLink()


def AddListLocationsFormats(parser):
  parser.display_info.AddFormat(_LOCATION_LIST_FORMAT)
  parser.display_info.AddUriFunc(LocationsUriFunc)


def ModifyCreateJobRequest(job_ref, args, create_job_req):
  """Change the job.name field to a relative name."""
  del args  # Unused in ModifyCreateJobRequest
  create_job_req.job.name = job_ref.RelativeName()
  return create_job_req


def ModifyCreatePubsubJobRequest(job_ref, args, create_job_req):
  """Add the pubsubMessage field to the given request.

  Because the Cloud Scheduler API has a reference to a PubSub message, but
  represents it as a bag of properties, we need to construct the object here and
  insert it into the request.

  Args:
    job_ref: Resource reference to the job to be created (unused)
    args: argparse namespace with the parsed arguments from the command line. In
        particular, we expect args.message_body and args.attributes (optional)
        to be AdditionalProperty types.
    create_job_req: CloudschedulerProjectsLocationsJobsCreateRequest, the
        request constructed from the remaining arguments.

  Returns:
    CloudschedulerProjectsLocationsJobsCreateRequest: the given request but with
        the job.pubsubTarget.pubsubMessage field populated.
  """
  ModifyCreateJobRequest(job_ref, args, create_job_req)
  create_job_req.job.pubsubTarget.data = _EncodeMessageBody(
      args.message_body or args.message_body_from_file)
  if args.attributes:
    create_job_req.job.pubsubTarget.attributes = args.attributes
  return create_job_req


def SetRequestJobName(job_ref, unused_args, update_job_req):
  """Change the job.name field to a relative name."""
  update_job_req.job.name = job_ref.RelativeName()
  return update_job_req


def SetAppEngineRequestMessageBody(unused_job_ref, args, update_job_req):
  """Modify the App Engine update request to populate the message body."""
  if args.clear_message_body:
    update_job_req.job.appEngineHttpTarget.body = None
  elif args.message_body or args.message_body_from_file:
    update_job_req.job.appEngineHttpTarget.body = _EncodeMessageBody(
        args.message_body or args.message_body_from_file)
  return update_job_req


def SetAppEngineRequestUpdateHeaders(unused_job_ref, args, update_job_req):
  """Modify the App Engine update request to update, remove or clear headers."""
  headers = None
  if args.clear_headers:
    headers = {}
  elif args.update_headers or args.remove_headers:
    if args.update_headers:
      headers = args.update_headers
    if args.remove_headers:
      for key in args.remove_headers:
        headers[key] = None

  if headers:
    update_job_req.job.appEngineHttpTarget.headers = _GenerateAdditionalProperties(
        headers)
  return update_job_req


def SetHTTPRequestMessageBody(unused_job_ref, args, update_job_req):
  """Modify the HTTP update request to populate the message body."""
  if args.clear_message_body:
    update_job_req.job.httpTarget.body = None
  elif args.message_body or args.message_body_from_file:
    update_job_req.job.httpTarget.body = _EncodeMessageBody(
        args.message_body or args.message_body_from_file)
  return update_job_req


def SetHTTPRequestUpdateHeaders(unused_job_ref, args, update_job_req):
  """Modify the HTTP update request to update, remove, or clear headers."""
  headers = None
  if args.clear_headers:
    headers = {}
  elif args.update_headers or args.remove_headers:
    if args.update_headers:
      headers = args.update_headers
    if args.remove_headers:
      for key in args.remove_headers:
        headers[key] = None
  if headers:
    update_job_req.job.httpTarget.headers = _GenerateAdditionalProperties(
        headers)
  return update_job_req


def SetPubsubRequestMessageBody(unused_job_ref, args, update_job_req):
  """Modify the Pubsub update request to populate the message body."""
  if args.message_body or args.message_body_from_file:
    update_job_req.job.pubsubTarget.data = _EncodeMessageBody(
        args.message_body or args.message_body_from_file)
  return update_job_req


def SetPubsubRequestUpdateAttributes(unused_job_ref, args, update_job_req):
  """Modify the Pubsub update request to update, remove, or clear attributes."""
  attributes = None
  if args.clear_attributes:
    attributes = {}
  elif args.update_attributes or args.remove_attributes:
    if args.update_attributes:
      attributes = args.update_attributes
    if args.remove_attributes:
      for key in args.remove_attributes:
        attributes[key] = None
  if attributes:
    update_job_req.job.pubsubTarget.attributes = _GenerateAdditionalProperties(
        attributes)
  return update_job_req


def ParseAttributes(attributes):
  """Parse "--attributes" flag as an argparse type.

  The flag is given as a Calliope ArgDict:

      --attributes key1=value1,key2=value2

  Args:
    attributes: str, the value of the --attributes flag.

  Returns:
    dict, a dict with 'additionalProperties' as a key, and a list of dicts
        containing key-value pairs as the value.
  """
  attributes = arg_parsers.ArgDict()(attributes)
  return {
      'additionalProperties':
          [{'key': key, 'value': value}
           for key, value in sorted(attributes.items())]
  }


def UpdateAppEngineMaskHook(unused_ref, args, req):
  """Constructs updateMask for patch requests of AppEngine targets.

  Args:
    unused_ref: A resource ref to the parsed Job resource
    args: The parsed args namespace from CLI
    req: Created Patch request for the API call.

  Returns:
    Modified request for the API call.
  """
  app_engine_fields = {
      '--message-body': 'appEngineHttpTarget.body',
      '--message-body-from-file': 'appEngineHttpTarget.body',
      '--relative-url': 'appEngineHttpTarget.relativeUri',
      '--version': 'appEngineHttpTarget.appEngineRouting.version',
      '--service': 'appEngineHttpTarget.appEngineRouting.service',
      '--clear-service': 'appEngineHttpTarget.appEngineRouting.service',
      '--clear-relative-url': 'appEngineHttpTarget.relativeUri',
      '--clear-headers': 'appEngineHttpTarget.headers',
      '--remove-headers': 'appEngineHttpTarget.headers',
      '--update-headers': 'appEngineHttpTarget.headers',
  }
  req.updateMask = _GenerateUpdateMask(args, app_engine_fields)
  return req


def UpdateHTTPMaskHook(unused_ref, args, req):
  """Constructs updateMask for patch requests of PubSub targets.

  Args:
    unused_ref: A resource ref to the parsed Job resource
    args: The parsed args namespace from CLI
    req: Created Patch request for the API call.

  Returns:
    Modified request for the API call.
  """
  http_fields = {
      '--message-body': 'httpTarget.body',
      '--message-body-from-file': 'httpTarget.body',
      '--uri': 'httpTarget.uri',
      '--http-method': 'httpTarget.httpMethod',
      '--clear-headers': 'httpTarget.headers',
      '--remove-headers': 'httpTarget.headers',
      '--update-headers': 'httpTarget.headers',
      '--oidc-service-account-email':
          'httpTarget.oidcToken.serviceAccountEmail',
      '--oidc-token-audience': 'httpTarget.oidcToken.audience',
      '--oauth-service-account-email':
          'httpTarget.oauthToken.serviceAccountEmail',
      '--oauth-token-scope': 'httpTarget.oauthToken.scope',
      '--clear-auth-token':
          'httpTarget.oidcToken.serviceAccountEmail,'
          'httpTarget.oidcToken.audience,'
          'httpTarget.oauthToken.serviceAccountEmail,'
          'httpTarget.oauthToken.scope',
  }
  req.updateMask = _GenerateUpdateMask(args, http_fields)
  return req


def UpdatePubSubMaskHook(unused_ref, args, req):
  """Constructs updateMask for patch requests of PubSub targets.

  Args:
    unused_ref: A resource ref to the parsed Job resource
    args: The parsed args namespace from CLI
    req: Created Patch request for the API call.

  Returns:
    Modified request for the API call.
  """
  pubsub_fields = {
      '--message-body': 'pubsubTarget.data',
      '--message-body-from-file': 'pubsubTarget.data',
      '--topic': 'pubsubTarget.topicName',
      '--clear-attributes': 'pubsubTarget.attributes',
      '--remove-attributes': 'pubsubTarget.attributes',
      '--update-attributes': 'pubsubTarget.attributes',
  }
  req.updateMask = _GenerateUpdateMask(args, pubsub_fields)
  return req


def _GenerateUpdateMask(args, target_fields):
  """Constructs updateMask for patch requests.

  Args:
    args: The parsed args namespace from CLI
    target_fields: A Dictionary of field mappings specific to the target.

  Returns:
    String containing update mask for patch request.
  """
  arg_name_to_field = {
      # Common flags
      '--description': 'description',
      '--schedule': 'schedule',
      '--time-zone': 'timeZone',
      '--clear-time-zone': 'timeZone',
      '--attempt-deadline': 'attemptDeadline',
      # Retry flags
      '--max-retry-attempts': 'retryConfig.retryCount',
      '--clear-max-retry-attempts': 'retryConfig.retryCount',
      '--max-retry-duration': 'retryConfig.maxRetryDuration',
      '--clear-max-retry-duration': 'retryConfig.maxRetryDuration',
      '--min-backoff': 'retryConfig.minBackoffDuration',
      '--clear-min-backoff': 'retryConfig.minBackoffDuration',
      '--max-backoff': 'retryConfig.maxBackoffDuration',
      '--clear-max-backoff': 'retryConfig.maxBackoffDuration',
      '--max-doublings': 'retryConfig.maxDoublings',
      '--clear-max-doublings': 'retryConfig.maxDoublings',
  }
  if target_fields:
    arg_name_to_field.update(target_fields)

  update_mask = []
  for arg_name in args.GetSpecifiedArgNames():
    if arg_name in arg_name_to_field:
      update_mask.append(arg_name_to_field[arg_name])

  return ','.join(sorted(list(set(update_mask))))


def _EncodeMessageBody(message_body):
  """HTTP encodes the given message body.

  Args:
    message_body: the message body to be encoded

  Returns:
    String containing HTTP encoded message body.
  """
  message_body_str = encoding.Decode(message_body, encoding='utf-8')
  return http_encoding.Encode(message_body_str)


def _GenerateAdditionalProperties(values_dict):
  """Format values_dict into additionalProperties-style dict."""
  return {
      'additionalProperties': [
          {'key': key, 'value': value} for key, value
          in sorted(values_dict.items())
      ]}


def _DoesCommandRequireAppEngineApp():
  """Returns whether the command being executed needs App Engine app."""
  gcloud_env_key = constants.GCLOUD_COMMAND_ENV_KEY
  if gcloud_env_key in os.environ:
    return os.environ[gcloud_env_key] in constants.COMMANDS_THAT_NEED_APPENGINE
  return False


class RegionResolvingError(exceptions.Error):
  """Error for when the app's region cannot be ultimately determined."""


class AppLocationResolver(object):
  """Callable that resolves and caches the app location for the project.

  The "fallback" for arg marshalling gets used multiple times in the course of
  YAML command translation. This prevents multiple API roundtrips without making
  that class stateful.
  """

  def __init__(self):
    self.location = None

  def __call__(self):
    if self.location is None:
      self.location = self._ResolveAppLocation()
    return self.location

  def _ResolveAppLocation(self):
    """Determines Cloud Scheduler location for the project."""
    # Not setting the quota project to 'LEGACY' sends the current project ID in
    # the App Engine API request. This prompts a check to see if the App Engine
    # admin API is enabled for that project.
    properties.VALUES.billing.quota_project.Set(
        properties.VALUES.billing.LEGACY)
    if app.AppEngineAppExists():
      project = properties.VALUES.core.project.GetOrFail()
      return self._GetLocation(project)
    raise RegionResolvingError(
        'Please use the location flag to manually specify a location.')

  def _GetLocation(self, project):
    """Gets the location from the Cloud Scheduler API."""
    try:
      client = _GetSchedulerClient()
      messages = _GetSchedulerMessages()
      request = messages.CloudschedulerProjectsLocationsListRequest(
          name='projects/{}'.format(project))
      locations = list(
          list_pager.YieldFromList(
              client.projects_locations,
              request,
              batch_size=2,
              limit=2,
              field='locations',
              batch_size_attribute='pageSize'))
      if len(locations) >= 1:
        location = locations[0].labels.additionalProperties[0].value
        if len(locations) > 1 and not _DoesCommandRequireAppEngineApp():
          log.warning(
              constants.APP_ENGINE_DEFAULT_LOCATION_WARNING.format(location))
        return location
      return None
    except apitools_exceptions.HttpNotFoundError:
      return None
