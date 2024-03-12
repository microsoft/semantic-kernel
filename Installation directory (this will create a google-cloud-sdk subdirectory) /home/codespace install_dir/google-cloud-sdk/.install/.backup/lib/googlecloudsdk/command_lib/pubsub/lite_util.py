# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""A library that is used to support Cloud Pub/Sub Lite commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
import six
from six.moves.urllib.parse import urlparse

# Resource path constants
PROJECTS_RESOURCE_PATH = 'projects/'
LOCATIONS_RESOURCE_PATH = 'locations/'
RESERVATIONS_RESOURCE_PATH = 'reservations/'
TOPICS_RESOURCE_PATH = 'topics/'
SUBSCRIPTIONS_RESOURCE_PATH = 'subscriptions/'
PUBSUBLITE_API_NAME = 'pubsublite'
PUBSUBLITE_API_VERSION = 'v1'


class UnexpectedResourceField(exceptions.Error):
  """Error for having and unknown resource field."""


class InvalidPythonVersion(exceptions.Error):
  """Error for an invalid python version."""


class NoGrpcInstalled(exceptions.Error):
  """Error that occurs when the grpc module is not installed."""

  def __init__(self):
    super(NoGrpcInstalled, self).__init__(
        'Please ensure that the gRPC module is installed and the environment '
        'is correctly configured. Run `sudo pip3 install grpcio` and set the '
        'environment variable CLOUDSDK_PYTHON_SITEPACKAGES=1.')


class InvalidSeekTarget(exceptions.Error):
  """Error for specifying an invalid seek target."""


class InvalidResourcePath(exceptions.Error):
  """Error for specifying an invalid fully qualified resource path."""


def PubsubLiteClient():
  """Returns the Pub/Sub Lite v1 client module."""
  return apis.GetClientInstance(PUBSUBLITE_API_NAME, PUBSUBLITE_API_VERSION)


def PubsubLiteMessages():
  """Returns the Pub/Sub Lite v1 messages module."""
  return apis.GetMessagesModule(PUBSUBLITE_API_NAME, PUBSUBLITE_API_VERSION)


def DurationToSeconds(duration):
  """Convert Duration object to total seconds for backend compatibility."""
  return six.text_type(int(duration.total_seconds)) + 's'


def DeriveRegionFromLocation(location):
  """Returns the region from a location string.

  Args:
    location: A str of the form `<region>-<zone>` or `<region>`, such as
      `us-central1-a` or `us-central1`. Any other form will cause undefined
      behavior.

  Returns:
    The str region. Example: `us-central1`.
  """
  splits = location.split('-')
  return '-'.join(splits[:2])


def DeriveRegionFromEndpoint(endpoint):
  """Returns the region from a endpoint string.

  Args:
    endpoint: A str of the form `https://<region-><environment->base.url.com/`.
      Example `https://us-central-base.url.com/`,
      `https://us-central-autopush-base.url.com/`, or `https://base.url.com/`.

  Returns:
    The str region if it exists, otherwise None.
  """
  parsed = urlparse(endpoint)
  dash_splits = parsed.netloc.split('-')
  if len(dash_splits) > 2:
    return dash_splits[0] + '-' + dash_splits[1]
  else:
    return None


def CreateRegionalEndpoint(region, url):
  """Returns a new endpoint string with the defined `region` prefixed to the netlocation."""
  url_parts = url.split('://')
  url_scheme = url_parts[0]
  return url_scheme + '://' + region + '-' + url_parts[1]


def RemoveRegionFromEndpoint(endpoint):
  """Returns a new endpoint string stripped of the region if one exists."""
  region = DeriveRegionFromEndpoint(endpoint)
  if region:
    endpoint = endpoint.replace(region + '-', '')
  return endpoint


def GetResourceInfo(request):
  """Returns a tuple of the resource and resource name from the `request`.

  Args:
    request: A Request object instance.

  Returns:
    A tuple of the resource string path and the resource name.

  Raises:
    UnexpectedResourceField: The `request` had a unsupported resource.
  """
  resource = ''
  resource_name = ''

  if hasattr(request, 'parent'):
    resource = request.parent
    resource_name = 'parent'
  elif hasattr(request, 'name'):
    resource = request.name
    resource_name = 'name'
  elif hasattr(request, 'subscription'):
    resource = request.subscription
    resource_name = 'subscription'
  else:
    raise UnexpectedResourceField(
        'The resource specified for this command is unknown!')

  return resource, resource_name


def LocationToZoneOrRegion(location_id):
  # pylint: disable=g-import-not-at-top
  from google.cloud.pubsublite import types
  # pylint: enable=g-import-not-at-top
  if len(location_id.split('-')) == 3:
    return types.CloudZone.parse(location_id)
  else:
    return types.CloudRegion.parse(location_id)


def DeriveLocationFromResource(resource):
  """Returns the location from a resource string."""
  location = resource[resource.index(LOCATIONS_RESOURCE_PATH) +
                      len(LOCATIONS_RESOURCE_PATH):]
  location = location.split('/')[0]
  return location


def DeriveProjectFromResource(resource):
  """Returns the project from a resource string."""
  project = resource[resource.index(PROJECTS_RESOURCE_PATH) +
                     len(PROJECTS_RESOURCE_PATH):]
  project = project.split('/')[0]
  return project


def ParseResource(request):
  """Returns an updated `request` with the resource path parsed."""
  resource, resource_name = GetResourceInfo(request)
  new_resource = resource[resource.rindex(PROJECTS_RESOURCE_PATH):]
  setattr(request, resource_name, new_resource)

  return request


def OverrideEndpointWithRegion(request):
  """Sets the pubsublite endpoint override to include the region."""
  resource, _ = GetResourceInfo(request)
  region = DeriveRegionFromLocation(DeriveLocationFromResource(resource))

  endpoint = apis.GetEffectiveApiEndpoint(PUBSUBLITE_API_NAME,
                                          PUBSUBLITE_API_VERSION)

  # Remove any region from the endpoint in case it was previously set.
  # Specifically this effects scenario tests where multiple tests are run in a
  # single instance.
  endpoint = RemoveRegionFromEndpoint(endpoint)

  regional_endpoint = CreateRegionalEndpoint(region, endpoint)
  properties.VALUES.api_endpoint_overrides.pubsublite.Set(regional_endpoint)


def ProjectIdToProjectNumber(project_id):
  """Returns the Cloud project number associated with the `project_id`."""
  crm_message_module = apis.GetMessagesModule('cloudresourcemanager', 'v1')
  resource_manager = apis.GetClientInstance('cloudresourcemanager', 'v1')

  req = crm_message_module.CloudresourcemanagerProjectsGetRequest(
      projectId=project_id)
  project = resource_manager.projects.Get(req)

  return project.projectNumber


def OverrideProjectIdToProjectNumber(request):
  """Returns an updated `request` with the Cloud project number."""
  resource, resource_name = GetResourceInfo(request)
  project_id = DeriveProjectFromResource(resource)
  project_number = ProjectIdToProjectNumber(project_id)
  setattr(request, resource_name,
          resource.replace(project_id, six.text_type(project_number)))

  return request


def UpdateAdminRequest(resource_ref, args, request):
  """Returns an updated `request` with values for a valid Admin request."""
  # Unused resource reference.
  del resource_ref, args

  request = ParseResource(request)
  request = OverrideProjectIdToProjectNumber(request)
  OverrideEndpointWithRegion(request)

  return request


def UpdateCommitCursorRequest(resource_ref, args, request):
  """Updates a CommitCursorRequest by adding 1 to the provided offset."""
  # Unused resource reference.
  del resource_ref, args

  request = ParseResource(request)
  # Add 1 to the offset so that the message corresponding to the provided offset
  # is included in the list of messages that are acknowledged.
  request.commitCursorRequest.cursor.offset += 1
  OverrideEndpointWithRegion(request)

  return request


def _HasReservation(topic):
  """Returns whether the topic has a reservation set."""
  if topic.reservationConfig is None:
    return False
  return bool(topic.reservationConfig.throughputReservation)


def AddTopicDefaultsWithoutReservation(resource_ref, args, request):
  """Adds the default values for topic throughput fields with no reservation."""
  # Unused resource reference and arguments.
  del resource_ref, args

  topic = request.topic
  if not _HasReservation(topic):
    if topic.partitionConfig is None:
      topic.partitionConfig = {}
    if topic.partitionConfig.capacity is None:
      topic.partitionConfig.capacity = {}
    capacity = topic.partitionConfig.capacity
    if capacity.publishMibPerSec is None:
      capacity.publishMibPerSec = 4
    if capacity.subscribeMibPerSec is None:
      capacity.subscribeMibPerSec = 8

  return request


def AddTopicReservationResource(resource_ref, args, request):
  """Returns an updated `request` with a resource path on the reservation."""
  # Unused resource reference and arguments.
  del resource_ref, args

  topic = request.topic
  if not _HasReservation(topic):
    return request

  resource, _ = GetResourceInfo(request)
  project = DeriveProjectFromResource(resource)
  region = DeriveRegionFromLocation(DeriveLocationFromResource(resource))
  reservation = topic.reservationConfig.throughputReservation
  request.topic.reservationConfig.throughputReservation = (
      '{}{}/{}{}/{}{}'.format(
          PROJECTS_RESOURCE_PATH, project, LOCATIONS_RESOURCE_PATH, region,
          RESERVATIONS_RESOURCE_PATH, reservation))

  return request


def AddSubscriptionTopicResource(resource_ref, args, request):
  """Returns an updated `request` with a resource path on the topic."""
  # Unused resource reference and arguments.
  del resource_ref, args

  resource, _ = GetResourceInfo(request)
  request.subscription.topic = '{}/{}{}'.format(resource, TOPICS_RESOURCE_PATH,
                                                request.subscription.topic)

  return request


def ConfirmPartitionsUpdate(resource_ref, args, request):
  """Prompts to confirm an update to a topic's partition count."""
  del resource_ref
  if 'partitions' not in args or not args.partitions:
    return request
  console_io.PromptContinue(
      message=(
          'Warning: The number of partitions in a topic can be increased but'
          ' not decreased. Additionally message order is not guaranteed across'
          ' a topic resize. See'
          ' https://cloud.google.com/pubsub/lite/docs/topics#scaling_capacity'
          ' for more details'),
      default=True,
      cancel_on_no=True)
  return request


def UpdateSkipBacklogField(resource_ref, args, request):
  # Unused resource reference
  del resource_ref

  if hasattr(args, 'starting_offset'):
    request.skipBacklog = (args.starting_offset == 'end')

  return request


def GetLocationValue(args):
  """Returns the raw location argument."""
  return args.location or args.zone


def GetLocation(args):
  """Returns the resource location (zone or region) extracted from arguments.

  Args:
    args: argparse.Namespace, the parsed commandline arguments.

  Raises:
    InvalidResourcePath: if the location component in a fully qualified path is
    invalid.
  """
  location = GetLocationValue(args)
  if LOCATIONS_RESOURCE_PATH not in location:
    return location

  parsed_location = DeriveLocationFromResource(location)
  if not parsed_location:
    raise InvalidResourcePath(
        'The location component in the specified location path is invalid: `{}`.'
        .format(location))
  return parsed_location


def GetProject(args):
  """Returns the project from either arguments or attributes.

  Args:
    args: argparse.Namespace, the parsed commandline arguments.

  Raises:
    InvalidResourcePath: if the project component in a fully qualified path is
    invalid.
  """
  location = GetLocationValue(args)
  if not location.startswith(PROJECTS_RESOURCE_PATH):
    return args.project or properties.VALUES.core.project.GetOrFail()

  parsed_project = DeriveProjectFromResource(location)
  if not parsed_project:
    raise InvalidResourcePath(
        'The project component in the specified location path is invalid: `{}`.'
        .format(location))
  return parsed_project


def GetDeliveryRequirement(args, psl):
  """Returns the DeliveryRequirement enum from arguments."""
  if args.delivery_requirement == 'deliver-after-stored':
    return psl.DeliveryConfig.DeliveryRequirementValueValuesEnum.DELIVER_AFTER_STORED
  return psl.DeliveryConfig.DeliveryRequirementValueValuesEnum.DELIVER_IMMEDIATELY


def GetDesiredExportState(args, psl):
  """Returns the export DesiredState enum from arguments."""
  if args.export_desired_state == 'paused':
    return psl.ExportConfig.DesiredStateValueValuesEnum.PAUSED
  return psl.ExportConfig.DesiredStateValueValuesEnum.ACTIVE


def GetSeekRequest(args, psl):
  """Returns a SeekSubscriptionRequest from arguments."""
  if args.publish_time:
    return psl.SeekSubscriptionRequest(
        timeTarget=psl.TimeTarget(
            publishTime=util.FormatSeekTime(args.publish_time)))
  elif args.event_time:
    return psl.SeekSubscriptionRequest(
        timeTarget=psl.TimeTarget(
            eventTime=util.FormatSeekTime(args.event_time)))
  elif args.starting_offset:
    if args.starting_offset == 'beginning':
      return psl.SeekSubscriptionRequest(namedTarget=psl.SeekSubscriptionRequest
                                         .NamedTargetValueValuesEnum.TAIL)
    elif args.starting_offset == 'end':
      return psl.SeekSubscriptionRequest(namedTarget=psl.SeekSubscriptionRequest
                                         .NamedTargetValueValuesEnum.HEAD)
    else:
      # Should already be validated.
      raise InvalidSeekTarget(
          'Invalid starting offset value! Must be one of: [beginning, end].')
  else:
    # Should already be validated.
    raise InvalidSeekTarget('Seek target must be specified!')


def SetExportConfigResources(args, psl, project, location, export_config):
  """Sets fully qualified resource paths for an ExportConfig."""
  if args.export_pubsub_topic:
    topic = args.export_pubsub_topic
    if not topic.startswith(PROJECTS_RESOURCE_PATH):
      topic = ('{}{}/{}{}'.format(PROJECTS_RESOURCE_PATH, project,
                                  TOPICS_RESOURCE_PATH, topic))
    export_config.pubsubConfig = psl.PubSubConfig(topic=topic)

  if args.export_dead_letter_topic:
    topic = args.export_dead_letter_topic
    if not topic.startswith(PROJECTS_RESOURCE_PATH):
      topic = ('{}{}/{}{}/{}{}'.format(PROJECTS_RESOURCE_PATH, project,
                                       LOCATIONS_RESOURCE_PATH, location,
                                       TOPICS_RESOURCE_PATH, topic))
    export_config.deadLetterTopic = topic


def GetExportConfig(args, psl, project, location, requires_seek):
  """Returns an ExportConfig from arguments."""
  if args.export_pubsub_topic is None:
    return None

  desired_state = GetDesiredExportState(args, psl)
  if requires_seek:
    # Will be updated to Active after seek.
    desired_state = psl.ExportConfig.DesiredStateValueValuesEnum.PAUSED

  export_config = psl.ExportConfig(desiredState=desired_state)
  SetExportConfigResources(args, psl, project, location, export_config)
  return export_config


def ExecuteCreateSubscriptionRequest(resource_ref, args):
  """Issues a CreateSubscriptionRequest and potentially other requests.

  Args:
    resource_ref: resources.Resource, the resource reference for the resource
      being operated on.
    args: argparse.Namespace, the parsed commandline arguments.

  Returns:
    The created Pub/Sub Lite Subscription.
  """
  psl = PubsubLiteMessages()
  location = GetLocation(args)
  project_id = GetProject(args)
  project_number = six.text_type(ProjectIdToProjectNumber(project_id))
  requires_seek = args.publish_time or args.event_time

  # Request 1 - Create the subscription.
  create_request = psl.PubsubliteAdminProjectsLocationsSubscriptionsCreateRequest(
      parent=('{}{}/{}{}'.format(PROJECTS_RESOURCE_PATH, project_number,
                                 LOCATIONS_RESOURCE_PATH, location)),
      subscription=psl.Subscription(
          topic=args.topic,
          deliveryConfig=psl.DeliveryConfig(
              deliveryRequirement=GetDeliveryRequirement(args, psl)),
          exportConfig=GetExportConfig(args, psl, project_number, location,
                                       requires_seek)),
      subscriptionId=args.subscription)
  OverrideEndpointWithRegion(create_request)
  AddSubscriptionTopicResource(resource_ref, args, create_request)
  if not requires_seek:
    UpdateSkipBacklogField(resource_ref, args, create_request)

  client = PubsubLiteClient()
  response = client.admin_projects_locations_subscriptions.Create(
      create_request)

  # Request 2 (optional) - seek the subscription.
  if requires_seek:
    seek_request = psl.PubsubliteAdminProjectsLocationsSubscriptionsSeekRequest(
        name=response.name, seekSubscriptionRequest=GetSeekRequest(args, psl))
    client.admin_projects_locations_subscriptions.Seek(seek_request)

  # Request 3 (optional) - make the export subscription active.
  if requires_seek and create_request.subscription.exportConfig and args.export_desired_state == 'active':
    update_request = psl.PubsubliteAdminProjectsLocationsSubscriptionsPatchRequest(
        name=response.name,
        updateMask='export_config.desired_state',
        subscription=psl.Subscription(
            exportConfig=psl.ExportConfig(desiredState=psl.ExportConfig
                                          .DesiredStateValueValuesEnum.ACTIVE)))
    response = client.admin_projects_locations_subscriptions.Patch(
        update_request)

  return response


def AddExportResources(resource_ref, args, request):
  """Sets export resource paths for an UpdateSubscriptionRequest.

  Args:
    resource_ref: resources.Resource, the resource reference for the resource
      being operated on.
    args: argparse.Namespace, the parsed commandline arguments.
    request: An UpdateSubscriptionRequest.

  Returns:
    The UpdateSubscriptionRequest.
  """
  # Unused resource reference
  del resource_ref

  if request.subscription.exportConfig is None:
    return request

  resource, _ = GetResourceInfo(request)
  project = DeriveProjectFromResource(resource)
  location = DeriveLocationFromResource(resource)
  psl = PubsubLiteMessages()
  SetExportConfigResources(args, psl, project, location,
                           request.subscription.exportConfig)
  return request


def SetSeekTarget(resource_ref, args, request):
  """Sets the target for a SeekSubscriptionRequest."""
  # Unused resource reference
  del resource_ref

  psl = PubsubLiteMessages()
  request.seekSubscriptionRequest = GetSeekRequest(args, psl)
  log.warning(
      'The seek operation will complete once subscribers react to the seek. ' +
      'If subscribers are offline, `pubsub lite-operations describe` can be ' +
      'used to check the operation status later.')
  return request


def UpdateListOperationsFilter(resource_ref, args, request):
  """Updates the filter for a ListOperationsRequest."""
  # Unused resource reference
  del resource_ref

  # If the --filter arg is specified, let gcloud handle it client-side.
  if args.filter:
    return request

  # Otherwise build the filter if the --subscription and/or --done flags are
  # specified. The server will handle filtering.
  if args.subscription:
    # Note: This relies on project ids replaced with project numbers until
    # b/194764731 is fixed.
    request.filter = 'target={}/{}{}'.format(request.name,
                                             SUBSCRIPTIONS_RESOURCE_PATH,
                                             args.subscription)
  if args.done:
    if request.filter:
      request.filter += ' AND '
    else:
      request.filter = ''
    request.filter += 'done={}'.format(args.done)
  return request


def RequirePython36(cmd='gcloud'):
  """Verifies that the python version is 3.6+.

  Args:
    cmd: The string command that requires python 3.6+.

  Raises:
    InvalidPythonVersion: if the python version is not 3.6+.
  """
  if sys.version_info.major < 3 or (sys.version_info.major == 3 and
                                    sys.version_info.minor < 6):
    raise InvalidPythonVersion(
        """The `{}` command requires python 3.6 or greater. Please update the
        python version to use this command.""".format(cmd))
