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
"""Commands for managing Compute Engine commitments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Commitments(base.Group):
  """Manage Compute Engine commitments."""


Commitments.category = base.INSTANCES_CATEGORY

Commitments.detailed_help = {
    'DESCRIPTION': """
        Manage Compute Engine commitments.

        For more information about commitments, see the
        [commitments documentation](https://cloud.google.com/compute/docs/instances/signing-up-committed-use-discounts).

        See also: [Commitments API](https://cloud.google.com/compute/docs/reference/rest/v1/regionCommitments).
    """,
}

