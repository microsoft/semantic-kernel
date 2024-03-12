# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Replaces a user's password policy in a given instance.

Replaces a user's password policy in a given instance with specified policy.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.command_lib.sql import users
from googlecloudsdk.core import properties


DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        """\
          To replace the password policy with 2 minutes password
          expiration time for ``my-user'' in instance ``prod-instance'', run:

            $ {command} my-user --instance=prod-instance --password-policy-password-expiration-duration=2m

          To clear the existing password policy of ``my-user'' in instance
          ``prod-instance'', run:

            $ {command} my-user --instance=prod-instance --clear-password-policy
          """,
}


def AddBaseArgs(parser):
  """Args is called by calliope to gather arguments for this command.

  Args:
    parser: An argparse parser that you can use it to add arguments that go on
      the command line after this command. Positional arguments are allowed.
  """
  flags.AddInstance(parser)
  flags.AddUsername(parser)
  flags.AddHost(parser)
  flags.AddPasswordPolicyAllowedFailedAttempts(parser)
  flags.AddPasswordPolicyPasswordExpirationDuration(parser)
  flags.AddPasswordPolicyEnableFailedAttemptsCheck(parser)
  flags.AddPasswordPolicyEnablePasswordVerification(parser)
  flags.AddPasswordPolicyClearPasswordPolicy(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  parser.display_info.AddCacheUpdater(None)


def AddBetaArgs(parser):
  del parser  # Unused.
  pass


def AddAlphaArgs(parser):
  del parser  # Unused.
  pass


def RunBaseSetPasswordCommand(args):
  """Changes a user's password in a given instance.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked
      with.

  Returns:
    SQL user resource iterator.
  """
  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  instance_ref = client.resource_parser.Parse(
      args.instance,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')
  operation_ref = None

  user = sql_client.users.Get(
      sql_messages.SqlUsersGetRequest(
          project=instance_ref.project,
          instance=args.instance,
          name=args.username,
          host=args.host))

  password_policy = users.CreatePasswordPolicyFromArgs(
      sql_messages, user.passwordPolicy, args)

  result_operation = sql_client.users.Update(
      sql_messages.SqlUsersUpdateRequest(
          project=instance_ref.project,
          instance=args.instance,
          name=args.username,
          host=args.host,
          user=sql_messages.User(
              project=instance_ref.project,
              instance=args.instance,
              name=args.username,
              host=args.host,
              passwordPolicy=password_policy)))
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
class SetPasswordPolicy(base.UpdateCommand):
  """Replaces a user's password policy in a given instance.

  Replaces a user's password policy in a given instance with a specified
  username and host.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    AddBaseArgs(parser)

  def Run(self, args):
    RunBaseSetPasswordCommand(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetPasswordPolicyBeta(base.UpdateCommand):
  """Replaces a user's password policy in a given instance.

  Replaces a user's password policy in a given instance with a specified
  username and host.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    AddBetaArgs(parser)
    AddBaseArgs(parser)

  def Run(self, args):
    RunBaseSetPasswordCommand(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetPasswordPolicyAlpha(base.UpdateCommand):
  """Replaces a user's password policy in a given instance.

  Replaces a user's password policy in a given instance with a specified
  username and host.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    AddAlphaArgs(parser)
    AddBetaArgs(parser)
    AddBaseArgs(parser)

  def Run(self, args):
    RunBaseSetPasswordCommand(args)
