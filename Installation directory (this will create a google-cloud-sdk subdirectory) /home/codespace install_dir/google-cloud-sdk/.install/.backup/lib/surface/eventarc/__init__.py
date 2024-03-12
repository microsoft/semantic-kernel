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
"""The main command group for Eventarc."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Eventarc(base.Group):
  """Manage Eventarc resources."""

  category = base.SERVERLESS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190533987):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args


@base.Deprecate(
    is_removed=False,
    warning='This command is deprecated. Please use `gcloud eventarc` instead.',
    error=(
        'This command has been removed. Please use `gcloud eventarc` instead.'
    ),
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class EventarcBeta(Eventarc):
  """Manage Eventarc resources."""
