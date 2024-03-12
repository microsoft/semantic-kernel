# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Flags for backup-dr commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def GetManagementServerResourceSpec():
  return concepts.ResourceSpec(
      'backupdr.projects.locations.managementServers',
      resource_name='Management Server',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def LocationAttributeConfig(arg_name='location'):
  return concepts.ResourceParameterAttributeConfig(
      name=arg_name, help_text='The location of the {resource}.'
  )


def AddManagementServerResourceArg(parser, help_text):
  """Adds an argument for management server to parser."""
  name = 'management_server'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetManagementServerResourceSpec(),
      help_text,
      required=True,
  ).AddToParser(parser)


def AddNetwork(parser, required=True):
  """Adds a positional network argument to parser.

  Args:
    parser: argparse.Parser: Parser object for command line inputs.
    required: Whether or not --network is required.
  """
  parser.add_argument(
      '--network',
      required=required,
      type=str,
      help=(
          'Name of an existing VPC network with private service access'
          ' configured in the format -'
          ' projects/<project>/global/networks/<network>. This VPC network'
          ' allows the management console to communicate with all'
          ' backup/recovery appliances and requires a minimum IP range of /23.'
          ' This value cannot be changed after you deploy the management'
          " server. If you don't have private service access, configure one."
          ' [Learn more]'
          ' (https://cloud.google.com/vpc/docs/configure-private-services-access)'
      ),
  )
