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

"""Base class for PySpark Job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from apitools.base.py import encoding

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc.jobs import base as job_base
from googlecloudsdk.command_lib.dataproc.jobs import util as job_util


@base.Hidden
class PyFlinkBase(job_base.JobBase):
  """Submit a PyFlink job to a cluster."""

  @staticmethod
  def Args(parser):
    """Performs command-line argument parsing specific to PyFlink."""

    parser.add_argument(
        'py_file', help='HCFS URI of the main Python file.'
    )
    parser.add_argument(
        '--savepoint',
        help='HCFS URI of the savepoint that contains the saved job progress.',
    )
    parser.add_argument(
        '--py-files',
        type=arg_parsers.ArgList(),
        metavar='PY_FILE',
        default=[],
        help=(
            'Comma-separated list of custom Python files to provide to the'
            ' job. Supports standard resource file suffixes, such as'
            ' .py, .egg, .zip and .whl. This also supports passing a directory.'
        ),
    )
    parser.add_argument(
        '--py-requirements',
        help=(
            'A requirements.txt file that defines third-party dependencies.'
            ' These dependencies are installed and added to the PYTHONPATH of'
            ' the python UDF worker.'
        ),
    )
    parser.add_argument(
        '--py-module',
        help=(
            'Python module with program entry point. This option should be used'
            ' with --pyFiles.'
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
        '--archives',
        type=arg_parsers.ArgList(),
        metavar='ARCHIVE',
        default=[],
        help=(
            'Comma-separated list of archives to be extracted into the working'
            ' directory of the python UDF worker. Must be one of the following '
            'file formats: .zip, .tar, .tar.gz, or .tgz.'
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
            'List of key=value pairs to configure PyFlink. For a list of '
            'available properties, see: '
            'https://nightlies.apache.org/flink/flink-docs-master/docs/deployment/config/'
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
            'List of key=value pairs to configure driver logging, where the key'
            ' is a package and the value is the log4j log level. For '
            'example: root=FATAL,com.example=INFO.'
        ),
    )

  @staticmethod
  def GetFilesByType(args):
    return {
        'py_file': args.py_file,
        'py_files': args.py_files,
        'archives': args.archives,
        'py_requirements': args.py_requirements,
        'jars': args.jars,
    }

  @staticmethod
  def ConfigureJob(messages, job, files_by_type, logging_config, args):
    """Populates the pyflinkJob member of the given job."""

    pyflink_job = messages.PyFlinkJob(
        args=args.job_args or [],
        archiveUris=files_by_type['archives'],
        pythonFileUris=files_by_type['py_files'],
        jarFileUris=files_by_type['jars'],
        pythonRequirements=files_by_type['py_requirements'],
        pythonModule=args.py_module,
        mainPythonFileUri=files_by_type['py_file'],
        loggingConfig=logging_config,
        savepointUri=args.savepoint
    )

    job_properties = job_util.BuildJobProperties(
        args.properties, args.properties_file
    )
    if job_properties:
      # Sort properties to ensure tests comparing messages not fail on ordering.
      pyflink_job.properties = encoding.DictToAdditionalPropertyMessage(
          job_properties, messages.PyFlinkJob.PropertiesValue, sort_items=True
      )

    job.pyflinkJob = pyflink_job
