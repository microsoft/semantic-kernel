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
"""Retrieves information about a backup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Retrieves information about a backup.

  Retrieves information about a backup.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddBackupId(parser)
    flags.AddOptionalInstance(parser)
    flags.AddProjectLevelBackupEndpoint(parser)

  def _GetById(self, backup_id, instance_name, project_level):
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    if project_level:
      request = sql_messages.SqlBackupsGetBackupRequest(name=backup_id)
      return sql_client.backups.GetBackup(request)

    instance_ref = client.resource_parser.Parse(
        instance_name,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances',
    )

    request = sql_messages.SqlBackupRunsGetRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        id=int(backup_id),
    )
    return sql_client.backupRuns.Get(request)

  def Run(self, args):
    """Retrieves information about a backup.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object that has the backup run resource if the command ran
      successfully.
    """

    if args.instance:
      validate.ValidateInstanceName(args.instance)

    return self._GetById(args.id, args.instance, args.project_level)
