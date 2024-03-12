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
"""Base class for the Trino job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


class TrinoBase(job_base.JobBase):
  """Submit a Trino job to a cluster."""

  @staticmethod
  def Args(parser):
    """Parses command line arguments specific to submitting Trino jobs."""
    driver = parser.add_mutually_exclusive_group(required=True)
    driver.add_argument(
        '--execute',
        '-e',
        metavar='QUERY',
        dest='queries',
        action='append',
        default=[],
        help='A Trino query to execute.')
    driver.add_argument(
        '--file',
        '-f',
        help='HCFS URI of file containing the Trino script to execute.')
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PARAM=VALUE',
        help='A list of key value pairs to set Trino session properties.')
    parser.add_argument(
        '--properties-file',
        help=job_util.PROPERTIES_FILE_HELP_TEXT)
    parser.add_argument(
        '--driver-log-levels',
        type=arg_parsers.ArgDict(),
        metavar='PACKAGE=LEVEL',
        help=('A list of package-to-log4j log level pairs to configure driver '
              'logging. For example: root=FATAL,com.example=INFO'))
    parser.add_argument(
        '--continue-on-failure',
        action='store_true',
        help='Whether to continue if a query fails.')
    parser.add_argument(
        '--query-output-format',
        help=('The query output display format. See the Trino documentation '
              'for supported output formats.'))
    parser.add_argument(
        '--client-tags',
        type=arg_parsers.ArgList(),
        metavar='CLIENT_TAG',
        help='A list of Trino client tags to attach to this query.')

  @staticmethod
  def GetFilesByType(args):
    return {'file': args.file}

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the trinoJob member of the given job."""

    trino_job = messages.TrinoJob(
        continueOnFailure=args.continue_on_failure,
        queryFileUri=files_by_type['file'],
        loggingConfig=logging_config)

    if args.queries:
      trino_job.queryList = messages.QueryList(queries=args.queries)
    if args.query_output_format:
      trino_job.outputFormat = args.query_output_format
    if args.client_tags:
      trino_job.clientTags = args.client_tags

    job_properties = job_util.BuildJobProperties(
        args.properties, args.properties_file)
    if job_properties:
    # Sort properties to ensure tests comparing messages not fail on ordering.
      trino_job.properties = encoding.DictToAdditionalPropertyMessage(
          job_properties, messages.TrinoJob.PropertiesValue, sort_items=True)

    job.trinoJob = trino_job
