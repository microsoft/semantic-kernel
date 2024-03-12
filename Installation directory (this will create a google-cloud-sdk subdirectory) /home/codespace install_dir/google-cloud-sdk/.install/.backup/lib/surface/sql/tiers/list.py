# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Lists all available service tiers for Google Cloud SQL."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


class _BaseList(object):
  """Lists all available service tiers for Google Cloud SQL."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.TIERS_FORMAT)
    flags.AddShowEdition(parser)

  def Run(self, args):
    """Lists all available service tiers for Google Cloud SQL.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object that has the list of tier resources if the command ran
      successfully.
    """
    if args.show_edition:
      args.GetDisplayInfo().AddFormat(flags.TIERS_FORMAT_EDITION)

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    result = sql_client.tiers.List(
        sql_messages.SqlTiersListRequest(
            project=properties.VALUES.core.project.Get(required=True)))
    return iter(result.items)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class List(_BaseList, base.ListCommand):
  """Lists all available service tiers for Google Cloud SQL."""
