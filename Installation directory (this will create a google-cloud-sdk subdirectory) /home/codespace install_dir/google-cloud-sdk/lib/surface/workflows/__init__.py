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
"""The main command group for Cloud Workflows."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Workflows(base.Group):
  """Manage your Cloud Workflows resources."""

  category = base.TOOLS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190541902):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class WorkflowsBeta(base.Group):
  """Manage your Cloud Workflows resources."""

  category = base.TOOLS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190541902):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class WorkflowsAlpha(base.Group):
  """Manage your Cloud Workflows resources."""

  category = base.TOOLS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190541902):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
