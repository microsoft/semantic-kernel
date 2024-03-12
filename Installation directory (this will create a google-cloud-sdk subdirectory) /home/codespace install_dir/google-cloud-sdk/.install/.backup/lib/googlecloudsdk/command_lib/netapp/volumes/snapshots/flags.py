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
"""Flags and helpers for the Cloud NetApp Files Volume Snapshots commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers


## Helper functions to add args / flags for Snapshots gcloud commands ##


def AddSnapshotVolumeArg(parser):
  concept_parsers.ConceptParser.ForResource(
      '--volume',
      flags.GetVolumeResourceSpec(positional=False),
      'The Volume to take a Snapshot of.',
      flag_name_overrides={'location': ''},
  ).AddToParser(parser)


## Helper functions to combine Snapshots args / flags for gcloud commands #


def AddSnapshotCreateArgs(parser):
  """Add args for creating a Snapshot."""
  concept_parsers.ConceptParser([
      flags.GetSnapshotPresentationSpec('The Snapshot to create.')
  ]).AddToParser(parser)
  AddSnapshotVolumeArg(parser)
  flags.AddResourceAsyncFlag(parser)
  flags.AddResourceDescriptionArg(parser, 'Snapshot')
  labels_util.AddCreateLabelsFlags(parser)


def AddSnapshotDeleteArgs(parser):
  """Add args for deleting a Snapshot."""
  concept_parsers.ConceptParser([
      flags.GetSnapshotPresentationSpec('The Snapshot to delete.')
  ]).AddToParser(parser)
  AddSnapshotVolumeArg(parser)
  flags.AddResourceAsyncFlag(parser)


def AddSnapshotUpdateArgs(parser):
  """Add args for updating a Snapshot."""
  concept_parsers.ConceptParser([
      flags.GetSnapshotPresentationSpec('The Snapshot to update.')
  ]).AddToParser(parser)
  AddSnapshotVolumeArg(parser)
  flags.AddResourceAsyncFlag(parser)
  flags.AddResourceDescriptionArg(parser, 'Snapshot')
  labels_util.AddUpdateLabelsFlags(parser)

