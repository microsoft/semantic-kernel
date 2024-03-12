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
"""Flags and helpers for the compute network-attachments commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      region.basename(),
      connection_preference
    )"""


class NetworkAttachmentsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(NetworkAttachmentsCompleter, self).__init__(
        collection='compute.networkAttachments',
        list_command='compute network-attachments list --uri',
        **kwargs)


def AddDescription(parser):
  """Add support for --description flag."""
  parser.add_argument(
      '--description',
      default=None,
      help='An optional, textual description for the network attachment.')


def AddConnectionPreference(parser):
  """Add support for --connection-preference flag."""
  parser.add_argument(
      '--connection-preference',
      choices=['ACCEPT_AUTOMATIC', 'ACCEPT_MANUAL'],
      type=lambda x: x.replace('-', '_').upper(),
      default='ACCEPT_AUTOMATIC',
      help="""\
      The connection preference of network attachment.
      The value can be set to ACCEPT_AUTOMATIC or ACCEPT_MANUAL.
      An ACCEPT_AUTOMATIC network attachment is one that
      always accepts the connection from producer NIC.
      An ACCEPT_MANUAL network attachment is one that
      requires an explicit addition of the producer project id
      or project number to the producer accept list.
      """)


def AddProducerRejectList(parser):
  """Add support for --producer-reject-list flag."""
  parser.add_argument(
      '--producer-reject-list',
      type=arg_parsers.ArgList(),
      metavar='REJECT_LIST',
      default=None,
      help="""\
      Projects that are not allowed to connect to this network attachment.
      """)


def AddProducerAcceptList(parser):
  """Add support for --producer-accept-list flag."""
  parser.add_argument(
      '--producer-accept-list',
      type=arg_parsers.ArgList(),
      metavar='ACCEPT_LIST',
      default=None,
      help="""\
      Projects that are allowed to connect to this network attachment.
      """)


def NetworkAttachmentArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='network attachment',
      completer=NetworkAttachmentsCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.networkAttachments',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)
