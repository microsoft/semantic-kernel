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
"""Lists all backups associated with a given instance.

Lists all backups associated with a given instance and configuration
in the reverse chronological order of the enqueued time.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists all backups associated with the project or a given instance.

  Lists all backups associated with the project or a given Cloud SQL instance
  and configuration in the reverse chronological order of the enqueued time.
  """

  @staticmethod
  def Args(parser):
    flags.AddOptionalInstance(parser, True)
    flags.AddProjectLevelBackupEndpoint(parser)
    parser.display_info.AddFormat("""
      table(
        id,
        windowStartTime.iso(),
        error.code.yesno(no="-"):label=ERROR,
        status,
        instance
      )
    """)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Lists all backups associated with a given instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object that has the list of backup run resources if the command ran
      successfully.
    """

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    if args.project_level:
      # For project-level backups, this command updates the output table.
      # pylint:disable-next=protected-access
      args._GetParser().ai.display_info.AddFormat("""table(
            name,
            backupInterval.startTime.iso():label=WINDOW_START_TIME,
            error.errors[0].code.yesno(no="-"):label=ERROR,
            state:label=STATE,
            instance,
            type
          )""")
      return list_pager.YieldFromList(
          sql_client.backups,
          sql_messages.SqlBackupsListBackupsRequest(
              parent='projects/{0}'.format(
                  properties.VALUES.core.project.GetOrFail()
              ),
              filter=args.filter,
          ),
          limit=args.limit,
          batch_size=args.page_size,
          batch_size_attribute='pageSize',
          method='ListBackups',
          field='backups',
      )

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    return list_pager.YieldFromList(
        sql_client.backupRuns,
        sql_messages.SqlBackupRunsListRequest(
            project=instance_ref.project, instance=instance_ref.instance))
