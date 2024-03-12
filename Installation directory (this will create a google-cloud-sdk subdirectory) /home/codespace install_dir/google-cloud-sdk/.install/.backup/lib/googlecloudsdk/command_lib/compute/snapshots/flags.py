# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute snapshots commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


def MakeSnapshotArg(plural=False):
  return compute_flags.ResourceArgument(
      resource_name='snapshot',
      name='snapshot_name',
      completer=compute_completers.RoutesCompleter,
      plural=plural,
      global_collection='compute.snapshots',
  )


def AddChainArg(parser):
  parser.add_argument(
      '--chain-name',
      help=(
          """Create the new snapshot in the snapshot chain labeled with the specified name.
          The chain name must be 1-63 characters long and comply with RFC1035.
          Use this flag only if you are an advanced service owner who needs
          to create separate snapshot chains, for example, for chargeback tracking.
          When you describe your snapshot resource, this field is visible only
          if it has a non-empty value."""
      ),
  )


def AddSourceDiskCsekKey(parser):
  parser.add_argument(
      '--source-disk-key-file',
      metavar='FILE',
      help="""
      Path to the customer-supplied encryption key of the source disk.
      Required if the source disk is protected by a customer-supplied
      encryption key.
      """,
  )


def AddSourceInstantSnapshotCsekKey(parser):
  parser.add_argument(
      '--source-instant-snapshot-key-file',
      metavar='FILE',
      help="""
      Path to the customer-supplied encryption key of the source instant snapshot.
      Required if the source instant snapshot is protected by a customer-supplied
      encryption key.
      """,
  )


def AddSnapshotType(parser):
  snapshot_type_choices = sorted(['STANDARD', 'ARCHIVE'])
  parser.add_argument(
      '--snapshot-type',
      choices=snapshot_type_choices,
      help="""
              Type of snapshot. If a snapshot type is not specified, a STANDARD snapshot will be created.
           """,
  )


def AddMaxRetentionDays(parser):
  parser.add_argument(
      '--max-retention-days',
      help="""
    Days for snapshot to live before being automatically deleted. If unspecified, the snapshot will live until manually deleted.
    """,
  )


SOURCE_DISK_ARG = compute_flags.ResourceArgument(
    resource_name='source disk',
    name='--source-disk',
    completer=compute_completers.DisksCompleter,
    short_help="""
    Source disk used to create the snapshot. To create a snapshot from a source
    disk in a different project, specify the full path to the source disk.
    For example:
    https://www.googleapis.com/compute/v1/projects/MY-PROJECT/zones/MY-ZONE/disks/MY-DISK
    """,
    zonal_collection='compute.disks',
    regional_collection='compute.regionDisks',
    required=False,
)

SOURCE_DISK_FOR_RECOVERY_CHECKPOINT_ARG = compute_flags.ResourceArgument(
    resource_name='source disk for recovery checkpoint',
    name='--source-disk-for-recovery-checkpoint',
    completer=compute_completers.DisksCompleter,
    short_help="""
    Source disk whose recovery checkpoint used to create the snapshot. To create a snapshot from the recovery
    checkpoint of a source disk in a different project, specify the full path to the source disk.
    For example:
    projects/MY-PROJECT/regions/MY-REGION/disks/MY-DISK
    """,
    regional_collection='compute.regionDisks',
    plural=False,
    required=False,
    scope_flags_usage=compute_flags.ScopeFlagsUsage.GENERATE_DEDICATED_SCOPE_FLAGS,
)

SOURCE_INSTANT_SNAPSHOT_ARG = compute_flags.ResourceArgument(
    resource_name='source instant snapshot',
    name='--source-instant-snapshot',
    completer=compute_completers.InstantSnapshotsCompleter,
    short_help="""
    The name or URL of the source instant snapshot. If the name is provided, the instant snapshot's zone
or region must be specified with --source-instant-snapshot-zone or --source-instant-snapshot-region accordingly.
    To create a snapshot from an instant snapshot in a different project, specify the full path to the instant snapshot.
    If the URL is provided, format should be:
    https://www.googleapis.com/compute/v1/projects/MY-PROJECT/zones/MY-ZONE/instantSnapshots/MY-INSTANT-SNAPSHOT
    """,
    zonal_collection='compute.instantSnapshots',
    regional_collection='compute.regionInstantSnapshots',
    required=False,
)
