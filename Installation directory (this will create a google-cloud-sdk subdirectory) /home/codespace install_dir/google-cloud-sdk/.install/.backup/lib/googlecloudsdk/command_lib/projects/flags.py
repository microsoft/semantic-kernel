# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Common flags for projects commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def GetProjectFlag(verb):
  return base.Argument(
      'id',
      metavar='PROJECT_ID',
      completer=completers.ProjectCompleter,
      help='ID for the project you want to {0}.'.format(verb))


def GetProjectIDNumberFlag(verb):
  return base.Argument(
      'id',
      metavar='PROJECT_ID_OR_NUMBER',
      completer=completers.ProjectCompleter,
      help='ID or number for the project you want to {0}.'.format(verb))


def GetRecommendFlag(action):
  return base.Argument(
      '--recommend',
      metavar='BOOLEAN_VALUE',
      type=arg_parsers.ArgBoolean(),
      default=False,
      required=False,
      help=(
          'If true, checks Active Assist recommendation for the risk level of '
          '{}, and issues a warning in the prompt. Optional flag is set to '
          'false by default. For details see https://cloud.google.com/'
          'recommender/docs/change-risk-recommendations'
      ).format(action),
  )


def ProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='project_id',
      help_text='The project id.')


def GetProjectResourceSpec():
  return concepts.ResourceSpec(
      'cloudresourcemanager.projects',
      resource_name='project',
      projectId=ProjectAttributeConfig(),
  )


def GetProjectResourceArg(verb):
  return concept_parsers.ConceptParser.ForResource(
      'project_id',
      GetProjectResourceSpec(),
      'ID for the project you want to {}.'.format(verb),
      required=True)


SHUT_DOWN_PROJECTS_URL = 'https://cloud.google.com/resource-manager/docs/creating-managing-projects'

CREATE_DELETE_IN_CONSOLE_SEE_ALSO = (
    'See https://support.google.com/cloud/answer/6251787 for information on '
    'creating or deleting projects from the Google Cloud Platform Console.')

SHUT_DOWN_PROJECTS = ('See {0} for information on shutting down projects.'
                      .format(SHUT_DOWN_PROJECTS_URL))
