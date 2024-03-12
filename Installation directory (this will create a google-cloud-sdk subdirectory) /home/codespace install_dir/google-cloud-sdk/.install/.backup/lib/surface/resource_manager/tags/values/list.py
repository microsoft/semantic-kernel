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
"""List command for the Resource Manager - Tag Values CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.resource_manager import tags
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import tag_arguments as arguments
from googlecloudsdk.command_lib.resource_manager import tag_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  r"""Lists TagValues under the specified parent resource.

  ## EXAMPLES

  To list all the TagValues under ``organizations/123/env'', run:

        $ {command} --parent=123/env
  """

  @staticmethod
  def Args(parser):
    arguments.AddParentArgToParser(
        parser,
        message=("Parent of the TagValue in either in the form of "
                 "tagKeys/{id} or {org_id}/{tagkey_short_name}"))
    parser.display_info.AddFormat("table(name:sort=1, short_name, description)")

  def Run(self, args):
    service = tags.TagValuesService()
    messages = tags.TagMessages()

    if args.parent.find("tagKeys/") == 0:
      tag_key = args.parent
    else:
      tag_key = tag_utils.GetNamespacedResource(
          args.parent, tag_utils.TAG_KEYS
      ).name

    list_request = messages.CloudresourcemanagerTagValuesListRequest(
        parent=tag_key, pageSize=args.page_size
    )
    return list_pager.YieldFromList(
        service,
        list_request,
        batch_size_attribute="pageSize",
        batch_size=args.page_size,
        field="tagValues",
    )
