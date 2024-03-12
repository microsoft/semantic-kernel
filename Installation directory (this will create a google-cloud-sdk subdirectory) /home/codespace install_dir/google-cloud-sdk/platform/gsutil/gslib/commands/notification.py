# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module provides the notification command to gsutil."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import getopt
import re
import time
import uuid
from datetime import datetime

from gslib import metrics
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import PublishPermissionDeniedException
from gslib.command import Command
from gslib.command import NO_MAX
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.help_provider import CreateHelpText
from gslib.project_id import PopulateProjectId
from gslib.pubsub_api import PubsubApi
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.pubsub_apitools.pubsub_v1_messages import Binding
from gslib.utils import copy_helper
from gslib.utils import shim_util
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap

# Cloud Pub/Sub commands

_LIST_SYNOPSIS = """
  gsutil notification list gs://<bucket_name>...
"""

_DELETE_SYNOPSIS = """
  gsutil notification delete (<notificationConfigName>|gs://<bucket_name>)...
"""

_CREATE_SYNOPSIS = """
  gsutil notification create -f (json|none) [-p <prefix>] [-t <topic>] \\
      [-m <key>:<value>]... [-e <eventType>]... gs://<bucket_name>
"""

# Object Change Notification commands

_WATCHBUCKET_SYNOPSIS = """
  gsutil notification watchbucket [-i <id>] [-t <token>] <app_url> gs://<bucket_name>
"""

_STOPCHANNEL_SYNOPSIS = """
  gsutil notification stopchannel <channel_id> <resource_id>
"""

_SYNOPSIS = (
    _CREATE_SYNOPSIS +
    _DELETE_SYNOPSIS.lstrip('\n') +
    _LIST_SYNOPSIS.lstrip('\n') +
    _WATCHBUCKET_SYNOPSIS +
    _STOPCHANNEL_SYNOPSIS.lstrip('\n') + '\n')  # yapf: disable

_LIST_DESCRIPTION = """
<B>LIST</B>
  The list sub-command provides a list of notification configs belonging to a
  given bucket. The listed name of each notification config can be used with
  the delete sub-command to delete that specific notification config.

  For listing Object Change Notifications instead of Cloud Pub/Sub notification
  subscription configs, add a -o flag.

<B>LIST EXAMPLES</B>
  Fetch the list of notification configs for the bucket example-bucket:

    gsutil notification list gs://example-bucket

  The same as above, but for Object Change Notifications instead of Cloud
  Pub/Sub notification subscription configs:

    gsutil notification list -o gs://example-bucket

  Fetch the notification configs in all buckets matching a wildcard:

    gsutil notification list gs://example-*

  Fetch all of the notification configs for buckets in the default project:

    gsutil notification list gs://*
"""

_DELETE_DESCRIPTION = """
<B>DELETE</B>
  The delete sub-command deletes notification configs from a bucket. If a
  notification config name is passed as a parameter, that notification config
  alone is deleted. If a bucket name is passed, all notification configs
  associated with that bucket are deleted.

  Cloud Pub/Sub topics associated with this notification config are not
  deleted by this command. Those must be deleted separately, for example with
  the gcloud command `gcloud beta pubsub topics delete`.

  Object Change Notification subscriptions cannot be deleted with this command.
  For that, see the command `gsutil notification stopchannel`.

<B>DELETE EXAMPLES</B>
  Delete a single notification config (with ID 3) in the bucket example-bucket:

    gsutil notification delete projects/_/buckets/example-bucket/notificationConfigs/3

  Delete all notification configs in the bucket example-bucket:

    gsutil notification delete gs://example-bucket
"""

_CREATE_DESCRIPTION = """
<B>CREATE</B>
  The create sub-command creates a notification config on a bucket, establishing
  a flow of event notifications from Cloud Storage to a Cloud Pub/Sub topic. As
  part of creating this flow, the create command also verifies that the
  destination Cloud Pub/Sub topic exists, creating it if necessary, and verifies
  that the Cloud Storage bucket has permission to publish events to that topic,
  granting the permission if necessary.

  If a destination Cloud Pub/Sub topic is not specified with the -t flag, Cloud
  Storage chooses a topic name in the default project whose ID is the same as
  the bucket name. For example, if the default project ID specified is
  'default-project' and the bucket being configured is gs://example-bucket, the
  create command uses the Cloud Pub/Sub topic
  "projects/default-project/topics/example-bucket".

  In order to enable notifications, your project's `Cloud Storage service agent
  <https://cloud.google.com/storage/docs/projects#service-accounts>`_ must have
  the IAM permission "pubsub.topics.publish". This command checks to see if the
  destination Cloud Pub/Sub topic grants the service agent this permission. If
  not, the create command attempts to grant it.

  A bucket can have up to 100 total notification configurations and up to 10
  notification configurations set to trigger for a specific event.

<B>CREATE EXAMPLES</B>
  Begin sending notifications of all changes to the bucket example-bucket
  to the Cloud Pub/Sub topic projects/default-project/topics/example-bucket:

    gsutil notification create -f json gs://example-bucket

  The same as above, but specifies the destination topic ID 'files-to-process'
  in the default project:

    gsutil notification create -f json \\
      -t files-to-process gs://example-bucket

  The same as above, but specifies a Cloud Pub/Sub topic belonging to the
  specific cloud project 'example-project':

    gsutil notification create -f json \\
      -t projects/example-project/topics/files-to-process gs://example-bucket

  Create a notification config that only sends an event when a new object
  has been created:

    gsutil notification create -f json -e OBJECT_FINALIZE gs://example-bucket

  Create a topic and notification config that only sends an event when
  an object beginning with "photos/" is affected:

    gsutil notification create -p photos/ gs://example-bucket

  List all of the notificationConfigs in bucket example-bucket:

    gsutil notification list gs://example-bucket

  Delete all notitificationConfigs for bucket example-bucket:

    gsutil notification delete gs://example-bucket

  Delete one specific notificationConfig for bucket example-bucket:

    gsutil notification delete \\
      projects/_/buckets/example-bucket/notificationConfigs/1

<B>OPTIONS</B>
  The create sub-command has the following options

  -e        Specify an event type filter for this notification config. Cloud
            Storage only sends notifications of this type. You may specify this
            parameter multiple times to allow multiple event types. If not
            specified, Cloud Storage sends notifications for all event types.
            The valid types are:

              OBJECT_FINALIZE - An object has been created.
              OBJECT_METADATA_UPDATE - The metadata of an object has changed.
              OBJECT_DELETE - An object has been permanently deleted.
              OBJECT_ARCHIVE - A live version of an object has become a
                noncurrent version.

  -f        Specifies the payload format of notification messages. Must be
            either "json" for a payload matches the object metadata for the
            JSON API, or "none" to specify no payload at all. In either case,
            notification details are available in the message attributes.

  -m        Specifies a key:value attribute that is appended to the set
            of attributes sent to Cloud Pub/Sub for all events associated with
            this notification config. You may specify this parameter multiple
            times to set multiple attributes.

  -p        Specifies a prefix path filter for this notification config. Cloud
            Storage only sends notifications for objects in this bucket whose
            names begin with the specified prefix.

  -s        Skips creation and permission assignment of the Cloud Pub/Sub topic.
            This is useful if the caller does not have permission to access
            the topic in question, or if the topic already exists and has the
            appropriate publish permission assigned.

  -t        The Cloud Pub/Sub topic to which notifications should be sent. If
            not specified, this command chooses a topic whose project is your
            default project and whose ID is the same as the Cloud Storage bucket
            name.

<B>NEXT STEPS</B>
  Once the create command has succeeded, Cloud Storage publishes a message to
  the specified Cloud Pub/Sub topic when eligible changes occur. In order to
  receive these messages, you must create a Pub/Sub subscription for your
  Pub/Sub topic. To learn more about creating Pub/Sub subscriptions, see `the
  Pub/Sub Subscriber Overview <https://cloud.google.com/pubsub/docs/subscriber>`_.

  You can create a simple Pub/Sub subscription using the ``gcloud`` command-line
  tool. For example, to create a new subscription on the topic "myNewTopic" and
  attempt to pull messages from it, you could run:

    gcloud beta pubsub subscriptions create --topic myNewTopic testSubscription
    gcloud beta pubsub subscriptions pull --auto-ack testSubscription
"""

_WATCHBUCKET_DESCRIPTION = """
<B>WATCHBUCKET</B>
  The watchbucket sub-command can be used to watch a bucket for object changes.
  A service account must be used when running this command.

  The app_url parameter must be an HTTPS URL to an application that will be
  notified of changes to any object in the bucket.

  The optional id parameter can be used to assign a unique identifier to the
  created notification channel. If not provided, a random UUID string is
  generated.

  The optional token parameter can be used to validate notifications events.
  To do this, set this custom token and store it to later verify that
  notification events contain the client token you expect.

<B>WATCHBUCKET EXAMPLES</B>
  Watch the bucket example-bucket for changes and send notifications to an
  application server running at example.com:

    gsutil notification watchbucket https://example.com/notify \\
      gs://example-bucket

  Assign identifier my-channel-id to the created notification channel:

    gsutil notification watchbucket -i my-channel-id \\
      https://example.com/notify gs://example-bucket

  Set a custom client token that is included with each notification event:

    gsutil notification watchbucket -t my-client-token \\
      https://example.com/notify gs://example-bucket
"""

_STOPCHANNEL_DESCRIPTION = """
<B>STOPCHANNEL</B>
  The stopchannel sub-command can be used to stop sending change events to a
  notification channel.

  The channel_id and resource_id parameters should match the values from the
  response of a bucket watch request.

<B>STOPCHANNEL EXAMPLES</B>
  Stop the notification event channel with channel identifier channel1 and
  resource identifier SoGqan08XDIFWr1Fv_nGpRJBHh8:

    gsutil notification stopchannel channel1 SoGqan08XDIFWr1Fv_nGpRJBHh8
"""

_DESCRIPTION = """
  You can use the ``notification`` command to configure
  `Pub/Sub notifications for Cloud Storage
  <https://cloud.google.com/storage/docs/pubsub-notifications>`_
  and `Object change notification
  <https://cloud.google.com/storage/docs/object-change-notification>`_ channels.

<B>CLOUD PUB/SUB</B>
  The "create", "list", and "delete" sub-commands deal with configuring Cloud
  Storage integration with Google Cloud Pub/Sub.
""" + _CREATE_DESCRIPTION + _LIST_DESCRIPTION + _DELETE_DESCRIPTION + """
<B>OBJECT CHANGE NOTIFICATIONS</B>
  Object change notification is a separate, older feature within Cloud Storage
  for generating notifications. This feature sends HTTPS messages to a client
  application that you've set up separately. This feature is generally not
  recommended, because Pub/Sub notifications are cheaper, easier to use, and
  more flexible. For more information, see
  `Object change notification
  <https://cloud.google.com/storage/docs/object-change-notification>`_.

  The "watchbucket" and "stopchannel" sub-commands enable and disable Object
  change notifications.
""" + _WATCHBUCKET_DESCRIPTION + _STOPCHANNEL_DESCRIPTION + """
<B>NOTIFICATIONS AND PARALLEL COMPOSITE UPLOADS</B>
  gsutil supports `parallel composite uploads
  <https://cloud.google.com/storage/docs/uploads-downloads#parallel-composite-uploads>`_.
  If enabled, an upload can result in multiple temporary component objects
  being uploaded before the actual intended object is created. Any subscriber
  to notifications for this bucket then sees a notification for each of these
  components being created and deleted. If this is a concern for you, note
  that parallel composite uploads can be disabled by setting
  "parallel_composite_upload_threshold = 0" in your .boto config file.
  Alternately, your subscriber code can filter out gsutil's parallel
  composite uploads by ignoring any notification about objects whose names
  contain (but do not start with) the following string:
    "{composite_namespace}".

""".format(composite_namespace=copy_helper.PARALLEL_UPLOAD_TEMP_NAMESPACE)

NOTIFICATION_AUTHORIZATION_FAILED_MESSAGE = """
Watch bucket attempt failed:
  {watch_error}

You attempted to watch a bucket with an application URL of:

  {watch_url}

which is not authorized for your project. Please ensure that you are using
Service Account authentication and that the Service Account's project is
authorized for the application URL. Notification endpoint URLs must also be
whitelisted in your Cloud Console project. To do that, the domain must also be
verified using Google Webmaster Tools. For instructions, please see
`Notification Authorization
<https://cloud.google.com/storage/docs/object-change-notification#_Authorization>`_.
"""

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

# yapf: disable
_create_help_text = (
    CreateHelpText(_CREATE_SYNOPSIS, _CREATE_DESCRIPTION))
_list_help_text = (
    CreateHelpText(_LIST_SYNOPSIS, _LIST_DESCRIPTION))
_delete_help_text = (
    CreateHelpText(_DELETE_SYNOPSIS, _DELETE_DESCRIPTION))
_watchbucket_help_text = (
    CreateHelpText(_WATCHBUCKET_SYNOPSIS, _WATCHBUCKET_DESCRIPTION))
_stopchannel_help_text = (
    CreateHelpText(_STOPCHANNEL_SYNOPSIS, _STOPCHANNEL_DESCRIPTION))
# yapf: enable

PAYLOAD_FORMAT_MAP = {
    'none': 'NONE',
    'json': 'JSON_API_V1',
}


class NotificationCommand(Command):
  """Implementation of gsutil notification command."""

  # Notification names might look like one of these:
  #  canonical form:  projects/_/buckets/bucket/notificationConfigs/3
  #  JSON API form:   b/bucket/notificationConfigs/5
  # Either of the above might start with a / if a user is copying & pasting.
  def _GetNotificationPathRegex(self):
    if not NotificationCommand._notification_path_regex:
      NotificationCommand._notification_path_regex = re.compile(
          ('/?(projects/[^/]+/)?b(uckets)?/(?P<bucket>[^/]+)/'
           'notificationConfigs/(?P<notification>[0-9]+)'))
    return NotificationCommand._notification_path_regex

  _notification_path_regex = None

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'notification',
      command_name_aliases=[
          'notify',
          'notifyconfig',
          'notifications',
          'notif',
      ],
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='i:t:m:t:of:e:p:s',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'watchbucket': [
              CommandArgument.MakeFreeTextArgument(),
              CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
          ],
          'stopchannel': [],
          'list': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),],
          'delete': [
              # Takes a list of one of the following:
              #   notification: projects/_/buckets/bla/notificationConfigs/5,
              #   bucket: gs://foobar
              CommandArgument.MakeZeroOrMoreCloudURLsArgument(),
          ],
          'create': [
              CommandArgument.MakeFreeTextArgument(),  # Cloud Pub/Sub topic
              CommandArgument.MakeNCloudBucketURLsArgument(1),
          ]
      },
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='notification',
      help_name_aliases=[
          'watchbucket',
          'stopchannel',
          'notifyconfig',
      ],
      help_type='command_help',
      help_one_line_summary='Configure object change notification',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'create': _create_help_text,
          'list': _list_help_text,
          'delete': _delete_help_text,
          'watchbucket': _watchbucket_help_text,
          'stopchannel': _stopchannel_help_text,
      },
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command={
          'create':
              GcloudStorageMap(
                  gcloud_command=[
                      'storage', 'buckets', 'notifications', 'create'
                  ],
                  flag_map={
                      '-m':
                          GcloudStorageFlag(
                              '--custom-attributes',
                              repeat_type=shim_util.RepeatFlagType.DICT),
                      '-e':
                          GcloudStorageFlag(
                              '--event-types',
                              repeat_type=shim_util.RepeatFlagType.LIST),
                      '-p':
                          GcloudStorageFlag('--object-prefix'),
                      '-f':
                          GcloudStorageFlag('--payload-format'),
                      '-s':
                          GcloudStorageFlag('--skip-topic-setup'),
                      '-t':
                          GcloudStorageFlag('--topic'),
                  },
              ),
          'delete':
              GcloudStorageMap(
                  gcloud_command=[
                      'storage', 'buckets', 'notifications', 'delete'
                  ],
                  flag_map={},
              ),
          'list':
              GcloudStorageMap(
                  gcloud_command=[
                      'storage',
                      'buckets',
                      'notifications',
                      'list',
                      '--human-readable',
                  ],
                  flag_map={},
                  supports_output_translation=True,
              ),
      },
      flag_map={},
  )

  def _WatchBucket(self):
    """Creates a watch on a bucket given in self.args."""
    self.CheckArguments()
    identifier = None
    client_token = None
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-i':
          identifier = a
        if o == '-t':
          client_token = a

    identifier = identifier or str(uuid.uuid4())
    watch_url = self.args[0]
    bucket_arg = self.args[-1]

    if not watch_url.lower().startswith('https://'):
      raise CommandException('The application URL must be an https:// URL.')

    bucket_url = StorageUrlFromString(bucket_arg)
    if not (bucket_url.IsBucket() and bucket_url.scheme == 'gs'):
      raise CommandException(
          'The %s command can only be used with gs:// bucket URLs.' %
          self.command_name)
    if not bucket_url.IsBucket():
      raise CommandException('URL must name a bucket for the %s command.' %
                             self.command_name)

    self.logger.info('Watching bucket %s with application URL %s ...',
                     bucket_url, watch_url)

    try:
      channel = self.gsutil_api.WatchBucket(bucket_url.bucket_name,
                                            watch_url,
                                            identifier,
                                            token=client_token,
                                            provider=bucket_url.scheme)
    except AccessDeniedException as e:
      self.logger.warn(
          NOTIFICATION_AUTHORIZATION_FAILED_MESSAGE.format(watch_error=str(e),
                                                           watch_url=watch_url))
      raise

    channel_id = channel.id
    resource_id = channel.resourceId
    client_token = channel.token
    self.logger.info('Successfully created watch notification channel.')
    self.logger.info('Watch channel identifier: %s', channel_id)
    self.logger.info('Canonicalized resource identifier: %s', resource_id)
    self.logger.info('Client state token: %s', client_token)

    return 0

  def _StopChannel(self):
    channel_id = self.args[0]
    resource_id = self.args[1]

    self.logger.info('Removing channel %s with resource identifier %s ...',
                     channel_id, resource_id)
    self.gsutil_api.StopChannel(channel_id, resource_id, provider='gs')
    self.logger.info('Succesfully removed channel.')

    return 0

  def _ListChannels(self, bucket_arg):
    """Lists active channel watches on a bucket given in self.args."""
    bucket_url = StorageUrlFromString(bucket_arg)
    if not (bucket_url.IsBucket() and bucket_url.scheme == 'gs'):
      raise CommandException(
          'The %s command can only be used with gs:// bucket URLs.' %
          self.command_name)
    if not bucket_url.IsBucket():
      raise CommandException('URL must name a bucket for the %s command.' %
                             self.command_name)
    channels = self.gsutil_api.ListChannels(bucket_url.bucket_name,
                                            provider='gs').items
    self.logger.info(
        'Bucket %s has the following active Object Change Notifications:',
        bucket_url.bucket_name)
    for idx, channel in enumerate(channels):
      self.logger.info('\tNotification channel %d:', idx + 1)
      self.logger.info('\t\tChannel identifier: %s', channel.channel_id)
      self.logger.info('\t\tResource identifier: %s', channel.resource_id)
      self.logger.info('\t\tApplication URL: %s', channel.push_url)
      self.logger.info('\t\tCreated by: %s', channel.subscriber_email)
      self.logger.info(
          '\t\tCreation time: %s',
          str(datetime.fromtimestamp(channel.creation_time_ms / 1000)))

    return 0

  def _Create(self):
    self.CheckArguments()

    # User-specified options
    pubsub_topic = None
    payload_format = None
    custom_attributes = {}
    event_types = []
    object_name_prefix = None
    should_setup_topic = True

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-e':
          event_types.append(a)
        elif o == '-f':
          payload_format = a
        elif o == '-m':
          if ':' not in a:
            raise CommandException(
                'Custom attributes specified with -m should be of the form '
                'key:value')
          key, value = a.split(':', 1)
          custom_attributes[key] = value
        elif o == '-p':
          object_name_prefix = a
        elif o == '-s':
          should_setup_topic = False
        elif o == '-t':
          pubsub_topic = a

    if payload_format not in PAYLOAD_FORMAT_MAP:
      raise CommandException(
          "Must provide a payload format with -f of either 'json' or 'none'")
    payload_format = PAYLOAD_FORMAT_MAP[payload_format]

    bucket_arg = self.args[-1]

    bucket_url = StorageUrlFromString(bucket_arg)
    if not bucket_url.IsCloudUrl() or not bucket_url.IsBucket():
      raise CommandException(
          "%s %s requires a GCS bucket name, but got '%s'" %
          (self.command_name, self.subcommand_name, bucket_arg))
    if bucket_url.scheme != 'gs':
      raise CommandException(
          'The %s command can only be used with gs:// bucket URLs.' %
          self.command_name)
    bucket_name = bucket_url.bucket_name
    self.logger.debug('Creating notification for bucket %s', bucket_url)

    # Find the project this bucket belongs to
    bucket_metadata = self.gsutil_api.GetBucket(bucket_name,
                                                fields=['projectNumber'],
                                                provider=bucket_url.scheme)
    bucket_project_number = bucket_metadata.projectNumber

    # If not specified, choose a sensible default for the Cloud Pub/Sub topic
    # name.
    if not pubsub_topic:
      pubsub_topic = 'projects/%s/topics/%s' % (PopulateProjectId(None),
                                                bucket_name)
    if not pubsub_topic.startswith('projects/'):
      # If a user picks a topic ID (mytopic) but doesn't pass the whole name (
      # projects/my-project/topics/mytopic ), pick a default project.
      pubsub_topic = 'projects/%s/topics/%s' % (PopulateProjectId(None),
                                                pubsub_topic)
    self.logger.debug('Using Cloud Pub/Sub topic %s', pubsub_topic)

    just_modified_topic_permissions = False
    if should_setup_topic:
      # Ask GCS for the email address that represents GCS's permission to
      # publish to a Cloud Pub/Sub topic from this project.
      service_account = self.gsutil_api.GetProjectServiceAccount(
          bucket_project_number, provider=bucket_url.scheme).email_address
      self.logger.debug('Service account for project %d: %s',
                        bucket_project_number, service_account)
      just_modified_topic_permissions = self._CreateTopic(
          pubsub_topic, service_account)

    for attempt_number in range(0, 2):
      try:
        create_response = self.gsutil_api.CreateNotificationConfig(
            bucket_name,
            pubsub_topic=pubsub_topic,
            payload_format=payload_format,
            custom_attributes=custom_attributes,
            event_types=event_types if event_types else None,
            object_name_prefix=object_name_prefix,
            provider=bucket_url.scheme)
        break
      except PublishPermissionDeniedException:
        if attempt_number == 0 and just_modified_topic_permissions:
          # If we have just set the IAM policy, it may take up to 10 seconds to
          # take effect.
          self.logger.info(
              'Retrying create notification in 10 seconds '
              '(new permissions may take up to 10 seconds to take effect.)')
          time.sleep(10)
        else:
          raise

    notification_name = 'projects/_/buckets/%s/notificationConfigs/%s' % (
        bucket_name, create_response.id)
    self.logger.info('Created notification config %s', notification_name)

    return 0

  def _CreateTopic(self, pubsub_topic, service_account):
    """Assures that a topic exists, creating it if necessary.

    Also adds GCS as a publisher on that bucket, if necessary.

    Args:
      pubsub_topic: name of the Cloud Pub/Sub topic to use/create.
      service_account: the GCS service account that needs publish permission.

    Returns:
      true if we modified IAM permissions, otherwise false.
    """

    pubsub_api = PubsubApi(logger=self.logger)

    # Verify that the Pub/Sub topic exists. If it does not, create it.
    try:
      pubsub_api.GetTopic(topic_name=pubsub_topic)
      self.logger.debug('Topic %s already exists', pubsub_topic)
    except NotFoundException:
      self.logger.debug('Creating topic %s', pubsub_topic)
      pubsub_api.CreateTopic(topic_name=pubsub_topic)
      self.logger.info('Created Cloud Pub/Sub topic %s', pubsub_topic)

    # Verify that the service account is in the IAM policy.
    policy = pubsub_api.GetTopicIamPolicy(topic_name=pubsub_topic)
    binding = Binding(role='roles/pubsub.publisher',
                      members=['serviceAccount:%s' % service_account])

    # This could be more extensive. We could, for instance, check for roles
    # that are stronger that pubsub.publisher, like owner. We could also
    # recurse up the hierarchy looking to see if there are project-level
    # permissions. This can get very complex very quickly, as the caller
    # may not necessarily have access to the project-level IAM policy.
    # There's no danger in double-granting permission just to make sure it's
    # there, though.
    if binding not in policy.bindings:
      policy.bindings.append(binding)
      # transactional safety via etag field.
      pubsub_api.SetTopicIamPolicy(topic_name=pubsub_topic, policy=policy)
      return True
    else:
      self.logger.debug('GCS already has publish permission to topic %s.',
                        pubsub_topic)
      return False

  def _EnumerateNotificationsFromArgs(self, accept_notification_configs=True):
    """Yields bucket/notification tuples from command-line args.

    Given a list of strings that are bucket names (gs://foo) or notification
    config IDs, yield tuples of bucket names and their associated notifications.

    Args:
      accept_notification_configs: whether notification configs are valid args.
    Yields:
      Tuples of the form (bucket_name, Notification)
    """
    path_regex = self._GetNotificationPathRegex()

    for list_entry in self.args:
      match = path_regex.match(list_entry)
      if match:
        if not accept_notification_configs:
          raise CommandException(
              '%s %s accepts only bucket names, but you provided %s' %
              (self.command_name, self.subcommand_name, list_entry))
        bucket_name = match.group('bucket')
        notification_id = match.group('notification')
        found = False
        for notification in self.gsutil_api.ListNotificationConfigs(
            bucket_name, provider='gs'):
          if notification.id == notification_id:
            yield (bucket_name, notification)
            found = True
            break
        if not found:
          raise NotFoundException('Could not find notification %s' % list_entry)
      else:
        storage_url = StorageUrlFromString(list_entry)
        if not storage_url.IsCloudUrl():
          raise CommandException(
              'The %s command must be used on cloud buckets or notification '
              'config names.' % self.command_name)
        if storage_url.scheme != 'gs':
          raise CommandException('The %s command only works on gs:// buckets.')
        path = None
        if storage_url.IsProvider():
          path = 'gs://*'
        elif storage_url.IsBucket():
          path = list_entry
        if not path:
          raise CommandException(
              'The %s command cannot be used on cloud objects, only buckets' %
              self.command_name)
        for blr in self.WildcardIterator(path).IterBuckets(
            bucket_fields=['id']):
          for notification in self.gsutil_api.ListNotificationConfigs(
              blr.storage_url.bucket_name, provider='gs'):
            yield (blr.storage_url.bucket_name, notification)

  def _List(self):
    self.CheckArguments()
    if self.sub_opts:
      if '-o' in dict(self.sub_opts):
        for bucket_name in self.args:
          self._ListChannels(bucket_name)
    else:
      for bucket_name, notification in self._EnumerateNotificationsFromArgs(
          accept_notification_configs=False):
        self._PrintNotificationDetails(bucket_name, notification)
    return 0

  def _PrintNotificationDetails(self, bucket, notification):
    print('projects/_/buckets/{bucket}/notificationConfigs/{notification}\n'
          '\tCloud Pub/Sub topic: {topic}'.format(
              bucket=bucket,
              notification=notification.id,
              topic=notification.topic[len('//pubsub.googleapis.com/'):]))
    if notification.custom_attributes:
      print('\tCustom attributes:')
      for attr in notification.custom_attributes.additionalProperties:
        print('\t\t%s: %s' % (attr.key, attr.value))
    filters = []
    if notification.event_types:
      filters.append('\t\tEvent Types: %s' %
                     ', '.join(notification.event_types))
    if notification.object_name_prefix:
      filters.append("\t\tObject name prefix: '%s'" %
                     notification.object_name_prefix)
    if filters:
      print('\tFilters:')
      for line in filters:
        print(line)
    self.logger.info('')

  def _Delete(self):
    for bucket_name, notification in self._EnumerateNotificationsFromArgs():
      self._DeleteNotification(bucket_name, notification.id)
    return 0

  def _DeleteNotification(self, bucket_name, notification_id):
    self.gsutil_api.DeleteNotificationConfig(bucket_name,
                                             notification=notification_id,
                                             provider='gs')
    return 0

  def _RunSubCommand(self, func):
    try:
      (self.sub_opts,
       self.args) = getopt.getopt(self.args,
                                  self.command_spec.supported_sub_args)
      # Commands with both suboptions and subcommands need to reparse for
      # suboptions, so we log again.
      metrics.LogCommandParams(sub_opts=self.sub_opts)
      return func(self)
    except getopt.GetoptError:
      self.RaiseInvalidArgumentException()

  SUBCOMMANDS = {
      'create': _Create,
      'list': _List,
      'delete': _Delete,
      'watchbucket': _WatchBucket,
      'stopchannel': _StopChannel
  }

  def RunCommand(self):
    """Command entry point for the notification command."""
    self.subcommand_name = self.args.pop(0)
    if self.subcommand_name in NotificationCommand.SUBCOMMANDS:
      metrics.LogCommandParams(subcommands=[self.subcommand_name])
      return self._RunSubCommand(
          NotificationCommand.SUBCOMMANDS[self.subcommand_name])
    else:
      raise CommandException('Invalid subcommand "%s" for the %s command.' %
                             (self.subcommand_name, self.command_name))
