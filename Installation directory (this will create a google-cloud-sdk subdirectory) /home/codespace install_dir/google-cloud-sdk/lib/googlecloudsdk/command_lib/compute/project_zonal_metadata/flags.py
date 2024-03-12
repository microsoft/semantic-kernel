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
"""Flags and helpers for the compute project zonal metadata commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers


def AddDescribeProjectZonalMetadataFlags(parser):
  parser.add_argument(
      '--zone',
      help='Zone for project zonal metadata',
      completer=compute_completers.ZonesCompleter,
      required=True,
  )


def ProjectZonalMetadataAddMetadataFlags(parser):
  """Flags for adding/updating metadata on instance settings."""
  parser.add_argument(
      '--metadata',
      default={},
      type=arg_parsers.ArgDict(min_length=1),
      help=(
          'The project zonal metadata key-value pairs that you want to add or'
          ' update\n\n'
      ),
      metavar='KEY=VALUE',
      required=True,
      action=arg_parsers.StoreOnceAction,
  )
  parser.add_argument(
      '--zone',
      help=(
          'The zone in which you want to add or update project zonal'
          ' metadata\n\n'
      ),
      completer=compute_completers.ZonesCompleter,
      required=True,
  )


def ProjectZonalMetadataRemoveMetadataFlags(parser):
  """Flags for removing metadata on instance settings."""
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--all',
      default=False,
      help=(
          'If provided, all project zonal metadata entries are removed from VM'
          ' instances in the zone.'
      ),
      action='store_true',
  )
  group.add_argument(
      '--keys',
      default={},
      type=arg_parsers.ArgList(min_length=1),
      metavar='KEY',
      help='The keys for which you want to remove project zonal metadata\n\n',
  )
  parser.add_argument(
      '--zone',
      help='The zone in which you want to remove project zonal metadata\n\n',
      completer=compute_completers.ZonesCompleter,
      required=True,
  )
