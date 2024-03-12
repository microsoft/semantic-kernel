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
"""The super-group for the organizations CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Organizations(base.Group):
  """Create and manage Google Cloud Platform Organizations.

  The {command} group lets you create and manage Cloud Organizations.
  Google Cloud Platform resources form a hierarchy with Organizations at the
  root. Organizations contain projects, and Projects contain the remaining
  Google Cloud Platform resources.

  More information on the Cloud Platform Resource Hierarchy and the Organization
  resource can be found here:
  https://cloud.google.com/resource-manager/docs/creating-managing-organization
  and detailed documentation on creating and managing organizations can be found
  here:
  https://cloud.google.com/resource-manager/docs/creating-managing-organization
  """

  category = base.MANAGEMENT_TOOLS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190538570):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
