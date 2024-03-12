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
"""Lists instances in a given project.

Lists instances in a given project in the alphabetical order of the
instance name.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import instances
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags


def _GetUriFromResource(resource):
  """Returns the URI for resource."""
  client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
  return client.resource_parser.Create(
      'sql.instances', project=resource.project, instance=resource.name
  ).SelfLink()


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists Cloud SQL instances in a given project.

  Lists Cloud SQL instances in a given project in the alphabetical
  order of the instance name.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(flags.GetInstanceListFormat())
    parser.display_info.AddUriFunc(_GetUriFromResource)
    flags.AddShowEdition(parser)
    flags.AddShowSqlNetworkArchitecture(parser)

  def Run(self, args):
    """Lists Cloud SQL instances in a given project.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      SQL instance resource iterator.
    """
    if args.show_edition:
      args.GetDisplayInfo().AddFormat(flags.GetInstanceListFormatEdition())
    if args.show_sql_network_architecture:
      args.GetDisplayInfo().AddFormat(
          flags.GetInstanceListFormatForNetworkArchitectureUpgrade()
      )
    return instances.InstancesV1Beta4.GetDatabaseInstances(
        limit=args.limit, batch_size=args.page_size
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(base.ListCommand):
  """Lists Cloud SQL instances in a given project.

  Lists Cloud SQL instances in a given project in the alphabetical
  order of the instance name.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    parser.display_info.AddFormat(flags.GetInstanceListFormat())
    parser.display_info.AddUriFunc(_GetUriFromResource)
    flags.AddShowEdition(parser)
    flags.AddShowSqlNetworkArchitecture(parser)

  def Run(self, args):
    """Lists Cloud SQL instances in a given project.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      SQL instance resource iterator.
    """
    if args.show_edition:
      args.GetDisplayInfo().AddFormat(flags.GetInstanceListFormatEdition())
    if args.show_sql_network_architecture:
      args.GetDisplayInfo().AddFormat(
          flags.GetInstanceListFormatForNetworkArchitectureUpgrade()
      )
    return instances.InstancesV1Beta4.GetDatabaseInstances(
        limit=args.limit, batch_size=args.page_size
    )
