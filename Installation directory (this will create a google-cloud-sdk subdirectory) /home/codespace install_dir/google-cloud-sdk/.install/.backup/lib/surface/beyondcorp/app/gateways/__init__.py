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
"""The super-group for the beyondcorp application CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Gateways(base.Group):
  """Manages appconnector gateways.

  A BeyondCorp AppGateway resource represents a BeyondCorp protected
  AppGateway to a remote application. It creates all the necessary google cloud
  platform components needed for creating a BeyondCorp protected AppGateway.
  Multiple connectors can be authorised for a single AppGateway
  """

  category = base.SECURITY_CATEGORY

  def Filter(self, context, args):
    base.DisableUserProjectQuota()
