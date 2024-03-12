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
"""Shared resource flags for Cloud Source Repo."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties


def ProjectAttributeConfig():
  """Get project resource attribute with default value."""
  return concepts.ResourceParameterAttributeConfig(
      name='project',
      help_text='Cloud Project for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(properties.VALUES.core.project)])


def TopicAttributeConfig():
  """Get Pub/Sub topic resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='topic', help_text='Name of the topic.')


def RepoAttributeConfig():
  """Get Cloud Source Repo resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='repo', help_text='Name of the repository.')


def GetTopicResourceSpec():
  return concepts.ResourceSpec(
      'pubsub.projects.topics',
      resource_name='topic',
      topicsId=TopicAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def GetRepoResourceSpec():
  return concepts.ResourceSpec(
      'sourcerepo.projects.repos',
      resource_name='repo',
      reposId=RepoAttributeConfig(),
      projectsId=ProjectAttributeConfig())


def CreateRepoResourcePresentationSpec(verb, positional=True):
  name = 'repo' if positional else '--repo'
  return presentation_specs.ResourcePresentationSpec(
      name,
      GetRepoResourceSpec(),
      'Name of the Cloud Source repository {}.'.format(verb),
      required=True,
  )


def CreateTopicResourcePresentationSpec(verb, help_text, group):
  """Create add_topic, remove_topic or update_topic specs."""
  name = '--' + verb + '-topic'

  return presentation_specs.ResourcePresentationSpec(
      name, GetTopicResourceSpec(), help_text, prefixes=True, group=group)
