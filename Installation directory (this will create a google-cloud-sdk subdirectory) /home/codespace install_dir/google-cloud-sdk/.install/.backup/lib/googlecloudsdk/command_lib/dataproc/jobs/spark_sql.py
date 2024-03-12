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

"""Base class for Spark Sql Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


class SparkSqlBase(job_base.JobBase):
  """Submit a Spark SQL job to a cluster."""

  @staticmethod
  def Args(parser):
    """Parses command-line arguments specific to submitting SparkSql jobs."""
    driver = parser.add_mutually_exclusive_group(required=True)
    driver.add_argument(
        '--execute', '-e',
        metavar='QUERY',
        dest='queries',
        action='append',
        default=[],
        help='A Spark SQL query to execute as part of the job.')
    driver.add_argument(
        '--file', '-f',
        help=('HCFS URI of file containing Spark SQL script to execute as '
              'the job.'))
    parser.add_argument(
        '--jars',
        type=arg_parsers.ArgList(),
        metavar='JAR',
        default=[],
        help=('Comma separated list of jar files to be provided to the '
              'executor and driver classpaths. May contain UDFs.'))
    parser.add_argument(
        '--params',
        type=arg_parsers.ArgDict(),
        metavar='PARAM=VALUE',
        help='A list of key value pairs to set variables in the Hive queries.')
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help='A list of key value pairs to configure Hive.')
    parser.add_argument(
        '--properties-file',
        help=job_util.PROPERTIES_FILE_HELP_TEXT)
    parser.add_argument(
        '--driver-log-levels',
        type=arg_parsers.ArgDict(),
        metavar='PACKAGE=LEVEL',
        help=('A list of package to log4j log level pairs to configure driver '
              'logging. For example: root=FATAL,com.example=INFO'))

  @staticmethod
  def GetFilesByType(args):
    return {
        'jars': args.jars,
        'file': args.file}

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the sparkSqlJob member of the given job."""

    spark_sql_job = messages.SparkSqlJob(
        jarFileUris=files_by_type['jars'],
        queryFileUri=files_by_type['file'],
        loggingConfig=logging_config)

    if args.queries:
      spark_sql_job.queryList = messages.QueryList(queries=args.queries)
    if args.params:
      spark_sql_job.scriptVariables = encoding.DictToAdditionalPropertyMessage(
          args.params, messages.SparkSqlJob.ScriptVariablesValue)

    job_properties = job_util.BuildJobProperties(
        args.properties, args.properties_file)
    if job_properties:
    # Sort properties to ensure tests comparing messages not fail on ordering.
      spark_sql_job.properties = encoding.DictToAdditionalPropertyMessage(
          job_properties, messages.SparkSqlJob.PropertiesValue, sort_items=True)

    job.sparkSqlJob = spark_sql_job
