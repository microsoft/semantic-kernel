# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a new Assured Workloads environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.base import ReleaseTrack
from googlecloudsdk.command_lib.assured import create_workload
from googlecloudsdk.command_lib.assured import flags


@base.ReleaseTracks(ReleaseTrack.GA)
class GaCreate(create_workload.CreateWorkload):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadFlags(parser, ReleaseTrack.GA)


@base.ReleaseTracks(ReleaseTrack.BETA)
class BetaCreate(create_workload.CreateWorkload):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadFlags(parser, ReleaseTrack.BETA)


@base.ReleaseTracks(ReleaseTrack.ALPHA)
class AlphaCreate(create_workload.CreateWorkload):
  """Create a new Assured Workloads environment."""

  @staticmethod
  def Args(parser):
    flags.AddCreateWorkloadFlags(parser, ReleaseTrack.ALPHA)
