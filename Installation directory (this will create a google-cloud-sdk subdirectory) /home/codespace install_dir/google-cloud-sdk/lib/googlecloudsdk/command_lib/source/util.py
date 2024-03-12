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
"""General utilties for Cloud Source commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_API_NAME = 'sourcerepo'
_API_VERSION = 'v1'

_MESSAGES = apis.GetMessagesModule(_API_NAME, _API_VERSION)


class InvalidTopicError(exceptions.Error):
  """Raised when a topic cannot be found within the repo."""


def CreateProjectResource(args):
  return resources.REGISTRY.Create(
      'sourcerepo.projects',
      projectsId=args.project or properties.VALUES.core.project.GetOrFail())


def CreateTopicResource(topic_name, topic_project):
  return resources.REGISTRY.Create(
      'pubsub.projects.topics',
      projectsId=topic_project,
      topicsId=topic_name,
  )


def ParseProjectConfigWithPushblock(args):
  project_ref = CreateProjectResource(args)
  project_name = project_ref.RelativeName()

  enable_pushblock = args.enable_pushblock
  return _MESSAGES.ProjectConfig(
      enablePrivateKeyCheck=enable_pushblock,
      name=project_name,
      pubsubConfigs=None  # No need to specify when only update key check.
  )


def ParseSourceRepoWithModifiedTopic(args, repo):
  """Parse and create a new Repo message with modified topic."""
  topic_name = GetTopicName(args)
  if args.add_topic:
    new_config = _ParsePubsubConfig(topic_name, args.message_format,
                                    args.service_account)
    return _AddTopicToResource(
        topic_name, new_config, repo, resource_name='repo')
  elif args.remove_topic:
    return _RemoveTopicFromResource(topic_name, repo, resource_name='repo')
  elif args.update_topic:
    return _UpdateTopicInResource(topic_name, args, repo, resource_name='repo')

  return repo


def ParseProjectConfigWithModifiedTopic(args, project_config):
  """Parse and create a new ProjectConfig message with modified topic."""
  topic_name = GetTopicName(args)
  if args.add_topic:
    new_config = _ParsePubsubConfig(topic_name, args.message_format,
                                    args.service_account)
    return _AddTopicToResource(
        topic_name, new_config, project_config, resource_name='project')
  elif args.remove_topic:
    return _RemoveTopicFromResource(
        topic_name, project_config, resource_name='project')
  elif args.update_topic:
    return _UpdateTopicInResource(
        topic_name, args, project_config, resource_name='project')

  return project_config


def GetTopicName(args):
  """Get the topic name based on project and topic_project flags."""
  if args.add_topic:
    topic_ref = args.CONCEPTS.add_topic.Parse()
  elif args.remove_topic:
    topic_ref = args.CONCEPTS.remove_topic.Parse()
  else:
    topic_ref = args.CONCEPTS.update_topic.Parse()

  return topic_ref.RelativeName()


def _AddTopicToResource(topic_name, new_config, resource, resource_name):
  """Add the PubsubConfig message to Repo/ProjectConfig message."""
  if resource.pubsubConfigs is None:
    config_additional_properties = []
  else:
    config_additional_properties = resource.pubsubConfigs.additionalProperties

  resource_msg_module = _MESSAGES.ProjectConfig
  if resource_name == 'repo':
    resource_msg_module = _MESSAGES.Repo

  config_additional_properties.append(
      resource_msg_module.PubsubConfigsValue.AdditionalProperty(
          key=topic_name, value=new_config))

  return resource_msg_module(
      name=resource.name,
      pubsubConfigs=resource_msg_module.PubsubConfigsValue(
          additionalProperties=config_additional_properties))


def _RemoveTopicFromResource(topic_name, resource, resource_name):
  """Remove the topic from the Repo/ProjectConfig message."""
  if resource.pubsubConfigs is None:
    raise InvalidTopicError('Invalid topic [{0}]: No topics are configured '
                            'in the {1}.'.format(topic_name, resource_name))

  config_additional_properties = resource.pubsubConfigs.additionalProperties
  for i, config in enumerate(config_additional_properties):
    if config.key == topic_name:
      del config_additional_properties[i]
      break
  else:
    raise InvalidTopicError('Invalid topic [{0}]: You must specify a '
                            'topic that is already configured in the {1}.'
                            .format(topic_name, resource_name))

  resource_msg_module = _MESSAGES.ProjectConfig
  if resource_name == 'repo':
    resource_msg_module = _MESSAGES.Repo

  return resource_msg_module(
      name=resource.name,
      pubsubConfigs=resource_msg_module.PubsubConfigsValue(
          additionalProperties=config_additional_properties))


def _UpdateTopicInResource(topic_name, args, resource, resource_name):
  """Update the topic in the configuration and return a new repo message."""

  if resource.pubsubConfigs is None:
    raise InvalidTopicError('Invalid topic [{0}]: No topics are configured '
                            'in the {1}.'.format(topic_name, resource_name))

  config_additional_properties = resource.pubsubConfigs.additionalProperties
  for i, config in enumerate(config_additional_properties):
    if config.key == topic_name:
      config_additional_properties[i].value = _UpdateConfigWithArgs(
          config.value, args)
      break
  else:
    raise InvalidTopicError('Invalid topic [{0}]: You must specify a '
                            'topic that is already configured in the {1}.'
                            .format(topic_name, resource_name))

  resource_msg_module = _MESSAGES.ProjectConfig
  if resource_name == 'repo':
    resource_msg_module = _MESSAGES.Repo

  return resource_msg_module(
      name=resource.name,
      pubsubConfigs=resource_msg_module.PubsubConfigsValue(
          additionalProperties=config_additional_properties))


def _ParsePubsubConfig(topic_name, message_format=None, service_account=None):
  """Parse and create PubsubConfig message."""
  message_format_enums = _MESSAGES.PubsubConfig.MessageFormatValueValuesEnum
  if message_format == 'protobuf':
    parsed_message_format = message_format_enums.PROTOBUF
  else:
    # By default, the message format is 'json'.
    parsed_message_format = message_format_enums.JSON

  return _MESSAGES.PubsubConfig(
      messageFormat=parsed_message_format,
      serviceAccountEmail=service_account,
      topic=topic_name)


def _GetMessageFormatString(pubsub_config):
  message_format_type = getattr(pubsub_config, 'messageFormat')
  message_format_enums = _MESSAGES.PubsubConfig.MessageFormatValueValuesEnum
  if message_format_type == message_format_enums.PROTOBUF:
    return 'protobuf'

  return 'json'


def _UpdateConfigWithArgs(pubsub_config, args):
  message_format = args.message_format or _GetMessageFormatString(pubsub_config)
  service_account = args.service_account or getattr(pubsub_config,
                                                    'serviceAccountEmail')
  topic_name = pubsub_config.topic

  return _ParsePubsubConfig(topic_name, message_format, service_account)
