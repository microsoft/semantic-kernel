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
"""'functions deploy' utilities for triggers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import exceptions
from googlecloudsdk.api_lib.functions.v1 import triggers
from googlecloudsdk.api_lib.functions.v1 import util as api_util
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class TriggerCompatibilityError(core_exceptions.Error):
  """Raised when deploy trigger is incompatible with existing trigger."""


GCS_COMPATIBILITY_ERROR = (
    'The `--trigger-bucket` flag corresponds to the '
    '`google.storage.object.finalize` event on file creation.  '
    'You are trying to update a function that is using the legacy '
    '`providers/cloud.storage/eventTypes/object.change` event type. To get the '
    'legacy behavior, use the `--trigger-event` and `--trigger-resource` flags '
    'e.g. `gcloud functions deploy --trigger-event '
    'providers/cloud.storage/eventTypes/object.change '
    '--trigger-resource [your_bucket_name]`.'
    'Please see https://cloud.google.com/storage/docs/pubsub-notifications for '
    'more information on storage event types.'
)

PUBSUB_COMPATIBILITY_ERROR = (
    'The format of the Pub/Sub event source has changed.  You are trying to '
    'update a function that is using the legacy '
    '`providers/cloud.pubsub/eventTypes/topic.publish` event type. To get the '
    'legacy behavior, use the `--trigger-event` and `--trigger-resource` flags '
    'e.g. `gcloud functions deploy --trigger-event '
    'providers/cloud.pubsub/eventTypes/topic.publish '
    '--trigger-resource [your_topic_name]`.'
)

# Old style trigger events as of 02/2018.
LEGACY_TRIGGER_EVENTS = {
    'providers/cloud.storage/eventTypes/object.change': GCS_COMPATIBILITY_ERROR,
    'providers/cloud.pubsub/eventTypes/topic.publish': (
        PUBSUB_COMPATIBILITY_ERROR
    ),
}


def CheckTriggerSpecified(args):
  if not (
      args.IsSpecified('trigger_topic')
      or args.IsSpecified('trigger_bucket')
      or args.IsSpecified('trigger_http')
      or args.IsSpecified('trigger_event')
  ):
    raise calliope_exceptions.OneOfArgumentsRequiredException(
        [
            '--trigger-topic',
            '--trigger-bucket',
            '--trigger-http',
            '--trigger-event',
        ],
        'You must specify a trigger when deploying a new function.',
    )


def ValidateTriggerArgs(
    trigger_event, trigger_resource, retry_specified, trigger_http_specified
):
  """Check if args related function triggers are valid.

  Args:
    trigger_event: The trigger event
    trigger_resource: The trigger resource
    retry_specified: Whether or not `--retry` was specified
    trigger_http_specified: Whether or not `--trigger-http` was specified

  Raises:
    FunctionsError.
  """
  # Check that Event Type is valid
  trigger_provider = triggers.TRIGGER_PROVIDER_REGISTRY.ProviderForEvent(
      trigger_event
  )
  trigger_provider_label = trigger_provider.label
  if trigger_provider_label != triggers.UNADVERTISED_PROVIDER_LABEL:
    resource_type = triggers.TRIGGER_PROVIDER_REGISTRY.Event(
        trigger_provider_label, trigger_event
    ).resource_type
    if trigger_resource is None and resource_type != triggers.Resources.PROJECT:
      raise exceptions.FunctionsError(
          'You must provide --trigger-resource when using '
          '--trigger-event={}'.format(trigger_event)
      )
  if retry_specified and trigger_http_specified:
    raise calliope_exceptions.ConflictingArgumentsException(
        '--trigger-http', '--retry'
    )


def _GetBucketTriggerEventParams(trigger_bucket):
  bucket_name = trigger_bucket[5:-1]
  return {
      'trigger_provider': 'cloud.storage',
      'trigger_event': 'google.storage.object.finalize',
      'trigger_resource': bucket_name,
  }


def _GetTopicTriggerEventParams(trigger_topic):
  return {
      'trigger_provider': 'cloud.pubsub',
      'trigger_event': 'google.pubsub.topic.publish',
      'trigger_resource': trigger_topic,
  }


def _GetEventTriggerEventParams(trigger_event, trigger_resource):
  """Get the args for creating an event trigger.

  Args:
    trigger_event: The trigger event
    trigger_resource: The trigger resource

  Returns:
    A dictionary containing trigger_provider, trigger_event, and
    trigger_resource.
  """
  trigger_provider = triggers.TRIGGER_PROVIDER_REGISTRY.ProviderForEvent(
      trigger_event
  )

  trigger_provider_label = trigger_provider.label
  result = {
      'trigger_provider': trigger_provider_label,
      'trigger_event': trigger_event,
      'trigger_resource': trigger_resource,
  }
  if trigger_provider_label == triggers.UNADVERTISED_PROVIDER_LABEL:
    return result

  resource_type = triggers.TRIGGER_PROVIDER_REGISTRY.Event(
      trigger_provider_label, trigger_event
  ).resource_type
  if resource_type == triggers.Resources.TOPIC:
    trigger_resource = api_util.ValidatePubsubTopicNameOrRaise(trigger_resource)
  elif resource_type == triggers.Resources.BUCKET:
    trigger_resource = storage_util.BucketReference.FromUrl(
        trigger_resource
    ).bucket
  elif resource_type in [
      triggers.Resources.FIREBASE_ANALYTICS_EVENT,
      triggers.Resources.FIREBASE_DB,
      triggers.Resources.FIRESTORE_DOC,
  ]:
    pass
  elif resource_type == triggers.Resources.PROJECT:
    if trigger_resource:
      properties.VALUES.core.project.Validate(trigger_resource)
  else:
    # Check if programmer allowed other methods in
    # api_util.PROVIDER_EVENT_RESOURCE but forgot to update code here
    raise core_exceptions.InternalError()
  # checked if provided resource and path have correct format
  result['trigger_resource'] = trigger_resource
  return result


def GetTriggerEventParams(
    trigger_http, trigger_bucket, trigger_topic, trigger_event, trigger_resource
):
  """Check --trigger-*  arguments and deduce if possible.

  0. if --trigger-http is return None.
  1. if --trigger-bucket return bucket trigger args (_GetBucketTriggerArgs)
  2. if --trigger-topic return pub-sub trigger args (_GetTopicTriggerArgs)
  3. if --trigger-event, deduce provider and resource from registry and return

  Args:
    trigger_http: The trigger http
    trigger_bucket: The trigger bucket
    trigger_topic: The trigger topic
    trigger_event: The trigger event
    trigger_resource: The trigger resource

  Returns:
    None, when using HTTPS trigger. Otherwise a dictionary containing
    trigger_provider, trigger_event, and trigger_resource.
  """
  if trigger_http:
    return None
  if trigger_bucket:
    return _GetBucketTriggerEventParams(trigger_bucket)
  if trigger_topic:
    return _GetTopicTriggerEventParams(trigger_topic)
  if trigger_event:
    return _GetEventTriggerEventParams(trigger_event, trigger_resource)
  elif trigger_resource:
    log.warning(
        'Ignoring the flag --trigger-resource. The flag --trigger-resource is '
        'provided but --trigger-event is not. If you intend to change '
        'trigger-resource you need to provide trigger-event as well.'
    )


def ConvertTriggerArgsToRelativeName(
    trigger_provider, trigger_event, trigger_resource
):
  """Prepares resource field for Function EventTrigger to use in API call.

  API uses relative resource name in EventTrigger message field. The
  structure of that identifier depends on the resource type which depends on
  combination of --trigger-provider and --trigger-event arguments' values.
  This function chooses the appropriate form, fills it with required data and
  returns as a string.

  Args:
    trigger_provider: The --trigger-provider flag value.
    trigger_event: The --trigger-event flag value.
    trigger_resource: The --trigger-resource flag value.

  Returns:
    Relative resource name to use in EventTrigger field.
  """
  resource_type = triggers.TRIGGER_PROVIDER_REGISTRY.Event(
      trigger_provider, trigger_event
  ).resource_type
  params = {}
  if resource_type.value.collection_id in {
      'google.firebase.analytics.event',
      'google.firebase.database.ref',
      'google.firestore.document',
  }:
    return trigger_resource
  elif resource_type.value.collection_id == 'cloudresourcemanager.projects':
    params['projectId'] = properties.VALUES.core.project.GetOrFail
  elif resource_type.value.collection_id == 'pubsub.projects.topics':
    params['projectsId'] = properties.VALUES.core.project.GetOrFail
  elif resource_type.value.collection_id == 'cloudfunctions.projects.buckets':
    pass

  ref = resources.REGISTRY.Parse(
      trigger_resource,
      params,
      collection=resource_type.value.collection_id,
  )
  return ref.RelativeName()


def CreateEventTrigger(trigger_provider, trigger_event, trigger_resource):
  """Create event trigger message.

  Args:
    trigger_provider: str, trigger provider label.
    trigger_event: str, trigger event label.
    trigger_resource: str, trigger resource name.

  Returns:
    A EventTrigger protobuf message.
  """
  messages = api_util.GetApiMessagesModule()
  event_trigger = messages.EventTrigger()
  event_trigger.eventType = trigger_event
  if trigger_provider == triggers.UNADVERTISED_PROVIDER_LABEL:
    event_trigger.resource = trigger_resource
  else:
    event_trigger.resource = ConvertTriggerArgsToRelativeName(
        trigger_provider, trigger_event, trigger_resource
    )
  return event_trigger


def CheckLegacyTriggerUpdate(function_trigger, new_trigger_event):
  if function_trigger:
    function_event_type = function_trigger.eventType
    if (
        function_event_type in LEGACY_TRIGGER_EVENTS
        and function_event_type != new_trigger_event
    ):
      error = LEGACY_TRIGGER_EVENTS[function_event_type]
      raise TriggerCompatibilityError(error)
