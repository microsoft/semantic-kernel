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
"""Commands for creating, reading, and manipulating SSL policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class SslPolicies(base.Group):
  """List, create, delete and update Compute Engine SSL policies."""


SslPolicies.category = base.LOAD_BALANCING_CATEGORY

SslPolicies.detailed_help = {
    'DESCRIPTION': """
        List, create, delete and update Compute Engine SSL policies.

        For more information about SSL policies, see the
        [SSL policies documentation](https://cloud.google.com/load-balancing/docs/ssl-policies-concepts).

        See also: [SSL policies API](https://cloud.google.com/compute/docs/reference/rest/v1/sslPolicies).
    """,
}

