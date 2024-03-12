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
"""Changes a user's password in a given instance.

Changes a user's password in a given instance with specified username and host.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import users_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import users
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


def AddBaseArgs(parser):
  flags.AddInstance(parser)
  flags.AddUsername(parser)
  flags.AddHost(parser)
  password_group = parser.add_mutually_exclusive_group()
  flags.AddPassword(password_group)
  flags.AddPromptForPassword(password_group)
  dual_password_group = parser.add_mutually_exclusive_group()
  flags.AddUserDiscardDualPassword(dual_password_group)
  flags.AddUserRetainPassword(dual_password_group)


def AddBetaArgs(parser):
  del parser  # unused
  pass


def AddAlphaArgs(parser):
  AddBetaArgs(parser)
  pass


def RunBaseSetPasswordCommand(args):
  """Changes a user's password in a given instance.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.

  Returns:
    SQL user resource iterator.
  """
  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client

  if args.prompt_for_password:
    args.password = console_io.PromptPassword('New Password: ')

  users.ValidateSetPasswordRequest(args)

  sql_messages = client.sql_messages
  instance_ref = client.resource_parser.Parse(
      args.instance,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')

  dual_password_type = users.ParseDualPasswordType(sql_messages, args)
  request = users_util.CreateSetPasswordRequest(sql_messages,
                                                args,
                                                dual_password_type,
                                                instance_ref.project)
  result_operation = sql_client.users.Update(request)
  operation_ref = client.resource_parser.Create(
      'sql.operations',
      operation=result_operation.name,
      project=instance_ref.project)
  if args.async_:
    return sql_client.operations.Get(
        sql_messages.SqlOperationsGetRequest(
            project=operation_ref.project, operation=operation_ref.operation))
  operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                'Updating Cloud SQL user')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Changes a user's password in a given instance.

  Changes a user's password in a given instance with specified username and
  host.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    return RunBaseSetPasswordCommand(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Changes a user's password in a given instance.

  Changes a user's password in a given instance with specified username and
  host.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)
    AddBetaArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    return RunBaseSetPasswordCommand(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Changes a user's password in a given instance.

  Changes a user's password in a given instance with specified username and
  host.
  """

  @staticmethod
  def Args(parser):
    AddBaseArgs(parser)
    AddAlphaArgs(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    return RunBaseSetPasswordCommand(args)
