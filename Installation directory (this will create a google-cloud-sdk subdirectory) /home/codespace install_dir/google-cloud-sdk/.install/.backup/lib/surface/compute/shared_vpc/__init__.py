# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Commands for configuring shared VPC."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Xpn(base.Group):
  """Configure shared VPC."""


Xpn.category = base.NETWORKING_CATEGORY

Xpn.detailed_help = {
    'DESCRIPTION': """
        Configure Shared VPC configurations.

        For more information about Shared VPC, see the
        [Shared VPC documentation](https://cloud.google.com/vpc/docs/shared-vpc/).
    """,
}

