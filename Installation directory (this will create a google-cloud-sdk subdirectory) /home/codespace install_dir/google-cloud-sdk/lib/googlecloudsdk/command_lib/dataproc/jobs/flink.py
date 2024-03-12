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

"""Base class for Flink Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from apitools.base.py import encoding

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


class FlinkBase(job_base.JobBase):
  """Submit a Java or Scala Flink job to a cluster."""

  @staticmethod
  def Args(parser):
    """Parses command-line arguments specific to submitting Flink jobs."""
    parser.add_argument(
        '--savepoint',
        help=(
            'HCFS URI of the savepoint that is used to refer to the state of '
            'the previously stopped job. The new job will resume previous '
            'state from there.'
        ),
    )
    parser.add_argument(
        '--jars',
        type=arg_parsers.ArgList(),
        metavar='JAR',
        default=[],
        help=(
            'Comma-separated list of jar files to provide to the '
            'task manager classpaths.'
        ),
    )
    parser.add_argument(
        'job_args',
        nargs=argparse.REMAINDER,
        help='The job arguments to pass.',
    )
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help=(
            'List of key=value pairs to configure Flink. For a list of '
            'available properties, see: '
            'https://nightlies.apache.org/flink/flink-docs-master/docs/deployment/config/.'
        ),
    )
    parser.add_argument(
        '--properties-file', help=job_util.PROPERTIES_FILE_HELP_TEXT
    )
    parser.add_argument(
        '--driver-log-levels',
        type=arg_parsers.ArgDict(),
        metavar='PACKAGE=LEVEL',
        help=(
            'List of package to log4j log level pairs to configure driver '
            'logging. For example: root=FATAL,com.example=INFO.'
        ),
    )

  @staticmethod
  def GetFilesByType(args):
    """Returns a dict of files by their type (main_jar, jars, etc.)."""
    return {'main_jar': args.main_jar, 'jars': args.jars}

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the flinkJob member of the given job."""

    flink_job = messages.FlinkJob(
        args=args.job_args or [],
        mainClass=args.main_class,
        mainJarFileUri=files_by_type['main_jar'],
        jarFileUris=files_by_type['jars'],
        loggingConfig=logging_config,
        savepointUri=args.savepoint
    )

    job_properties = job_util.BuildJobProperties(
        args.properties, args.properties_file
    )
    if job_properties:
      # Sort properties to ensure tests comparing messages not fail on ordering.
      flink_job.properties = encoding.DictToAdditionalPropertyMessage(
          job_properties, messages.FlinkJob.PropertiesValue, sort_items=True
      )

    job.flinkJob = flink_job
