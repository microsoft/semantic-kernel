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
"""Command for spanner samples init."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.api_lib.spanner import instances
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.spanner import ddl_parser
from googlecloudsdk.command_lib.spanner import samples
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import files


def check_instance(instance_id):
  """Raise if the given instance doesn't exist."""
  try:
    instances.Get(instance_id)
  except apitools_exceptions.HttpNotFoundError:
    raise ValueError(
        textwrap.dedent("""\
        Instance '{instance_id}' does not exist. Create it with:

        $ gcloud spanner instances create {instance_id}
        """.format(instance_id=instance_id)))


def download_sample_files(appname):
  """Download schema and binaries for the given sample app.

  If the schema and all binaries exist already, skip download. If any file
  doesn't exist, download them all.

  Args:
    appname: The name of the sample app, should exist in samples.APP_NAMES
  """
  storage_client = storage_api.StorageClient()
  bucket_ref = storage_util.BucketReference.FromUrl(samples.GCS_BUCKET)

  # Get the GCS object ref and local path for each file
  gcs_to_local = [(storage_util.ObjectReference.FromBucketRef(
      bucket_ref, samples.get_gcs_schema_name(appname)),
                   samples.get_local_schema_path(appname))]
  gcs_bin_msgs = storage_client.ListBucket(
      bucket_ref, prefix=samples.get_gcs_bin_prefix(appname))
  bin_path = samples.get_local_bin_path(appname)
  for gcs_ref in gcs_bin_msgs:
    gcs_ref = storage_util.ObjectReference.FromMessage(gcs_ref)
    local_path = os.path.join(bin_path, gcs_ref.name.split('/')[-1])
    gcs_to_local.append((gcs_ref, local_path))

  # Download all files again if any file is missing
  if any(not os.path.exists(file_path) for _, file_path in gcs_to_local):
    log.status.Print('Downloading files for the {} sample app'.format(appname))
    for gcs_ref, local_path in gcs_to_local:
      log.status.Print('Downloading {}'.format(local_path))
      local_dir = os.path.split(local_path)[0]
      if not os.path.exists(local_dir):
        files.MakeDir(local_dir)
      storage_client.CopyFileFromGCS(gcs_ref, local_path, overwrite=True)


def _create_db_op(instance_ref, database_id, statements, database_dialect):
  """Wrapper over databases.Create with error handling."""
  try:
    return databases.Create(
        instance_ref,
        database_id,
        statements,
        database_dialect=database_dialect)
  except apitools_exceptions.HttpConflictError:
    raise ValueError(
        textwrap.dedent("""\
        Database '{database_id}' exists already. Delete it with:

        $ gcloud spanner databases delete {database_id} --instance={instance_id}
        """.format(
            database_id=database_id, instance_id=instance_ref.instancesId)))
  except apitools_exceptions.HttpError as ex:
    raise ValueError(json.loads(ex.content)['error']['message'])
  except Exception:  # pylint: disable=broad-except
    raise ValueError("Failed to create database '{}'.".format(database_id))


def check_create_db(appname, instance_ref, database_id):
  """Create the DB if it doesn't exist already, raise otherwise."""
  schema_file = samples.get_local_schema_path(appname)
  database_dialect = samples.get_database_dialect(appname)

  schema = files.ReadFileContents(schema_file)
  # Special case for POSTGRESQL dialect:
  # a. CreateDatabase does not support additional_statements. Instead a
  #    separate call to UpdateDDL is used.
  # b. ddl_parser only supports GSQL; instead remove comment lines, then
  #    split on ';'.
  if database_dialect == databases.DATABASE_DIALECT_POSTGRESQL:
    create_ddl = []
    # Remove comments
    schema = '\n'.join(
        [line for line in schema.split('\n') if not line.startswith('--')])
    # TODO(b/195711543): This would be incorrect if ';' is inside strings
    # and / or comments.
    update_ddl = [stmt for stmt in schema.split(';') if stmt]
  else:
    create_ddl = ddl_parser.PreprocessDDLWithParser(schema)
    update_ddl = []

  create_op = _create_db_op(instance_ref, database_id, create_ddl,
                            database_dialect)
  database_operations.Await(create_op,
                            "Creating database '{}'".format(database_id))
  if update_ddl:
    database_ref = resources.REGISTRY.Parse(
        database_id,
        params={
            'instancesId': instance_ref.instancesId,
            'projectsId': instance_ref.projectsId,
        },
        collection='spanner.projects.instances.databases')
    update_op = databases.UpdateDdl(database_ref, update_ddl)
    database_operations.Await(update_op,
                              "Updating database '{}'".format(database_id))


class Init(base.Command):
  """Initialize a Cloud Spanner sample app.

  This command creates a Cloud Spanner database in the given instance for the
  sample app and loads any initial data required by the application.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To initialize the 'finance' sample app using instance
          'my-instance', run:

          $ {command} finance --instance-id=my-instance
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument('appname', help='The sample app name, e.g. "finance".')
    parser.add_argument(
        '--instance-id',
        required=True,
        type=str,
        help='The Cloud Spanner instance ID for the sample app.')
    parser.add_argument(
        '--database-id',
        type=str,
        help='ID of the new Cloud Spanner database to create for the sample '
        'app.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    appname = args.appname
    try:
      samples.check_appname(appname)
    except ValueError as ex:
      raise calliope_exceptions.BadArgumentException('APPNAME', ex)

    instance_id = args.instance_id
    instance_ref = resources.REGISTRY.Parse(
        instance_id,
        params={
            'projectsId': properties.VALUES.core.project.GetOrFail,
        },
        collection='spanner.projects.instances')

    if args.database_id is not None:
      database_id = args.database_id
    else:
      database_id = samples.get_db_id_for_app(appname)

    # Check that the instance exists
    log.status.Print("Checking instance '{}'".format(instance_id))
    try:
      check_instance(instance_id)
    except ValueError as ex:
      raise calliope_exceptions.BadArgumentException('--instance-id', ex)

    # Download any missing sample app binaries from GCS, including the schema
    # file we need to create the DB
    download_sample_files(appname)

    # Create the sample app DB
    log.status.Print(
        "Initializing database '{database_id}' for sample app '{appname}'"
        .format(database_id=database_id, appname=appname))
    try:
      check_create_db(appname, instance_ref, database_id)
    except ValueError as ex:
      raise calliope_exceptions.BadArgumentException('--database-id', ex)

    backend_args = '{appname} --instance-id={instance_id}'.format(
        appname=appname, instance_id=instance_id)
    if args.database_id is not None:
      backend_args += ' --database-id {}'.format(database_id)
    return textwrap.dedent("""\
        Initialization done. Next, start the backend gRPC service with:

        $ gcloud spanner samples backend {}
        """.format(backend_args))
