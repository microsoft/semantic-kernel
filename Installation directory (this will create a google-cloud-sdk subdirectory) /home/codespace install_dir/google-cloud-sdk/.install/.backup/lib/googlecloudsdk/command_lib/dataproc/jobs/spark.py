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

"""Base class for Spark Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from apitools.base.py import encoding

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


class SparkBase(job_base.JobBase):
  """Submit a Java or Scala Spark job to a cluster."""

  @staticmethod
  def Args(parser):
    """Parses command-line arguments specific to submitting Spark jobs."""
    parser.add_argument(
        '--jars',
        type=arg_parsers.ArgList(),
        metavar='JAR',
        default=[],
        help=('Comma separated list of jar files to be provided to the '
              'executor and driver classpaths.'))
    parser.add_argument(
        '--files',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        default=[],
        help=('Comma separated list of files to be placed in the working '
              'directory of both the app driver and executors.'))
    parser.add_argument(
        '--archives',
        type=arg_parsers.ArgList(),
        metavar='ARCHIVE',
        default=[],
        help=(
            'Comma separated list of archives to be extracted into the working '
            'directory of each executor. '
            'Must be one of the following file formats: .zip, .tar, .tar.gz, '
            'or .tgz.'))
    parser.add_argument(
        'job_args',
        nargs=argparse.REMAINDER,
        help='Arguments to pass to the driver.')
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help='List of key value pairs to configure Spark. For a list of '
             'available properties, see: '
             'https://spark.apache.org/docs/latest/'
             'configuration.html#available-properties.')
    parser.add_argument(
        '--properties-file',
        help=job_util.PROPERTIES_FILE_HELP_TEXT)
    parser.add_argument(
        '--driver-log-levels',
        type=arg_parsers.ArgDict(),
        metavar='PACKAGE=LEVEL',
        help=('List of package to log4j log level pairs to configure driver '
              'logging. For example: root=FATAL,com.example=INFO'))

  @staticmethod
  def GetFilesByType(args):
    """Returns a dict of files by their type (jars, archives, etc.)."""
    return {
        'main_jar': args.main_jar,
        'jars': args.jars,
        'archives': args.archives,
        'files': args.files}

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the sparkJob member of the given job."""

    spark_job = messages.SparkJob(
        args=args.job_args or [],
        archiveUris=files_by_type['archives'],
        fileUris=files_by_type['files'],
        jarFileUris=files_by_type['jars'],
        mainClass=args.main_class,
        mainJarFileUri=files_by_type['main_jar'],
        loggingConfig=logging_config)

    job_properties = job_util.BuildJobProperties(
        args.properties, args.properties_file)
    if job_properties:
    # Sort properties to ensure tests comparing messages not fail on ordering.
      spark_job.properties = encoding.DictToAdditionalPropertyMessage(
          job_properties, messages.SparkJob.PropertiesValue, sort_items=True)

    job.sparkJob = spark_job
