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

"""Implementation of create command for Insights dataset config."""

import csv
import os

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage.insights.dataset_configs import log_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def _get_source_projects_list(source_projects_file):
  source_projects_abs_path = os.path.expanduser(source_projects_file)

  with files.FileReader(source_projects_abs_path) as f:
    try:
      reader = csv.reader(f)

      source_projects_list = []
      for row_number, row in enumerate(reader):
        row = [element.strip() for element in row if element.strip()]

        if (len(row)) > 1:
          raise ValueError(
              'Row {} Should have excatly 1 column, but found {} columns'
              .format(row_number, len(row))
          )
        if any(row) and row[0].strip():
          try:
            source_projects_list.append(int(row[0].strip()))
          except ValueError:
            raise ValueError(
                'Source project number {} is not a valid number'.format(
                    row[0].strip()
                )
            )
    except Exception as e:
      raise errors.Error(
          'Invalid format for file {} provided for the --source-projects-file'
          ' flag.\nError: {}'.format(source_projects_file, e)
      )

  return source_projects_list


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Create a new dataset config for Insights."""

  detailed_help = {
      'DESCRIPTION': """
       Create a new dataset config for Insights.
      """,
      'EXAMPLES': """
      To create a dataset config with config name as "my-config" in location
      "us-central1" and project numbers "123456" and "456789" belonging to
      organization number "54321":

         $ {command} my-config --location=us-central1
         --source-projects=123456,456789 --organization=54321 --retention-period-days=1

      To create a dataset config that automatically adds new buckets into
      config:

         $ {command} my-config --location=us-central1
         --source-projects=123456,456789 --organization=54321
         --auto-add-new-buckets --retention-period-days=1
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'DATASET_CONFIG_NAME',
        type=str,
        help='Provide human readable config name.',
    )
    source_projects_group = parser.add_group(
        mutex=True,
        required=True,
        help=(
            'List of source project numbers or the file containing list of'
            ' project numbers.'
        ),
    )
    source_projects_group.add_argument(
        '--source-projects',
        type=arg_parsers.ArgList(element_type=int),
        metavar='SOURCE_PROJECT_NUMBERS',
        help='List of source project numbers.',
    )
    source_projects_group.add_argument(
        '--source-projects-file',
        type=str,
        metavar='SOURCE_PROJECT_NUMBERS_IN_FILE',
        help=(
            'CSV formatted file containing source project numbers, one per'
            ' line.'
        ),
    )
    parser.add_argument(
        '--organization',
        type=int,
        required=True,
        metavar='SOURCE_ORG_NUMBER',
        help='Provide the source organization number.',
    )
    parser.add_argument(
        '--identity',
        type=str,
        metavar='IDENTITY_TYPE',
        choices=['IDENTITY_TYPE_PER_CONFIG', 'IDENTITY_TYPE_PER_PROJECT'],
        default='IDENTITY_TYPE_PER_CONFIG',
        help='The type of service account used in the dataset config.',
    )

    include_exclude_buckets_group = parser.add_group(
        mutex=True,
        help=(
            'Specify the list of buckets to be included or excluded, both a'
            ' list of bucket names and prefix regexes can be specified for'
            ' either include or exclude buckets.'
        ),
    )
    include_buckets_group = include_exclude_buckets_group.add_group(
        help='Specify the list of buckets to be included.',
    )
    include_buckets_group.add_argument(
        '--include-bucket-names',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_NAMES',
        help='List of bucket names be included.',
    )
    include_buckets_group.add_argument(
        '--include-bucket-prefix-regexes',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_REGEXES',
        help=(
            'List of bucket prefix regexes to be included. The dataset config'
            ' will include all the buckets that match with the prefix regex.'
            ' Examples of allowed prefix regex patterns can be'
            ' testbucket```*```, testbucket.```*```foo, testb.+foo```*``` . It'
            ' should follow syntax specified in google/re2 on GitHub. '
        ),
    )
    exclude_buckets_group = include_exclude_buckets_group.add_group(
        help='Specify the list of buckets to be excluded.',
    )
    exclude_buckets_group.add_argument(
        '--exclude-bucket-names',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_NAMES',
        help='List of bucket names to be excluded.',
    )
    exclude_buckets_group.add_argument(
        '--exclude-bucket-prefix-regexes',
        type=arg_parsers.ArgList(),
        metavar='BUCKETS_REGEXES',
        help=(
            'List of bucket prefix regexes to be excluded. Allowed regex'
            ' patterns are similar to those for the'
            ' --include-bucket-prefix-regexes flag.'
        ),
    )

    include_exclude_locations_group = parser.add_group(
        mutex=True,
        help=(
            'Specify the list of locations for source projects to be included'
            ' or excluded.'
        ),
    )
    include_exclude_locations_group.add_argument(
        '--include-source-locations',
        type=arg_parsers.ArgList(),
        metavar='LIST_OF_SOURCE_LOCATIONS',
        help='List of locations for projects to be included.',
    )
    include_exclude_locations_group.add_argument(
        '--exclude-source-locations',
        type=arg_parsers.ArgList(),
        metavar='LIST_OF_SOURCE_LOCATIONS',
        help='List of locations for projects to be excluded.',
    )

    parser.add_argument(
        '--auto-add-new-buckets',
        action='store_true',
        help=(
            'Automatically include any new buckets created if they satisfy'
            ' criteria defined in config settings.'
        ),
    )

    flags.add_dataset_config_location_flag(parser)
    flags.add_dataset_config_create_update_flags(parser)

  def Run(self, args):

    if args.source_projects is not None:
      source_projects_list = args.source_projects
    else:
      source_projects_list = _get_source_projects_list(
          args.source_projects_file
      )

    api_client = insights_api.InsightsApi()

    try:
      dataset_config_operation = api_client.create_dataset_config(
          dataset_config_name=args.DATASET_CONFIG_NAME,
          location=args.location,
          destination_project=properties.VALUES.core.project.Get(),
          source_projects_list=source_projects_list,
          organization_number=args.organization,
          include_buckets_name_list=args.include_bucket_names,
          include_buckets_prefix_regex_list=args.include_bucket_prefix_regexes,
          exclude_buckets_name_list=args.exclude_bucket_names,
          exclude_buckets_prefix_regex_list=args.exclude_bucket_prefix_regexes,
          include_source_locations=args.include_source_locations,
          exclude_source_locations=args.exclude_source_locations,
          auto_add_new_buckets=args.auto_add_new_buckets,
          retention_period=args.retention_period_days,
          identity_type=args.identity,
          description=args.description,
      )
      log_util.dataset_config_operation_started_and_status_log(
          'Create', args.DATASET_CONFIG_NAME, dataset_config_operation.name
      )
    except apitools_exceptions.HttpBadRequestError:
      log.status.Print(
          'We caught an exception while trying to create the'
          ' dataset-configuration.\nPlease check that the flags are set with'
          ' valid values. For example, config name must start with an'
          " alphanumeric value and only contain '_' as a special character"
      )
      raise
