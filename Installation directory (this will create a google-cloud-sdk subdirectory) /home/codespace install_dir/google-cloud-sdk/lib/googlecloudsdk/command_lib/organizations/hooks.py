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
"""Declarative hooks for Cloud Identity Groups CLI."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.organizations import org_utils


# request hooks
def SetOrganization(unused_ref, args, request):
  """Set organization ID to request.organizationId.

  Args:
    unused_ref: A string representing the operation reference. Unused and may
      be None.
    args: The argparse namespace.
    request: The request to modify.

  Returns:
    The updated request.
  """

  org_id = org_utils.GetOrganizationId(args.organization)

  if org_id:
    request.organizationsId = org_id
    return request
  else:
    raise org_utils.UnknownOrganizationError(args.organization)
