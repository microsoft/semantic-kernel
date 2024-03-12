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
"""Commands for reading and manipulating interconnects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Interconnects(base.Group):
  """Read and manipulate Compute Engine interconnects."""


Interconnects.category = base.NETWORKING_CATEGORY

Interconnects.detailed_help = {
    'DESCRIPTION': """
        Read and manipulate Cloud Interconnect connections.

        For more information about Cloud Interconnect, see the
        [Cloud Interconnect documentation](https://cloud.google.com//network-connectivity/docs/interconnect/concepts/overview).

        See also: [Interconnects API](https://cloud.google.com/compute/docs/reference/rest/v1/interconnects).
    """,
}
