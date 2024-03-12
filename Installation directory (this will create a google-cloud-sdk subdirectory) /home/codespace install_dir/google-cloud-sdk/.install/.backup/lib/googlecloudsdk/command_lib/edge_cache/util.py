# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utils for Edge Cache commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import resources


def SetLocationAsGlobal():
  """Set default location to global."""
  return 'global'


def SetFailoverOriginRelativeName(unused_ref, args, request):
  """Parse the provided failover origin to a relative name.

  Relative name includes defaults (or overridden values) for project & location.
  Location defaults to 'global'.

  Args:
    unused_ref: A string representing the operation reference. Unused and may be
      None.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.
  """

  # request.parent has the form 'projects/<project>/locations/<location>'
  project = request.parent.split('/')[1]

  request.edgeCacheOrigin.failoverOrigin = resources.REGISTRY.Parse(
      args.failover_origin,
      params={
          'projectsId': args.project or project,
          'locationsId': args.location or SetLocationAsGlobal(),
          'edgeCacheOriginsId': request.edgeCacheOriginId
      },
      collection='networkservices.projects.locations.edgeCacheOrigins'
  ).RelativeName()
  return request
