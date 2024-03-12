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
"""Command to lookup a stream object for a datastream."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import stream_objects
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.datastream.objects import flags as so_flags
from googlecloudsdk.core import properties

DESCRIPTION = (
    'Lookup a stream object by its source object identifier (e.g. schema.table)'
)
EXAMPLES = """\
    To lookup an existing Mysql stream object:

        $ {command} --stream=my-stream --location=us-central1 --mysql-database=my-db --mysql-table=my-table

    To lookup an existing Oracle stream object:

        $ {command} --stream=my-stream --location=us-central1 --oracle-schema=my-schema --oracle-table=my-table

    To lookup an existing PostgreSQL stream object:

        $ {command} --stream=my-stream --location=us-central1 --postgresql-schema=my-schema --postgresql-table=my-table
   """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Lookup(base.Command):
  """Lookup a Datastream stream object."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddStreamObjectResourceArg(parser)

    object_identifier_parser = parser.add_group(required=True, mutex=True)
    so_flags.AddOracleObjectIdentifier(object_identifier_parser)
    so_flags.AddMysqlObjectIdentifier(object_identifier_parser)
    so_flags.AddPostgresqlObjectIdentifier(object_identifier_parser)

  def Run(self, args):
    """Lookup a Datastream stream object.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the looked up stream object if the lookup was
      successful.
    """
    project_id = properties.VALUES.core.project.Get(required=True)
    stream_id = args.CONCEPTS.stream.Parse().streamsId
    so_client = stream_objects.StreamObjectsClient()
    return so_client.Lookup(project_id, stream_id, args)
