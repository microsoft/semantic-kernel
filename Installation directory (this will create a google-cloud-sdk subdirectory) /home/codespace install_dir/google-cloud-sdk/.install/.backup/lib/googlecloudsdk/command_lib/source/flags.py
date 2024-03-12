# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Common arguments for `gcloud source repos` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.source import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers

REPO_NAME_VALIDATOR = arg_parsers.RegexpValidator(
    '[A-Za-z0-9_][-._A-Za-z0-9/]{0,127}',
    'repostory name may contain between 1 and 128 (inclusive) letters, digits, '
    'hyphens, periods, underscores and slashes.')


def AddPushblockFlags(group):
  """Add pushblock enabled/disabled flags to the given group."""

  group.add_argument(
      '--enable-pushblock',
      action='store_true',
      help="""\
Enable PushBlock for all repositories under current project.
PushBlock allows repository owners to block git push transactions containing
private key data.""")

  group.add_argument(
      '--disable-pushblock',
      action='store_true',
      help="""\
Disable PushBlock for all repositories under current project.
PushBlock allows repository owners to block git push transactions containing
private key data.""")


def AddOptionalTopicFlags(group, resource_name='repo'):
  """Add message_format and service_account flags to the topic arg group."""
  group.add_argument(
      '--message-format',
      choices=['json', 'protobuf'],
      help="""\
The format of the message to publish to the topic.""")

  group.add_argument(
      '--service-account',
      help="""\
Email address of the service account used for publishing Cloud Pub/Sub messages.
This service account needs to be in the same project as the {}. When added, the
caller needs to have iam.serviceAccounts.actAs permission on this service
account. If unspecified, it defaults to the Compute Engine default service
account.""".format(resource_name))

  group.add_argument(
      '--topic-project',
      help="""\
Cloud project for the topic. If not set, the currently set project will be
used.""")


def AddRepoUpdateArgs(parser, verb='to update'):
  """Add the arg groups for `source repos update` command."""
  topic_group = parser.add_group(
      'Manages Cloud Pub/Sub topics associated with the repository.',
      required=True)
  topic_resource_group = topic_group.add_argument_group(
      mutex=True, required=True)

  concept_parsers.ConceptParser(
      [
          resource_args.CreateTopicResourcePresentationSpec(
              'add', 'The Cloud Pub/Sub topic to add to the repository.',
              topic_resource_group),
          resource_args.CreateTopicResourcePresentationSpec(
              'remove',
              'The Cloud Pub/Sub topic to remove from the repository.',
              topic_resource_group),
          resource_args.CreateTopicResourcePresentationSpec(
              'update', 'The Cloud Pub/Sub topic to update in the project.',
              topic_resource_group),
          resource_args.CreateRepoResourcePresentationSpec(verb)
      ],
      command_level_fallthroughs={
          '--add-topic.project': ['--topic-project'],
          '--remove-topic.project': ['--topic-project'],
          '--update-topic.project': ['--topic-project'],
      }).AddToParser(parser)

  AddOptionalTopicFlags(topic_group)


def AddProjectConfigUpdateArgs(parser):
  """Add the arg groups for `source project-configs update` command."""
  update_group = parser.add_group(required=True, mutex=True)
  AddPushblockFlags(update_group)
  topic_group = update_group.add_group(
      'Manage Cloud Pub/Sub topics associated with the Cloud project.')
  topic_resource_group = topic_group.add_argument_group(mutex=True)

  concept_parsers.ConceptParser(
      [
          resource_args.CreateTopicResourcePresentationSpec(
              'add', 'The Cloud Pub/Sub topic to add to the project.',
              topic_resource_group),
          resource_args.CreateTopicResourcePresentationSpec(
              'remove', 'The Cloud Pub/Sub topic to remove from the project.',
              topic_resource_group),
          resource_args.CreateTopicResourcePresentationSpec(
              'update', 'The Cloud Pub/Sub topic to update in the project.',
              topic_resource_group),
      ],
      command_level_fallthroughs={
          '--add-topic.project': ['--topic-project'],
          '--remove-topic.project': ['--topic-project'],
          '--update-topic.project': ['--topic-project'],
      }).AddToParser(parser)
  AddOptionalTopicFlags(topic_group, 'project')
