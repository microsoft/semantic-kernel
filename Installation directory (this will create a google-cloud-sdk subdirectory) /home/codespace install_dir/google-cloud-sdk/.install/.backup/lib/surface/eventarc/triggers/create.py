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
"""Command to create a trigger."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.eventarc import triggers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc import flags
from googlecloudsdk.command_lib.eventarc import types
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To create a new trigger ``my-trigger'' for events of type ``google.cloud.pubsub.topic.v1.messagePublished'' with destination Cloud Run service ``my-service'', run:

          $ {command} my-trigger --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" --destination-run-service=my-service
        """,
}

_DETAILED_HELP_BETA = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """ \
        To create a new trigger ``my-trigger'' for events of type ``google.cloud.pubsub.topic.v1.messagePublished'' with destination Cloud Run service ``my-service'', run:

          $ {command} my-trigger --matching-criteria="type=google.cloud.pubsub.topic.v1.messagePublished" --destination-run-service=my-service
        """,
}


class NoDestinationLocationSpecifiedError(exceptions.Error):
  """Error when no destination location was specified for a global trigger."""


class UnsupportedDestinationError(exceptions.Error):
  """Error when none of the supported destination args is specified."""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create an Eventarc trigger."""

  detailed_help = _DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    flags.AddCreateTrigerResourceArgs(parser, cls.ReleaseTrack())
    flags.AddEventFiltersArg(parser, cls.ReleaseTrack(), required=True)
    flags.AddEventFiltersPathPatternArg(parser, cls.ReleaseTrack())
    flags.AddEventDataContentTypeArg(parser, cls.ReleaseTrack())
    flags.AddServiceAccountArg(parser)
    flags.AddCreateDestinationArgs(parser, cls.ReleaseTrack(), required=True)
    flags.AddTransportTopicResourceArg(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run the create command."""
    client = triggers.CreateTriggersClient(self.ReleaseTrack())
    trigger_ref = args.CONCEPTS.trigger.Parse()
    channel_ref = flags.GetChannelArg(args, self.ReleaseTrack())
    transport_topic_ref = args.CONCEPTS.transport_topic.Parse()
    event_filters = flags.GetEventFiltersArg(args, self.ReleaseTrack())
    event_filters_path_pattern = flags.GetEventFiltersPathPatternArg(
        args, self.ReleaseTrack()
    )
    event_data_content_type = flags.GetEventDataContentTypeArg(
        args, self.ReleaseTrack()
    )

    destination_message = None
    # destination Cloud Run
    if args.IsSpecified('destination_run_service') or args.IsKnownAndSpecified(
        'destination_run_job'
    ):
      resource_type = (
          'service' if args.IsSpecified('destination_run_service') else 'job'
      )
      destination_run_region = self.GetDestinationLocation(
          args,
          trigger_ref,
          'destination_run_region',
          'Cloud Run {}'.format(resource_type),
      )

      # Jobs only exist in the v1 API and thus only in the GA track.
      # This extra check is needed so we don't throw trying to access a flag
      # which doesn't exist.
      run_job = (
          args.destination_run_job if 'destination_run_job' in args else None
      )
      destination_message = client.BuildCloudRunDestinationMessage(
          args.destination_run_service,
          run_job,
          args.destination_run_path,
          destination_run_region,
      )
      dest_str = 'Cloud Run {} [{}]'.format(
          resource_type, args.destination_run_service or run_job
      )
      loading_msg = ''
    # destination GKE service
    elif args.IsSpecified('destination_gke_service'):
      destination_gke_location = self.GetDestinationLocation(
          args, trigger_ref, 'destination_gke_location', 'GKE service'
      )
      destination_gke_namespace = args.destination_gke_namespace or 'default'

      destination_message = client.BuildGKEDestinationMessage(
          args.destination_gke_cluster,
          destination_gke_location,
          destination_gke_namespace,
          args.destination_gke_service,
          args.destination_gke_path,
      )
      dest_str = 'GKE service [{}] in cluster [{}]'.format(
          args.destination_gke_service, args.destination_gke_cluster
      )
      loading_msg = 'this operation may take several minutes'
    # destination Http Endpoint
    elif args.IsSpecified('destination_http_endpoint_uri'):
      destination_message = client.BuildHTTPEndpointDestinationMessage(
          args.destination_http_endpoint_uri,
          args.network_attachment,
      )
      dest_str = 'HTTP endpoint [{}]'.format(args.destination_http_endpoint_uri)
      loading_msg = 'this operation may take several minutes'
    # destination Workflow
    elif args.IsSpecified('destination_workflow'):
      destination_workflow_location = self.GetDestinationLocation(
          args, trigger_ref, 'destination_workflow_location', 'Workflow'
      )

      destination_message = client.BuildWorkflowDestinationMessage(
          trigger_ref.Parent().Parent().Name(),
          args.destination_workflow,
          destination_workflow_location,
      )
      dest_str = 'Workflow [{}]'.format(args.destination_workflow)
      loading_msg = ''
    # Destination Cloud Function
    elif args.IsSpecified('destination_function'):
      destination_function_location = self.GetDestinationLocation(
          args, trigger_ref, 'destination_function_location', 'Function'
      )
      destination_message = client.BuildFunctionDestinationMessage(
          trigger_ref.Parent().Parent().Name(),
          args.destination_function,
          destination_function_location,
      )
      dest_str = 'Cloud Function [{}]'.format(args.destination_function)
      loading_msg = ''
    else:
      raise UnsupportedDestinationError('Must specify a valid destination.')
    trigger_message = client.BuildTriggerMessage(
        trigger_ref,
        event_filters,
        event_filters_path_pattern,
        event_data_content_type,
        args.service_account,
        destination_message,
        transport_topic_ref,
        channel_ref,
    )
    operation = client.Create(trigger_ref, trigger_message)
    self._event_type = event_filters['type']
    if args.async_:
      return operation

    response = client.WaitFor(operation, 'Creating', trigger_ref, loading_msg)
    trigger_dict = encoding.MessageToPyValue(response)
    if types.IsPubsubType(self._event_type):
      topic = trigger_dict['transport']['pubsub']['topic']
      if args.IsSpecified('transport_topic'):
        log.status.Print('Publish to Pub/Sub topic [{}] to receive events '
                         'in {}.'.format(topic, dest_str))
      else:
        log.status.Print('Created Pub/Sub topic [{}].'.format(topic))
        log.status.Print(
            'Publish to this topic to receive events in {}.'.format(dest_str))
    return response

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed:
      log.warning(
          'It may take up to {} minutes for the new trigger to become active.'
          .format(triggers.MAX_ACTIVE_DELAY_MINUTES))

  def GetDestinationLocation(self, args, trigger_ref, location_arg_name,
                             destination_type):
    # If no Destination region was provided, use the trigger's location instead.
    if not args.IsSpecified(location_arg_name):
      destination_location = trigger_ref.Parent().Name()
      if destination_location == 'global':
        raise NoDestinationLocationSpecifiedError(
            'The `{}` flag is required when creating a global trigger with a '
            'destination {}.'.format(
                args.GetFlag(location_arg_name), destination_type))
    else:
      destination_location = args.GetValue(location_arg_name)

    return destination_location


@base.Deprecate(
    is_removed=False,
    warning=('This command is deprecated. '
             'Please use `gcloud eventarc triggers create` instead.'),
    error=('This command has been removed. '
           'Please use `gcloud eventarc triggers create` instead.')
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create an Eventarc trigger."""

  detailed_help = _DETAILED_HELP_BETA
