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

"""Base class for Hadoop Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from apitools.base.py import encoding

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


class HadoopBase(job_base.JobBase):
  """Common functionality between release tracks."""

  @staticmethod
  def Args(parser):
    """Parses command-line arguments specific to submitting Hadoop jobs."""
    parser.add_argument(
        '--jars',
        type=arg_parsers.ArgList(),
        metavar='JAR',
        default=[],
        help=('Comma separated list of jar files to be provided to the MR and '
              'driver classpaths.'))
    parser.add_argument(
        '--files',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        default=[],
        help='Comma separated list of file paths to be provided to the job. '
             'A file path can either be a path to a local file or a path '
             'to a file already in a Cloud Storage bucket.')
    parser.add_argument(
        '--archives',
        type=arg_parsers.ArgList(),
        metavar='ARCHIVE',
        default=[],
        help=('Comma separated list of archives to be provided to the job. '
              'must be one of the following file formats: .zip, .tar, .tar.gz, '
              'or .tgz.'))
    parser.add_argument(
        'job_args',
        nargs=argparse.REMAINDER,
        help='The arguments to pass to the driver.')
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help='A list of key value pairs to configure Hadoop.')
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
    """Returns a dict of files by their type (jars, archives, etc.)."""
    return {
        'main_jar': args.main_jar,
        'jars': args.jars,
        'archives': args.archives,
        'files': args.files}

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the hadoopJob member of the given job."""
    hadoop_job = messages.HadoopJob(
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
      hadoop_job.properties = encoding.DictToAdditionalPropertyMessage(
          job_properties, messages.HadoopJob.PropertiesValue, sort_items=True)

    job.hadoopJob = hadoop_job
