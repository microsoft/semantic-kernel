# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Commands for reading and manipulating HTTPS health checks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class HttpsHealthChecks(base.Group):
  """Read and manipulate HTTPS health checks for load balanced instances."""


HttpsHealthChecks.category = base.LOAD_BALANCING_CATEGORY

HttpsHealthChecks.detailed_help = {
    'DESCRIPTION': """
        Read and manipulate legacy health checks that use the HTTPS protocol.

        For more information about legacy health checks, see the
        [HTTPS health checks documentation](https://cloud.google.com/load-balancing/docs/health-checks#legacy-health-checks)

        See also: [HTTPS health checks API](https://cloud.google.com/compute/docs/reference/rest/v1/httpsHealthChecks).
    """,
}
