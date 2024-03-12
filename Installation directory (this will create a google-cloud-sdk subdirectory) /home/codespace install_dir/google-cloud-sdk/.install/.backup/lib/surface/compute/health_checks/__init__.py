# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Commands for reading and manipulating health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class HealthChecks(base.Group):
  """Read and manipulate health checks for load balanced instances."""


HealthChecks.category = base.LOAD_BALANCING_CATEGORY

HealthChecks.detailed_help = {
    'DESCRIPTION': """
        Read and manipulate health checks for load balanced instances.

        For more information about health checks, see the
        [health checks documentation](https://cloud.google.com/load-balancing/docs/health-check-concepts).

        See also: [Health checks API](https://cloud.google.com/compute/docs/reference/rest/v1/healthChecks)
        and [Regional health checks API](https://cloud.google.com/compute/docs/reference/rest/v1/regionHealthChecks).
    """,
}
