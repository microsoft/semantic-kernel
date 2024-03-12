# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The simulator command group for the IAM CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.Hidden
class SimulatorBeta(base.Group):
  """Understand access permission impacts before IAM policy change deployment.

  Commands for analyzing access permission impacts before proposed IAM policy
  changes are deployed.
  """

  def Filter(self, context, args):
    """Enables User-Project override for this surface."""
    base.EnableUserProjectQuota()


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SimulatorGA(base.Group):
  """Understand how an IAM policy change could impact access before deploying the change.
  """

  def Filter(self, context, args):
    """Enables User-Project override for this surface."""
    base.EnableUserProjectQuota()
