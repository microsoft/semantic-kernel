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
"""Lists users in a given project.

Lists users in a given project in the alphabetical order of the user name.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


def AddBaseArgs(parser):
  flags.AddInstance(parser)
  parser.display_info.AddCacheUpdater(flags.UserCompleter)


def RunBaseListCommand(args, release_track):
  """Lists Cloud SQL users in a given instance.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    release_track: base.ReleaseTrack, the release track that this was run under.

  Returns:
    SQL user resource iterator.
  """
  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  project_id = properties.VALUES.core.project.Get(required=True)

  users = sql_client.users.List(
      sql_messages.SqlUsersListRequest(
          project=project_id, instance=args.instance)).items

  # We will not display dual passwords if no user in the instance
  # has information about this field. This an implicit way of saying that we
  # will only show dual password type on MySQL 8.0, as no other instance type
  # will have dual password information.
  dual_password_type = ""
  for user in users:
    if user.dualPasswordType:
      dual_password_type = "dualPasswordType,"
    policy = user.passwordPolicy
    if not policy:
      continue
    # Don't display
    policy.enableFailedAttemptsCheck = None

  # Dual Password types is exposed in all release tracks, but we will not
  # expose the column early to customers, because returning the Dual Password
  # status is gated by a flag upstream.
  if release_track == base.ReleaseTrack.GA:
    # Because there are tests running against Python 3.5, I can't use f-Strings.
    args.GetDisplayInfo().AddFormat("""
      table(
        name.yesno(no='(anonymous)'),
        host,
        type.yesno(no='BUILT_IN'),
        {dualPasswordType}
        passwordPolicy
      )
    """.format(dualPasswordType=dual_password_type))
  else:
    args.GetDisplayInfo().AddFormat("""
      table(
        name.yesno(no='(anonymous)'),
        host,
        type.yesno(no='BUILT_IN'),
        {dualPasswordType}
        iamEmail,
        passwordPolicy
      )
    """.format(dualPasswordType=dual_password_type))

  return users


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists Cloud SQL users in a given instance.

  Lists Cloud SQL users in a given instance in the alphabetical
  order of the user name.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)

  def Run(self, args):
    return RunBaseListCommand(args, self.ReleaseTrack())


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """Lists Cloud SQL users in a given instance.

  Lists Cloud SQL users in a given instance in the alphabetical
  order of the user name.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(ListBeta):
  """Lists Cloud SQL users in a given instance.

  Lists Cloud SQL users in a given instance in the alphabetical
  order of the user name.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)
