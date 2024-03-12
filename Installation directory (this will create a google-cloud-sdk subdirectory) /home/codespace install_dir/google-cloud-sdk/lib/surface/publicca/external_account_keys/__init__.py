# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""The command group for external account key resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class ExternalAccountKeys(base.Group):
  """Create ACME external account binding keys.

  {command} lets you create an external account key associated with
  Google Trust Services' publicly trusted certificate authority.

  The external account key will be associated with the Cloud project and
  it may be bound to an Automatic Certificate Management Environment (ACME)
  account following RFC 8555.

  See https://tools.ietf.org/html/rfc8555#section-7.3.4 for more details.
  """
