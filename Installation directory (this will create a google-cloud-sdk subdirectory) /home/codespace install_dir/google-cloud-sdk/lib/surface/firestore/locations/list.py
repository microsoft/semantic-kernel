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
"""The gcloud Firestore locations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import locations
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class List(base.ListCommand):
  """List locations available to Google Cloud Firestore.

  ## EXAMPLES

  To list all Firestore locations with table.

      $ {command} --format="table(locationId, displayName)"

  To list Firestore locations with a filter.

      $ {command} --filter="locationId:us-west1"
  """

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return locations.ListLocations(project)
