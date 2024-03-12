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
"""Helpers for writing commands interacting with jobs and their IDs.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def ArgsForJobRef(parser):
  """Register flags for specifying a single Job ID.

  Args:
    parser: The argparse.ArgParser to configure with job-filtering arguments.
  """
  parser.add_argument('job', metavar='JOB_ID', help='Job ID to operate on.')
  # TODO(b/139889563): Mark as required when default region is removed
  parser.add_argument(
      '--region',
      metavar='REGION_ID',
      help=('Region ID of the job\'s regional endpoint. ' +
            dataflow_util.DEFAULT_REGION_MESSAGE))


def ArgsForJobRefs(parser, **kwargs):
  """Register flags for specifying jobs using positional job IDs.

  Args:
    parser: The argparse.ArgParser to configure with job ID arguments.
    **kwargs: Extra arguments to pass to the add_argument call.
  """
  parser.add_argument(
      'jobs', metavar='JOB_ID', help='Job IDs to operate on.', **kwargs)
  # TODO(b/139889563): Mark as required when default region is removed
  parser.add_argument(
      '--region',
      metavar='REGION_ID',
      help=('Region ID of the jobs\' regional endpoint. ' +
            dataflow_util.DEFAULT_REGION_MESSAGE))


def ExtractJobRef(args):
  """Extract the Job Ref for a command. Used with ArgsForJobRef.

  Args:
    args: The command line arguments.
  Returns:
    A Job resource.
  """
  job = args.job
  region = dataflow_util.GetRegion(args)
  return resources.REGISTRY.Parse(
      job,
      params={
          'projectId': properties.VALUES.core.project.GetOrFail,
          'location': region
      },
      collection='dataflow.projects.locations.jobs')


def ExtractJobRefs(args):
  """Extract the Job Refs for a command. Used with ArgsForJobRefs.

  Args:
    args: The command line arguments that were provided to this invocation.
  Returns:
    A list of job resources.
  """
  jobs = args.jobs
  region = dataflow_util.GetRegion(args)
  return [
      resources.REGISTRY.Parse(
          job,
          params={
              'projectId': properties.VALUES.core.project.GetOrFail,
              'location': region
          },
          collection='dataflow.projects.locations.jobs') for job in jobs
  ]


def CommonArgs(parser):
  """Register flags applicable to all template launches.

  Args:
    parser: argparse.ArgumentParser to register arguments with.
  """
  parser.add_argument(
      '--dataflow-kms-key',
      help='The Cloud KMS key to protect the job resources.')

  parser.add_argument(
      '--disable-public-ips',
      action=actions.StoreBooleanProperty(
          properties.VALUES.dataflow.disable_public_ips),
      help='The Cloud Dataflow workers must not use public IP addresses.')

  parser.add_argument(
      '--max-workers', type=int, help='The maximum number of workers to run.')

  parser.add_argument(
      '--network',
      help='The Compute Engine network for launching instances to '
      'run your pipeline.')

  parser.add_argument(
      '--num-workers', type=int, help='The initial number of workers to use.')

  parser.add_argument(
      '--service-account-email',
      type=arg_parsers.RegexpValidator(r'.*@.*\..*',
                                       'must provide a valid email address'),
      help='The service account to run the workers as.')

  parser.add_argument(
      '--subnetwork',
      help='The Compute Engine subnetwork for launching instances '
      'to run your pipeline.')

  parser.add_argument(
      '--worker-machine-type',
      help='The type of machine to use for workers. Defaults to '
      'server-specified.')

  group = parser.add_group(mutex=True, help='Worker location options.')

  group.add_argument(
      '--worker-region',
      type=arg_parsers.RegexpValidator(r'\w+-\w+\d',
                                       'must provide a valid region'),
      help='The region to run the workers in.')

  group.add_argument(
      '--worker-zone',
      type=arg_parsers.RegexpValidator(r'\w+-\w+\d-\w',
                                       'must provide a valid zone'),
      help='The zone to run the workers in.')

  group.add_argument(
      '--zone',
      type=arg_parsers.RegexpValidator(r'\w+-\w+\d-\w',
                                       'must provide a valid zone'),
      help='The zone to run the workers in.',
      action=actions.DeprecationAction(
          '--zone',
          warn=('The {flag_name} option is deprecated; '
                'use --worker-region or --worker-zone instead.'),
          removed=False))
