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
"""Commands for creating and manipulating client connector services (Deprecated)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ClientConnectorServices(base.Group):
  """Create and manipulate BeyondCorp client connector services.

  The client connector service is used to define a common configuration for a
  group of client gateways. Client gateways refer to the client connector
  service and are used to control the regions where you want to manage user
  traffic.
    The gateways communicate with the BeyondCorp Enterprise enforcement system
  to enforce context-aware checks. The BeyondCorp Enterprise enforcement system
  uses Identity-Aware Proxy and Access Context Manager, a flexible BeyondCorp
  Enterprise zero trust policy engine.
  """
