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
"""Flags for Eventarc commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import googlecloudsdk
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties

_IAM_API_VERSION = 'v1'


def LocationAttributeConfig(required=True):
  """Builds an AttributeConfig for the location resource."""
  fallthroughs_list = [
      deps.PropertyFallthrough(properties.FromString('eventarc/location'))
  ]
  help_text = ('The location for the Eventarc {resource}, which should be '
               "either ``global'' or one of the supported regions. "
               'Alternatively, set the [eventarc/location] property.')
  if not required:
    fallthroughs_list.append(
        deps.Fallthrough(
            googlecloudsdk.command_lib.eventarc.flags.SetLocation,
            'use \'-\' location to aggregate results for all Eventarc locations'
        ))
    help_text = ('The location for the Eventarc {resource}, which should be '
                 "either ``global'' or one of the supported regions. "
                 "Use ``-'' to aggregate results for all Eventarc locations. "
                 'Alternatively, set the [eventarc/location] property.')
  return concepts.ResourceParameterAttributeConfig(
      name='location', fallthroughs=fallthroughs_list, help_text=help_text)


def SetLocation():
  return '-'


def TriggerAttributeConfig():
  """Builds an AttributeConfig for the trigger resource."""
  return concepts.ResourceParameterAttributeConfig(name='trigger')


def ChannelAttributeConfig():
  """Builds an AttributeConfig for the channel resource."""
  return concepts.ResourceParameterAttributeConfig(name='channel')


def ChannelConnectionAttributeConfig():
  """Builds an AttributeConfig for the channel connection resource."""
  return concepts.ResourceParameterAttributeConfig(name='channel-connection')


def ProviderAttributeConfig():
  """Builds an AttributeConfig for the provider resource."""
  return concepts.ResourceParameterAttributeConfig(name='provider')


def TransportTopicAttributeConfig():
  """Builds an AttributeConfig for the transport topic resource."""
  return concepts.ResourceParameterAttributeConfig(name='transport-topic')


def TriggerResourceSpec():
  """Builds a ResourceSpec for trigger resource."""
  return concepts.ResourceSpec(
      'eventarc.projects.locations.triggers',
      resource_name='trigger',
      triggersId=TriggerAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def ChannelResourceSpec():
  """Builds a ResourceSpec for channel resource."""
  return concepts.ResourceSpec(
      'eventarc.projects.locations.channels',
      resource_name='channel',
      channelsId=ChannelAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def ChannelConnectionResourceSpec():
  """Builds a ResourceSpec for channel connection resource."""
  return concepts.ResourceSpec(
      'eventarc.projects.locations.channelConnections',
      resource_name='channel connection',
      channelConnectionsId=ChannelConnectionAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def ProviderResourceSpec():
  """Builds a ResourceSpec for event provider."""
  return concepts.ResourceSpec(
      'eventarc.projects.locations.providers',
      resource_name='provider',
      providersId=ProviderAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddTransportTopicResourceArg(parser, required=False):
  """Adds a resource argument for a customer-provided transport topic."""
  resource_spec = concepts.ResourceSpec(
      'pubsub.projects.topics',
      resource_name='Pub/Sub topic',
      topicsId=TransportTopicAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  concept_parser = concept_parsers.ConceptParser.ForResource(
      '--transport-topic',
      resource_spec,
      "The Cloud Pub/Sub topic to use for the trigger's transport "
      'intermediary. This feature is currently only available for triggers '
      "of event type ``google.cloud.pubsub.topic.v1.messagePublished''. "
      'The topic must be in the same project as the trigger. '
      'If not specified, a transport topic will be created.',
      required=required)
  concept_parser.AddToParser(parser)


def AddLocationResourceArg(parser, group_help_text, required=False):
  """Adds a resource argument for an Eventarc location."""
  resource_spec = concepts.ResourceSpec(
      'eventarc.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(required),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  concept_parser = concept_parsers.ConceptParser.ForResource(
      '--location', resource_spec, group_help_text, required=required)
  concept_parser.AddToParser(parser)


def AddProjectResourceArg(parser):
  """Adds a resource argument for a project."""
  resource_spec = concepts.ResourceSpec(
      'eventarc.projects',
      resource_name='project',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  concept_parser = concept_parsers.ConceptParser.ForResource(
      '--project',
      resource_spec,
      'Project ID of the Google Cloud project for the {resource}.',
      required=True)
  concept_parser.AddToParser(parser)


def AddTriggerResourceArg(parser, group_help_text, required=False):
  """Adds a resource argument for an Eventarc trigger."""
  concept_parsers.ConceptParser.ForResource(
      'trigger', TriggerResourceSpec(), group_help_text,
      required=required).AddToParser(parser)


def AddCreateTrigerResourceArgs(parser, release_track):
  """Adds trigger and channel arguments to for trigger creation."""
  if release_track == base.ReleaseTrack.GA:
    concept_parsers.ConceptParser(
        [
            presentation_specs.ResourcePresentationSpec(
                'trigger',
                TriggerResourceSpec(),
                'The trigger to create.',
                required=True),
            presentation_specs.ResourcePresentationSpec(
                '--channel',
                ChannelResourceSpec(),
                'The channel to use in the trigger. The channel is needed only if trigger is created for a third-party provider.',
                flag_name_overrides={'location': ''})
        ],
        # This configures the fallthrough from the channel 's location to
        # the primary flag for the trigger's location.
        command_level_fallthroughs={
            '--channel.location': ['trigger.location']
        }).AddToParser(parser)
  else:
    AddTriggerResourceArg(parser, 'The trigger to create.', required=True)


def AddChannelResourceArg(parser, group_help_text, required=False):
  """Adds a resource argument for an Eventarc channel."""
  concept_parsers.ConceptParser.ForResource(
      'channel', ChannelResourceSpec(), group_help_text,
      required=required).AddToParser(parser)


def AddChannelConnectionResourceArg(parser, group_help_text):
  """Adds a resource argument for an Eventarc channel connection."""
  concept_parsers.ConceptParser.ForResource(
      'channel_connection',
      ChannelConnectionResourceSpec(),
      group_help_text,
      required=True).AddToParser(parser)


def AddProviderResourceArg(parser, group_help_text, required=False):
  """Adds a resource argument for an Eventarc provider."""
  concept_parsers.ConceptParser.ForResource(
      'provider', ProviderResourceSpec(), group_help_text,
      required=required).AddToParser(parser)


def AddProviderNameArg(parser):
  """Adds an argument for an Eventarc provider name."""
  parser.add_argument(
      '--name',
      required=False,
      help='A provider name (e.g. `storage.googleapis.com`) List results will be filtered on this provider. '
      'Only exact match of the provider name is supported.')


def AddEventPublishingArgs(parser):
  """Adds an argument for an Eventarc channel and channel connection."""
  parser.add_argument(
      '--event-id',
      required=True,
      help='An event id. The id of a published event.')

  parser.add_argument(
      '--event-type',
      required=True,
      help='An event type. The event type of a published event.')

  parser.add_argument(
      '--event-source',
      required=True,
      help='An event source. The event source of a published event.')

  parser.add_argument(
      '--event-data',
      required=True,
      help='An event data. The event data of a published event.')

  parser.add_argument(
      '--event-attributes',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(),
      metavar='ATTRIBUTE=VALUE',
      help='Event attributes. The event attributes of a published event.'
      'This flag can be repeated to add more attributes.')


def AddServiceAccountArg(parser, required=False):
  """Adds an argument for the trigger's service account."""
  parser.add_argument(
      '--service-account',
      required=required,
      help='The IAM service account email associated with the trigger.')


def AddEventFiltersArg(parser, release_track, required=False):
  """Adds an argument for the trigger's event filters."""
  if release_track == base.ReleaseTrack.GA:
    flag = '--event-filters'
    help_text = (
        "The trigger's list of filters that apply to CloudEvents attributes. "
        'This flag can be repeated to add more filters to the list. Only '
        'events that match all these filters will be sent to the destination. '
        "The filters must include the ``type'' attribute, as well as any other "
        'attributes that are expected for the chosen type.')
  else:
    flag = '--matching-criteria'
    help_text = (
        'The criteria by which events are filtered for the trigger, specified '
        'as a comma-separated list of CloudEvents attribute names and values. '
        'This flag can also be repeated to add more criteria to the list. Only '
        'events that match with this criteria will be sent to the destination. '
        "The criteria must include the ``type'' attribute, as well as any "
        'other attributes that are expected for the chosen type.')
  parser.add_argument(
      flag,
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(),
      required=required,
      help=help_text,
      metavar='ATTRIBUTE=VALUE')


def AddEventFiltersPathPatternArg(parser,
                                  release_track,
                                  required=False,
                                  hidden=False):
  """Adds an argument for the trigger's event filters in path pattern format."""
  if release_track == base.ReleaseTrack.GA:
    parser.add_argument(
        '--event-filters-path-pattern',
        action=arg_parsers.UpdateAction,
        type=arg_parsers.ArgDict(),
        hidden=hidden,
        required=required,
        help="The trigger's list of filters in path pattern format that apply "
        'to CloudEvent attributes. This flag can be repeated to add more '
        'filters to the list. Only events that match all these filters will be '
        'sent to the destination. Currently, path pattern format is only '
        'available for the resourceName attribute for Cloud Audit Log events.',
        metavar='ATTRIBUTE=PATH_PATTERN')


def AddEventDataContentTypeArg(
    parser, release_track, required=False, hidden=False
):
  """Adds an argument for the trigger's event data content type."""
  if release_track == base.ReleaseTrack.GA:
    parser.add_argument(
        '--event-data-content-type',
        hidden=hidden,
        required=required,
        help=(
            'Depending on the event provider, you can specify the encoding of'
            ' the event data payload that will be delivered to your'
            " destination, to either be encoded in ``application/json'' or"
            " ``application/protobuf''. The default encoding is"
            " ``application/json''."
            ' Note that for custom sources or third-party providers, or for'
            ' direct events from Cloud Pub/Sub, this formatting option is not'
            ' supported.'
        ),
    )


def GetEventFiltersArg(args, release_track):
  """Gets the event filters from the arguments."""
  if release_track == base.ReleaseTrack.GA:
    return args.event_filters
  else:
    return args.matching_criteria


def GetEventFiltersPathPatternArg(args, release_track):
  """Gets the event filters with path pattern from the arguments."""
  if release_track == base.ReleaseTrack.GA:
    return args.event_filters_path_pattern
  return None


def GetEventDataContentTypeArg(args, release_track):
  """Gets the event data content type from the arguments."""
  if release_track == base.ReleaseTrack.GA:
    return args.event_data_content_type
  return None


def GetChannelArg(args, release_track):
  """Gets the channel from the arguments."""
  if release_track == base.ReleaseTrack.GA:
    return args.CONCEPTS.channel.Parse()
  return None


def AddCreateDestinationArgs(parser, release_track, required=False):
  """Adds arguments related to trigger's destination for create operations."""
  dest_group = parser.add_mutually_exclusive_group(
      required=required,
      help='Flags for specifying the destination to which events should be sent.'
  )
  _AddCreateCloudRunDestinationArgs(dest_group, release_track)
  if release_track == base.ReleaseTrack.GA:
    _AddCreateGKEDestinationArgs(dest_group)
    _AddCreateWorkflowDestinationArgs(dest_group, hidden=True)
    _AddCreateFunctionDestinationArgs(dest_group, hidden=True)
    _AddCreateHTTPEndpointDestinationArgs(dest_group)


def _AddCreateCloudRunDestinationArgs(parser, release_track, required=False):
  """Adds arguments related to trigger's Cloud Run fully-managed resource destination for create operations."""
  run_group = parser.add_group(
      required=required,
      help='Flags for specifying a Cloud Run fully-managed resource destination.'
  )
  resource_group = run_group.add_mutually_exclusive_group(required=True)
  AddDestinationRunServiceArg(resource_group)
  # When this is not True and only the service flag is in the mutually exclusive
  # group, it will appear the same as if it was directly in the base run_group.
  if release_track == base.ReleaseTrack.GA:
    AddDestinationRunJobArg(resource_group)
  AddDestinationRunPathArg(run_group)
  AddDestinationRunRegionArg(run_group)


def _AddCreateGKEDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's GKE service destination for create operations."""
  gke_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for specifying a GKE service destination.')
  _AddDestinationGKEClusterArg(gke_group, required=True)
  _AddDestinationGKELocationArg(gke_group)
  _AddDestinationGKENamespaceArg(gke_group)
  _AddDestinationGKEServiceArg(gke_group, required=True)
  _AddDestinationGKEPathArg(gke_group)


def _AddCreateWorkflowDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's Workflows destination for create operations."""
  workflow_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for specifying a Workflow destination.')
  _AddDestinationWorkflowArg(workflow_group, required=True)
  _AddDestinationWorkflowLocationArg(workflow_group)


def _AddCreateHTTPEndpointDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's HTTP Endpoint destination for create operations."""
  http_endpoint_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for specifying a HTTP Endpoint destination.')
  _AddDestinationHTTPEndpointUriArg(http_endpoint_group, required=True)
  _AddCreateNetworkConfigDestinationArgs(http_endpoint_group)


def _AddCreateNetworkConfigDestinationArgs(
    parser, required=False, hidden=False
):
  """Adds arguments related to trigger's Network Config destination for create operations."""
  network_config_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for specifying a Network Config for the destination.',
  )
  _AddNetworkAttachmentArg(network_config_group, required=True)


def _AddCreateFunctionDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's Function destination for create operation."""
  function_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for specifying a Function destination.')
  _AddDestinationFunctionArg(function_group, required=True)
  _AddDestinationFunctionLocationArg(function_group)


def AddUpdateDestinationArgs(parser, release_track, required=False):
  """Adds arguments related to trigger's destination for update operations."""
  dest_group = parser.add_mutually_exclusive_group(
      required=required,
      help='Flags for updating the destination to which events should be sent.')
  _AddUpdateCloudRunDestinationArgs(dest_group, release_track)
  if release_track == base.ReleaseTrack.GA:
    _AddUpdateGKEDestinationArgs(dest_group)
    _AddUpdateWorkflowDestinationArgs(dest_group, hidden=True)
    _AddUpdateFunctionDestinationArgs(dest_group, hidden=True)


def _AddUpdateCloudRunDestinationArgs(parser, release_track, required=False):
  """Adds arguments related to trigger's Cloud Run fully-managed resource destination for update operations."""
  run_group = parser.add_group(
      required=required,
      help='Flags for updating a Cloud Run fully-managed resource destination.')
  resource_group = run_group.add_mutually_exclusive_group()
  AddDestinationRunServiceArg(resource_group)
  # When this is not True and only the service flag is in the mutually exclusive
  # group, it will appear the same as if it was directly in the base run_group.
  if release_track == base.ReleaseTrack.GA:
    AddDestinationRunJobArg(resource_group)
  AddDestinationRunRegionArg(run_group)
  destination_run_path_group = run_group.add_mutually_exclusive_group()
  AddDestinationRunPathArg(destination_run_path_group)
  AddClearDestinationRunPathArg(destination_run_path_group)


def _AddUpdateGKEDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's GKE service destination for update operations."""
  gke_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for updating a GKE service destination.')
  _AddDestinationGKENamespaceArg(gke_group)
  _AddDestinationGKEServiceArg(gke_group)
  destination_gke_path_group = gke_group.add_mutually_exclusive_group()
  _AddDestinationGKEPathArg(destination_gke_path_group)
  _AddClearDestinationGKEPathArg(destination_gke_path_group)


def _AddUpdateWorkflowDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's Workflow destination for update operations."""
  workflow_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for updating a Workflow destination.')
  _AddDestinationWorkflowArg(workflow_group)
  _AddDestinationWorkflowLocationArg(workflow_group)


def _AddUpdateFunctionDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's Function destination for update operations."""
  function_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for updating a Function destination.')
  _AddDestinationFunctionArg(function_group)
  _AddDestinationFunctionLocationArg(function_group)


def AddDestinationRunServiceArg(parser):
  """Adds an argument for the trigger's destination Cloud Run service."""
  parser.add_argument(
      '--destination-run-service',
      help='Name of the Cloud Run fully-managed service that receives the '
      'events for the trigger. The service must be in the same project as the '
      'trigger.')


def AddDestinationRunJobArg(parser):
  """Adds an argument for the trigger's destination Cloud Run job."""
  parser.add_argument(
      '--destination-run-job',
      hidden=True,
      help='Name of the Cloud Run fully-managed job that receives the '
      'events for the trigger. The job must be in the same project as the '
      'trigger.')


def AddDestinationRunPathArg(parser, required=False):
  """Adds an argument for the trigger's destination path on the Cloud Run service."""
  parser.add_argument(
      '--destination-run-path',
      required=required,
      help='Relative path on the destination Cloud Run service to which '
      "the events for the trigger should be sent. Examples: ``/route'', "
      "``route'', ``route/subroute''.")


def AddDestinationRunRegionArg(parser, required=False):
  """Adds an argument for the trigger's destination Cloud Run service's region."""
  parser.add_argument(
      '--destination-run-region',
      required=required,
      help='Region in which the destination Cloud Run service can be '
      'found. If not specified, it is assumed that the service is in the same '
      'region as the trigger.')


def _AddDestinationGKEClusterArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's cluster."""
  parser.add_argument(
      '--destination-gke-cluster',
      required=required,
      help='Name of the GKE cluster that the destination GKE service is '
      'running in.  The cluster must be in the same project as the trigger.')


def _AddDestinationGKELocationArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's location."""
  parser.add_argument(
      '--destination-gke-location',
      required=required,
      help='Location of the GKE cluster that the destination GKE service '
      'is running in. If not specified, it is assumed that the cluster is a '
      'regional cluster and is in the same region as the trigger.')


def _AddDestinationGKENamespaceArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's namespace."""
  parser.add_argument(
      '--destination-gke-namespace',
      required=required,
      help='Namespace that the destination GKE service is running in. If '
      "not specified, the ``default'' namespace is used.")


def _AddDestinationGKEServiceArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's name."""
  parser.add_argument(
      '--destination-gke-service',
      required=required,
      help='Name of the destination GKE service that receives the events '
      'for the trigger.')


def _AddDestinationGKEPathArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's name."""
  parser.add_argument(
      '--destination-gke-path',
      required=required,
      help='Relative path on the destination GKE service to which '
      "the events for the trigger should be sent. Examples: ``/route'', "
      "``route'', ``route/subroute''.")


def _AddDestinationWorkflowArg(parser, required=False):
  """Adds an argument for the trigger's destination Workflow."""
  parser.add_argument(
      '--destination-workflow',
      required=required,
      help='ID of the Workflow that receives the events for the trigger. '
      'The Workflow must be in the same project as the trigger.')


def _AddDestinationWorkflowLocationArg(parser, required=False):
  """Adds an argument for the trigger's destination Workflow location."""
  parser.add_argument(
      '--destination-workflow-location',
      required=required,
      help='Location that the destination Workflow is running in. '
      'If not specified, it is assumed that the Workflow is in the same '
      'location as the trigger.')


def _AddDestinationFunctionArg(parser, required=False):
  """Adds an argument for the trigger's destination Function."""
  parser.add_argument(
      '--destination-function',
      required=required,
      help='ID of the Function that receives the events for the trigger. '
      'The Function must be in the same project as the trigger.')


def _AddDestinationFunctionLocationArg(parser, required=False):
  """Adds an argument for the trigger's destination Function location."""
  parser.add_argument(
      '--destination-function-location',
      required=required,
      help='Location that the destination Function is running in. '
      'If not specified, it is assumed that the Function is in the same '
      'location as the trigger.')


def _AddDestinationHTTPEndpointUriArg(parser, required=False):
  """Adds an argument for the trigger's HTTP endpoint destination URI."""
  parser.add_argument(
      '--destination-http-endpoint-uri',
      required=required,
      help='URI that the destination HTTP Endpoint is connecting to.')


def _AddNetworkAttachmentArg(parser, required=False):
  """Adds an argument for the trigger's destination service account."""
  parser.add_argument(
      '--network-attachment',
      required=required,
      help=(
          'The network attachment associated with the trigger that allows'
          ' access to the destination VPC.'
      ),
  )


def AddClearServiceAccountArg(parser):
  parser.add_argument(
      '--clear-service-account',
      action='store_true',
      help='Clear the IAM service account associated with the trigger.',
  )


def AddClearDestinationRunPathArg(parser):
  """Adds an argument for clearing the trigger's Cloud Run destination path."""
  parser.add_argument(
      '--clear-destination-run-path',
      action='store_true',
      help='Clear the relative path on the destination Cloud Run service to '
      'which the events for the trigger should be sent.')


def _AddClearDestinationGKEPathArg(parser):
  """Adds an argument for clearing the trigger's GKE destination path."""
  parser.add_argument(
      '--clear-destination-gke-path',
      action='store_true',
      help='Clear the relative path on the destination GKE service to which '
      'the events for the trigger should be sent.')


def AddTypePositionalArg(parser, help_text):
  """Adds a positional argument for the event type."""
  parser.add_argument('type', help=help_text)


def AddTypeArg(parser, required=False):
  """Adds an argument for the event type."""
  parser.add_argument('--type', required=required, help='The event type.')


def AddServiceNameArg(parser, required=False):
  """Adds an argument for the value of the serviceName CloudEvents attribute."""
  parser.add_argument(
      '--service-name',
      required=required,
      help='The value of the serviceName CloudEvents attribute.')


def AddCreateChannelArg(parser):
  concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              'channel',
              ChannelResourceSpec(),
              'Channel to create.',
              required=True),
          presentation_specs.ResourcePresentationSpec(
              '--provider',
              ProviderResourceSpec(),
              'Provider to use for the channel.',
              flag_name_overrides={'location': ''}),
      ],
      # This configures the fallthrough from the provider's location to the
      # primary flag for the channel's location
      command_level_fallthroughs={
          '--provider.location': ['channel.location']
      }).AddToParser(parser)


def AddCryptoKeyArg(parser, required=False, hidden=False, with_clear=True):
  """Adds an argument for the crypto key used for CMEK."""
  policy_group = parser
  if with_clear:
    policy_group = parser.add_mutually_exclusive_group(hidden=hidden)
    AddClearCryptoNameArg(policy_group, required, hidden)
  policy_group.add_argument(
      '--crypto-key',
      required=required,
      hidden=hidden,
      help='Fully qualified name of the crypto key to use for '
      'customer-managed encryption. If this is unspecified, Google-managed '
      'keys will be used for encryption.')


def AddClearCryptoNameArg(parser, required=False, hidden=False):
  """Adds an argument for the crypto key used for CMEK."""
  parser.add_argument(
      '--clear-crypto-key',
      required=required,
      hidden=hidden,
      default=False,
      action='store_true',
      help=(
          'Remove the previously configured crypto key. The channel will'
          ' continue to be encrypted using Google-managed keys.'
      ),
  )
