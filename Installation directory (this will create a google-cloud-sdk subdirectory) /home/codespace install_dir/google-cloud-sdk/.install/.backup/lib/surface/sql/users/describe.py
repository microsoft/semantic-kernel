# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Retrieves information about a Cloud SQL user in a given instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


def AddBaseArgs(parser):
  flags.AddInstance(parser)
  flags.AddUsername(parser)
  flags.AddHost(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Get(base.DescribeCommand):
  """Retrieves information about a Cloud SQL user in a given instance."""

  detailed_help = {
      'EXAMPLES':
          """\
          To fetch a user with name 'my-user' and optional host '%' in instance 'my-instance', run:

          $ {command} my-user --host=% --instance=my-instance

        """
  }

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)

  def Run(self, args):
    """Retrieves information about a Cloud SQL user in a given instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      SQL user resource.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    project_id = properties.VALUES.core.project.Get(required=True)

    return sql_client.users.Get(
        sql_messages.SqlUsersGetRequest(
            project=project_id,
            instance=args.instance,
            name=args.username,
            host=args.host))
