# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Helpers for writing commands interacting with Cloud Dataflow snapshots.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers

from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

import six


def ArgsForSnapshotRef(parser):
  """Register flags for specifying a single Snapshot ID.

  Args:
    parser: The argparse.ArgParser to configure with snapshot arguments.
  """
  parser.add_argument(
      'snapshot',
      metavar='SNAPSHOT_ID',
      help='ID of the Cloud Dataflow snapshot.')
  parser.add_argument(
      '--region',
      required=True,
      metavar='REGION_ID',
      help='Region ID of the snapshot regional endpoint.')


def ArgsForSnapshotJobRef(parser):
  """Register flags for specifying a single Job ID.

  Args:
    parser: The argparse.ArgParser to configure with job-filtering arguments.
  """
  parser.add_argument(
      '--job-id',
      required=True,
      metavar='JOB_ID',
      help='The job ID to snapshot.')
  parser.add_argument(
      '--region',
      required=True,
      metavar='REGION_ID',
      help='The region ID of the snapshot and job\'s regional endpoint.')


def ArgsForListSnapshot(parser):
  """Register flags for listing Cloud Dataflow snapshots.

  Args:
    parser: The argparse.ArgParser to configure with job-filtering arguments.
  """
  parser.add_argument(
      '--job-id',
      required=False,
      metavar='JOB_ID',
      help='The job ID to use to filter the snapshots list.')
  parser.add_argument(
      '--region',
      required=True,
      metavar='REGION_ID',
      help='The region ID of the snapshot and job\'s regional endpoint.')


def ArgsForSnapshotTtl(parser):
  """Register flags for specifying a snapshot ttl.

  Args:
    parser: the argparse.ArgParser to configure with a ttl argument.
  """
  parser.add_argument(
      '--snapshot-ttl',
      default='7d',
      metavar='DURATION',
      type=arg_parsers.Duration(lower_bound='1h', upper_bound='30d'),
      help='Time to live for the snapshot.')


def ExtractSnapshotRef(args):
  """Extract the Snapshot Ref for a command. Used with ArgsForSnapshotRef.

  Args:
    args: The command line arguments.
  Returns:
    A Snapshot resource.
  """
  snapshot = args.snapshot
  region = dataflow_util.GetRegion(args)
  return resources.REGISTRY.Parse(
      snapshot,
      params={
          'projectId': properties.VALUES.core.project.GetOrFail,
          'location': region
      },
      collection='dataflow.projects.locations.snapshots')


def ExtractSnapshotJobRef(args):
  """Extract the Job Ref for a command. Used with ArgsForSnapshotJobRef.

  Args:
    args: The command line arguments.
  Returns:
    A Job resource.
  """
  job = args.job_id
  region = dataflow_util.GetRegion(args)
  return resources.REGISTRY.Parse(
      job,
      params={
          'projectId': properties.VALUES.core.project.GetOrFail,
          'location': region
      },
      collection='dataflow.projects.locations.jobs')


def ExtractSnapshotTtlDuration(args):
  """Extract the Duration string for the Snapshot ttl.

  Args:
    args: The command line arguments.
  Returns:
    A duration string for the snapshot ttl.
  """
  return six.text_type(args.snapshot_ttl) + 's'
