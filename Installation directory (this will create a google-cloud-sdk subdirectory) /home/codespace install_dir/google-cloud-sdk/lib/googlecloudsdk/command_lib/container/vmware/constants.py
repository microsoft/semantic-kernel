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
"""Constants for Anthos clusters on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

VMWARE_CLUSTERS_FORMAT = """
table(
    name.segment(5):label=NAME,
    name.segment(3):label=LOCATION,
    onPremVersion:label=VERSION,
    adminClusterMembership.segment(5):label=ADMIN_CLUSTER,
    state:label=STATE
)
"""

VMWARE_NODEPOOLS_FORMAT = """
table(
  name.segment(7):label=NAME,
  name.segment(3):label=LOCATION,
  config.replicas,
  config.image:label=IMAGE,
  state
)
"""

VMWARE_ADMIN_CLUSTERS_FORMAT = """
table(
    name.segment(5):label=NAME,
    name.segment(3):label=LOCATION,
    onPremVersion:label=VERSION,
    platformConfig.platformVersion:label=PLATFORM_VERSION,
    state:label=STATE
)
"""

