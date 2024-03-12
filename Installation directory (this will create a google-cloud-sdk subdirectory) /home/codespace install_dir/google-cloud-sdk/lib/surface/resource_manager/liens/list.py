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
"""Command to list all lien IDs associated for the specified project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.resource_manager import error
from googlecloudsdk.api_lib.resource_manager import liens
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List liens associated with the specified project.

  List all liens which are associated with the specified project.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""
          table(
            name.segment(),
            origin,
            reason
          )
        """)

  @error.YieldErrorDetails
  def Run(self, args):
    """Run the list command."""
    parent = 'projects/' + properties.VALUES.core.project.Get(required=True)
    return list_pager.YieldFromList(
        liens.LiensService(),
        liens.LiensMessages().CloudresourcemanagerLiensListRequest(
            parent=parent),
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='liens')
