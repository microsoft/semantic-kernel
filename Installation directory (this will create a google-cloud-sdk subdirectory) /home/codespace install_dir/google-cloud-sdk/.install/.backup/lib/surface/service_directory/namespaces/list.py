# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""`gcloud service-directory namespaces list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import namespaces
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import resource_args


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists namespaces."""

  detailed_help = {
      'EXAMPLES':
          """\
          To list Service Directory namespaces, run:

            $ {command} --location=us-east1
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to list.', positional=False)
    base.LIMIT_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = namespaces.NamespacesClient(self.GetReleaseTrack())
    location_ref = args.CONCEPTS.location.Parse()
    order_by = common_args.ParseSortByArg(args.sort_by)

    return client.List(location_ref, args.filter, order_by, args.page_size)

  def GetReleaseTrack(self):
    return base.ReleaseTrack.GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListBeta(List):
  """Lists namespaces."""

  def GetReleaseTrack(self):
    return base.ReleaseTrack.BETA
