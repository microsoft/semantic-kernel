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

"""The command group for the Cloud IoT CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.Deprecate(
    is_removed=False,
    warning=(
        'This command is deprecated. Google Cloud IoT Core has been retired.'
    ),
    error=(
        'This command has been removed. Google Cloud IoT Core has been retired.'
    ),
)
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Iot(base.Group):
  """Manage Cloud IoT resources.

  Commands for managing Google Cloud IoT resources.
  """

  category = base.INTERNET_OF_THINGS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190535196):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
