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
"""Base class for SparkR Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from apitools.base.py import encoding
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


class SparkRBase(job_base.JobBase):
  """Submit a SparkR job to a cluster."""

  @staticmethod
  def Args(parser):
    """Performs command-line argument parsing specific to SparkR."""

    parser.add_argument('r_file', help='Main .R file to run as the driver.')
    parser.add_argument(
        '--files',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        default=[],
        help='Comma separated list of files to be placed in the working '
        'directory of both the app driver and executors.')
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
        help='List of key value pairs to configure SparkR. For a list of '
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
        help=('List of key value pairs to configure driver logging, where key '
              'is a package and value is the log4j log level. For '
              'example: root=FATAL,com.example=INFO'))

  @staticmethod
  def GetFilesByType(args):
    return {
        'r_file': args.r_file,
        'archives': args.archives,
        'files': args.files
    }

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the sparkRJob member of the given job."""
    spark_r_job = messages.SparkRJob(
        args=args.job_args or [],
        archiveUris=files_by_type['archives'],
        fileUris=files_by_type['files'],
        mainRFileUri=files_by_type['r_file'],
        loggingConfig=logging_config)

    job_properties = job_util.BuildJobProperties(
        args.properties, args.properties_file)
    if job_properties:
      spark_r_job.properties = encoding.DictToMessage(
          job_properties, messages.SparkRJob.PropertiesValue)

    job.sparkRJob = spark_r_job
