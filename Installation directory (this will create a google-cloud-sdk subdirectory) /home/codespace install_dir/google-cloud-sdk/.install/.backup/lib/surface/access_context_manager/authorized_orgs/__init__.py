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
"""The command group for the Access Context Manager authorized organizations description CLI.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class AuthorizedOrgsDescs(base.Group):
  """Manage Access Context Manager authorized organizations descriptions.

   An authorized organizations description describes a list of organizations (1)
   that have been authorized to use certain asset (for example, device) data
   owned by different organizations at the enforcement points, or (2) with
   certain asset (for example, device) have been authorized to access the
   resources in another organization at the enforcement points.
  """
