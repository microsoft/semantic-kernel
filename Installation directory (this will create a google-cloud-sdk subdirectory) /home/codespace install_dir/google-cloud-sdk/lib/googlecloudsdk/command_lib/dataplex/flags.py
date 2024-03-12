# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Shared resource args for the Dataplex surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AddDiscoveryArgs(parser):
  """Adds Discovery Args to parser."""
  discovery_spec = parser.add_group(
      help='Settings to manage the metadata discovery and publishing.')
  discovery_spec.add_argument(
      '--discovery-enabled',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether discovery is enabled.')
  discovery_spec.add_argument(
      '--discovery-include-patterns',
      default=[],
      type=arg_parsers.ArgList(),
      metavar='INCLUDE_PATTERNS',
      help="""The list of patterns to apply for selecting data to include
        during discovery if only a subset of the data should considered. For
        Cloud Storage bucket assets, these are interpreted as glob patterns
        used to match object names. For BigQuery dataset assets, these are
        interpreted as patterns to match table names.""")
  discovery_spec.add_argument(
      '--discovery-exclude-patterns',
      default=[],
      type=arg_parsers.ArgList(),
      metavar='EXCLUDE_PATTERNS',
      help="""The list of patterns to apply for selecting data to exclude
        during discovery. For Cloud Storage bucket assets, these are interpreted
        as glob patterns used to match object names. For BigQuery dataset
        assets, these are interpreted as patterns to match table names.""")
  trigger = discovery_spec.add_group(
      help='Determines when discovery jobs are triggered.')
  trigger.add_argument(
      '--discovery-schedule',
      help="""[Cron schedule](https://en.wikipedia.org/wiki/Cron) for running
                discovery jobs periodically. Discovery jobs must be scheduled at
                least 30 minutes apart.""")
  discovery_prefix = discovery_spec.add_group(help='Describe data formats.')
  csv_option = discovery_prefix.add_group(
      help='Describe CSV and similar semi-structured data formats.')
  csv_option.add_argument(
      '--csv-header-rows',
      type=int,
      help='The number of rows to interpret as header rows that should be skipped when reading data rows.'
  )
  csv_option.add_argument(
      '--csv-delimiter',
      help='The delimiter being used to separate values. This defaults to \',\'.'
  )
  csv_option.add_argument(
      '--csv-encoding',
      help='The character encoding of the data. The default is UTF-8.')
  csv_option.add_argument(
      '--csv-disable-type-inference',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to disable the inference of data type for CSV data. If true, all columns will be registered as strings.'
  )
  json_option = discovery_prefix.add_group(help='Describe JSON data format.')
  json_option.add_argument(
      '--json-encoding',
      help='The character encoding of the data. The default is UTF-8.')
  json_option.add_argument(
      '--json-disable-type-inference',
      action=arg_parsers.StoreTrueFalseAction,
      help=' Whether to disable the inference of data type for Json data. If true, all columns will be registered as their primitive types (strings, number or boolean).'
  )
  return discovery_spec
