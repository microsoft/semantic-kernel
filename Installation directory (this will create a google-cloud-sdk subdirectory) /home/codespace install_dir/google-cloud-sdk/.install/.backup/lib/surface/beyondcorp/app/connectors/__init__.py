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

"""Commands for creating and manipulating connectors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Connectors(base.Group):
  """Create and manipulate beyondcorp connectors.

  A Beyondcorp connector represents an application facing component deployed
  proximal to and with direct access to the application instances. It is used to
  establish connectivity between the remote enterprise environment and Google
  Cloud Platform. It initiates connections to the applications and can proxy the
  data from users over the connection.
  """

  category = base.SECURITY_CATEGORY
