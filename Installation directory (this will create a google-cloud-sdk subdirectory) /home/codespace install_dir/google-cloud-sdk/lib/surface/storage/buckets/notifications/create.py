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
"""Implementation of create command for notifications."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import time

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as api_errors
from googlecloudsdk.api_lib.storage.gcs_json import error_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import notification_configuration_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@error_util.catch_http_error_raise_gcs_api_error()
def _maybe_create_or_modify_topic(topic_name, service_account_email):
  """Ensures that topic with SA permissions exists, creating it if needed.

  Args:
    topic_name (str): Name of the Cloud Pub/Sub topic to use or create.
    service_account_email (str): The project service account for Google Cloud
      Storage. This SA needs publish permission on the PubSub topic.

  Returns:
    True if topic was created or had its IAM permissions modified.
    Otherwise, False.
  """
  pubsub_client = apis.GetClientInstance('pubsub', 'v1')
  pubsub_messages = apis.GetMessagesModule('pubsub', 'v1')

  try:
    pubsub_client.projects_topics.Get(
        pubsub_messages.PubsubProjectsTopicsGetRequest(topic=topic_name))
    log.warning('Topic already exists: ' + topic_name)
    created_new_topic = False
  except apitools_exceptions.HttpError as e:
    if e.status_code != 404:
      # Expect an Apitools NotFound error. Raise error otherwise.
      raise
    new_topic = pubsub_client.projects_topics.Create(
        pubsub_messages.Topic(name=topic_name))
    log.info('Created topic:\n{}'.format(new_topic))
    created_new_topic = True

  # Verify that the service account is in the IAM policy.
  topic_iam_policy = pubsub_client.projects_topics.GetIamPolicy(
      pubsub_messages.PubsubProjectsTopicsGetIamPolicyRequest(
          resource=topic_name))
  expected_binding = pubsub_messages.Binding(
      role='roles/pubsub.publisher',
      members=['serviceAccount:' + service_account_email])

  # Can be improved by checking for roles stronger than "pubsub.publisher".
  # We could also recurse up the hierarchy, checking project-level permissions.
  # However, the caller may not have permission to perform this recursion.
  # The trade-off of complexity for the benefit of not granting a redundant,
  # permission is not worth it, so we grant "publisher" if a simple check fails.
  if expected_binding not in topic_iam_policy.bindings:
    topic_iam_policy.bindings.append(expected_binding)
    updated_topic_iam_policy = pubsub_client.projects_topics.SetIamPolicy(
        pubsub_messages.PubsubProjectsTopicsSetIamPolicyRequest(
            resource=topic_name,
            setIamPolicyRequest=pubsub_messages.SetIamPolicyRequest(
                policy=topic_iam_policy)))
    log.info('Updated topic IAM policy:\n{}'.format(updated_topic_iam_policy))
    return True
  else:
    log.warning(
        'Project service account {} already has publish permission for topic {}'
        .format(service_account_email, topic_name))
  return created_new_topic


class Create(base.Command):
  """Create a notification configuration on a bucket."""

  detailed_help = {
      'DESCRIPTION':
          """
      *{command}* creates a notification configuration on a bucket,
      establishing a flow of event notifications from Cloud Storage to a
      Cloud Pub/Sub topic. As part of creating this flow, it also verifies
      that the destination Cloud Pub/Sub topic exists, creating it if necessary,
      and verifies that the Cloud Storage bucket has permission to publish
      events to that topic, granting the permission if necessary.

      If a destination Cloud Pub/Sub topic is not specified with the `-t` flag,
      Cloud Storage chooses a topic name in the default project whose ID is
      the same as the bucket name. For example, if the default project ID
      specified is `default-project` and the bucket being configured is
      `gs://example-bucket`, the create command uses the Cloud Pub/Sub topic
      `projects/default-project/topics/example-bucket`.

      In order to enable notifications, your project's
      [Cloud Storage service agent](https://cloud.google.com/storage/docs/projects#service-accounts)
      must have the IAM permission "pubsub.topics.publish".
      This command checks to see if the destination Cloud Pub/Sub topic grants
      the service agent this permission. If not, the create command attempts to
      grant it.

      A bucket can have up to 100 total notification configurations and up to
      10 notification configurations set to trigger for a specific event.
      """,
      'EXAMPLES':
          """
      Send notifications of all changes to the bucket
      `example-bucket` to the Cloud Pub/Sub topic
      `projects/default-project/topics/example-bucket`:

        $ {command} gs://example-bucket

      The same as the above but sends no notification payload:

        $ {command} --payload-format=none gs://example-bucket

      Include custom metadata in notification payloads:

        $ {command} --custom-attributes=key1:value1,key2:value2 gs://example-bucket

      Create a notification configuration that only sends an event when a new
      object has been created or an object is deleted:

        $ {command} --event-types=OBJECT_FINALIZE,OBJECT_DELETE gs://example-bucket

      Create a topic and notification configuration that sends events only when
      they affect objects with the prefix `photos/`:

        $ {command} --object-prefix=photos/ gs://example-bucket

      Specifies the destination topic ID `files-to-process` in the default
      project:

        $ {command} --topic=files-to-process gs://example-bucket

      The same as above but specifies a Cloud Pub/Sub topic belonging
      to the specific cloud project `example-project`:

        $ {command} --topic=projects/example-project/topics/files-to-process gs://example-bucket

      Skip creating a topic when creating the notification configuraiton:

        $ {command} --skip-topic-setup gs://example-bucket
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'url',
        help='URL of the bucket to create the notification configuration'
        ' on.')
    parser.add_argument(
        '-m',
        '--custom-attributes',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        help='Specifies key:value attributes that are appended to the set of'
        ' attributes sent to Cloud Pub/Sub for all events associated with'
        ' this notification configuration.')
    parser.add_argument(
        '-e',
        '--event-types',
        metavar='NOTIFICATION_EVENT_TYPE',
        type=arg_parsers.ArgList(
            choices=sorted(
                [status.value for status in cloud_api.NotificationEventType])),
        help=(
            'Specify event type filters for this notification configuration.'
            ' Cloud Storage will send notifications of only these types. By'
            ' default, Cloud Storage sends notifications for all event types.'
            ' * OBJECT_FINALIZE: An object has been created.'
            ' * OBJECT_METADATA_UPDATE: The metadata of an object has changed.'
            ' * OBJECT_DELETE: An object has been permanently deleted.'
            ' * OBJECT_ARCHIVE: A live version of an object has become a'
            ' noncurrent version.'))
    parser.add_argument(
        '-p',
        '--object-prefix',
        help='Specifies a prefix path for this notification configuration.'
        ' Cloud Storage will send notifications for only objects in the'
        ' bucket whose names begin with the prefix.')
    parser.add_argument(
        '-f',
        '--payload-format',
        choices=sorted(
            [status.value for status in cloud_api.NotificationPayloadFormat]),
        default=cloud_api.NotificationPayloadFormat.JSON.value,
        help='Specifies the payload format of notification messages.'
        ' Notification details are available in the message attributes.'
        " 'none' sends no payload.")
    parser.add_argument(
        '-s',
        '--skip-topic-setup',
        action='store_true',
        help='Skips creation and permission assignment of the Cloud Pub/Sub'
        ' topic. This is useful if the caller does not have permission to'
        ' access the topic in question, or if the topic already exists and has'
        ' the appropriate publish permission assigned.')
    parser.add_argument(
        '-t',
        '--topic',
        help='Specifies the Cloud Pub/Sub topic to send notifications to.'
        ' If not specified, this command chooses a topic whose project is'
        ' your default project and whose ID is the same as the'
        ' Cloud Storage bucket name.')

  def Run(self, args):
    project_id = properties.VALUES.core.project.GetOrFail()
    url = storage_url.storage_url_from_string(args.url)
    notification_configuration_iterator.raise_error_if_not_gcs_bucket_matching_url(
        url)
    if not args.topic:
      topic_name = 'projects/{}/topics/{}'.format(project_id, url.bucket_name)
    elif not args.topic.startswith('projects/'):
      # A topic ID may be present but not a whole path. Use the default project.
      topic_name = 'projects/{}/topics/{}'.format(
          project_id,
          args.topic.rpartition('/')[-1])
    else:
      topic_name = args.topic

    # Notifications supported for only GCS.
    gcs_client = api_factory.get_api(storage_url.ProviderPrefix.GCS)
    if not args.skip_topic_setup:
      # Using generated topic name instead of custom one.
      # Project number is different than project ID.
      bucket_project_number = gcs_client.get_bucket(
          url.bucket_name).metadata.projectNumber
      # Fetch the email of the service account that will need access to
      # the new pubsub topic.
      service_account_email = gcs_client.get_service_agent(
          project_number=bucket_project_number)
      log.info(
          'Checking for topic {} with access for project {} service account {}.'
          .format(topic_name, project_id, service_account_email))
      created_new_topic_or_set_new_permissions = _maybe_create_or_modify_topic(
          topic_name, service_account_email)
    else:
      created_new_topic_or_set_new_permissions = False

    if args.event_types:
      event_types = [
          cloud_api.NotificationEventType(event_type)
          for event_type in args.event_types
      ]
    else:
      event_types = None
    create_notification_configuration = functools.partial(
        gcs_client.create_notification_configuration,
        url,
        topic_name,
        custom_attributes=args.custom_attributes,
        event_types=event_types,
        object_name_prefix=args.object_prefix,
        payload_format=cloud_api.NotificationPayloadFormat(args.payload_format))
    try:
      return create_notification_configuration()
    except api_errors.CloudApiError:
      if not created_new_topic_or_set_new_permissions:
        raise
      log.warning(
          'Retrying create notification request because topic changes may'
          ' take up to 10 seconds to process.')
      time.sleep(10)
      return create_notification_configuration()
