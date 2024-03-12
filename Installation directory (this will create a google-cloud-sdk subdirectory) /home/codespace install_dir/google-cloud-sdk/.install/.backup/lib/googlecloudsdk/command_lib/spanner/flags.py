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
"""Provides common arguments for the Spanner command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from argcomplete.completers import FilesCompleter
from cloudsdk.google.protobuf import descriptor_pb2
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import ddl_parser
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core.util import files


class BackupCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BackupCompleter, self).__init__(
        collection='spanner.projects.instances.backups',
        list_command='spanner backups list --uri',
        flags=['instance'],
        **kwargs)


class DatabaseCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DatabaseCompleter, self).__init__(
        collection='spanner.projects.instances.databases',
        list_command='spanner databases list --uri',
        flags=['instance'],
        **kwargs)


class DatabaseOperationCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DatabaseOperationCompleter, self).__init__(
        collection='spanner.projects.instances.databases.operations',
        list_command='spanner operations list --uri',
        flags=['instance'],
        **kwargs)


class InstanceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceCompleter, self).__init__(
        collection='spanner.projects.instances',
        list_command='spanner instances list --uri',
        **kwargs)


class InstanceConfigCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceConfigCompleter, self).__init__(
        collection='spanner.projects.instanceConfigs',
        list_command='spanner instance-configs list --uri',
        **kwargs)


class OperationCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(OperationCompleter, self).__init__(
        collection='spanner.projects.instances.operations',
        list_command='spanner operations list --uri',
        flags=['instance'],
        **kwargs)


class DatabaseSessionCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DatabaseSessionCompleter, self).__init__(
        collection='spanner.projects.instances.databases.sessions',
        list_command='spanner databases sessions list --uri',
        flags=['database', 'instance'],
        **kwargs)


class DatabaseRoleCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DatabaseRoleCompleter, self).__init__(
        collection='spanner.projects.instances.databases.roles',
        list_command='beta spanner databases roles list --uri',
        flags=['database', 'instance'],
        **kwargs)


def Database(positional=True, required=True, text='Cloud Spanner database ID.'):
  if positional:
    return base.Argument('database', completer=DatabaseCompleter, help=text)
  else:
    return base.Argument(
        '--database', required=required, completer=DatabaseCompleter, help=text)


def Backup(positional=True, required=True, text='Cloud Spanner backup ID.'):
  if positional:
    return base.Argument('backup', completer=BackupCompleter, help=text)
  else:
    return base.Argument(
        '--backup', required=required, completer=BackupCompleter, help=text)


def Ddl(help_text=''):
  return base.Argument(
      '--ddl',
      action='append',
      required=False,
      help=help_text,
  )


def DdlFile(help_text):
  return base.Argument(
      '--ddl-file',
      required=False,
      completer=FilesCompleter,
      help=help_text,
  )


def ProtoDescriptorsFile(help_text):
  return base.Argument(
      '--proto-descriptors-file',
      required=False,
      completer=FilesCompleter,
      help=help_text,
      hidden=True,
  )


def DatabaseDialect(help_text):
  return base.Argument(
      '--database-dialect',
      required=False,
      choices=[
          databases.DATABASE_DIALECT_POSTGRESQL,
          databases.DATABASE_DIALECT_GOOGLESQL
      ],
      help=help_text,
  )


def IncludeProtoDescriptors(help_text):
  return base.Argument(
      '--include-proto-descriptors',
      action='store_true',
      help=help_text,
      default=False,
      hidden=True,
  )


def GetDDLsFromArgs(args):
  if args.ddl_file:
    return [files.ReadFileContents(args.ddl_file)]
  return args.ddl or []


def SplitDdlIntoStatements(args):
  """Break DDL statements on semicolon while preserving string literals."""
  ddls = GetDDLsFromArgs(args)
  statements = []
  for x in ddls:
    if hasattr(args, 'database_dialect'
              ) and args.database_dialect and args.database_dialect.upper(
              ) == databases.DATABASE_DIALECT_POSTGRESQL:
      # Split the ddl string by semi-colon and remove empty string to avoid
      # adding a PG ddl parser.
      # TODO(b/195711543): This would be incorrect if ';' is inside strings
      # and / or comments.
      statements.extend([stmt for stmt in x.split(';') if stmt])
    else:
      statements.extend(ddl_parser.PreprocessDDLWithParser(x))
  return statements


def GetProtoDescriptors(args):
  if args.proto_descriptors_file:
    proto_desc_content = files.ReadBinaryFileContents(
        args.proto_descriptors_file)
    descriptor_pb2.FileDescriptorSet.FromString(proto_desc_content)
    return proto_desc_content
  return None


def Config(required=True):
  return base.Argument(
      '--config',
      completer=InstanceConfigCompleter,
      required=required,
      help='Instance configuration defines the geographic placement and '
      'replication of the databases in that instance. Available '
      'configurations can be found by running '
      '"gcloud spanner instance-configs list"')


def Description(required=True):
  return base.Argument(
      '--description', required=required, help='Description of the instance.')


def Instance(positional=True, text='Cloud Spanner instance ID.'):
  if positional:
    return base.Argument('instance', completer=InstanceCompleter, help=text)
  else:
    return base.Argument(
        '--instance', required=True, completer=InstanceCompleter, help=text)


def Nodes(required=False):
  return base.Argument(
      '--nodes',
      required=required,
      type=int,
      help='Number of nodes for the instance.')


def ProcessingUnits(required=False):
  return base.Argument(
      '--processing-units',
      required=required,
      type=int,
      help='Number of processing units for the instance.')


def AutoscalingMaxNodes(required=False):
  return base.Argument(
      '--autoscaling-max-nodes',
      required=required,
      type=int,
      help='Maximum number of nodes for the autoscaled instance.',
  )


def AutoscalingMinNodes(required=False):
  return base.Argument(
      '--autoscaling-min-nodes',
      required=required,
      type=int,
      help='Minimum number of nodes for the autoscaled instance.',
  )


def AutoscalingMaxProcessingUnits(required=False):
  return base.Argument(
      '--autoscaling-max-processing-units',
      required=required,
      type=int,
      help='Maximum number of processing units for the autoscaled instance.',
  )


def AutoscalingMinProcessingUnits(required=False):
  return base.Argument(
      '--autoscaling-min-processing-units',
      required=required,
      type=int,
      help='Minimum number of processing units for the autoscaled instance.',
  )


def AutoscalingHighPriorityCpuTarget(required=False):
  return base.Argument(
      '--autoscaling-high-priority-cpu-target',
      required=required,
      type=int,
      help=(
          'Specifies the target percentage of high-priority CPU the autoscaled'
          ' instance can utilize.'
      ),
  )


def AutoscalingStorageTarget(required=False):
  return base.Argument(
      '--autoscaling-storage-target',
      required=required,
      type=int,
      help=(
          'Specifies the target percentage of storage the autoscaled instance'
          ' can utilize.'
      ),
  )


def SsdCache(
    positional=False,
    required=False,
    hidden=True,
    text='Cloud Spanner SSD Cache ID.',
):
  if positional:
    return base.Argument('cache_id', hidden=hidden, help=text)
  else:
    return base.Argument(
        '--ssd-cache', required=required, hidden=hidden, help=text
    )


def AddCapacityArgsForInstance(
    require_all_autoscaling_args, hide_autoscaling_args, parser
):
  """Parse the instance capacity arguments, including manual and autoscaling.

  Args:
    require_all_autoscaling_args: bool. If True, a complete autoscaling config
      is required.
    hide_autoscaling_args: bool. If True, the autoscaling args will be hidden.
    parser: the argparse parser for the command.
  """
  capacity_parser = parser.add_argument_group(mutex=True, required=False)

  # Manual scaling.
  Nodes().AddToParser(capacity_parser)
  ProcessingUnits().AddToParser(capacity_parser)

  # Autoscaling.
  autoscaling_config_group_parser = capacity_parser.add_argument_group(
      help='Autoscaling (Preview)', hidden=hide_autoscaling_args
  )
  AutoscalingHighPriorityCpuTarget(
      required=require_all_autoscaling_args
  ).AddToParser(autoscaling_config_group_parser)
  AutoscalingStorageTarget(required=require_all_autoscaling_args).AddToParser(
      autoscaling_config_group_parser
  )
  autoscaling_limits_group_parser = (
      autoscaling_config_group_parser.add_argument_group(
          mutex=True, required=require_all_autoscaling_args
      )
  )
  autoscaling_node_limits_group_parser = (
      autoscaling_limits_group_parser.add_argument_group(
          help='Autoscaling limits in nodes'
      )
  )
  AutoscalingMinNodes(required=require_all_autoscaling_args).AddToParser(
      autoscaling_node_limits_group_parser
  )
  AutoscalingMaxNodes(required=require_all_autoscaling_args).AddToParser(
      autoscaling_node_limits_group_parser
  )
  autoscaling_pu_limits_group_parser = (
      autoscaling_limits_group_parser.add_argument_group(
          help='Autoscaling limits in processing units'
      )
  )
  AutoscalingMinProcessingUnits(
      required=require_all_autoscaling_args
  ).AddToParser(autoscaling_pu_limits_group_parser)
  AutoscalingMaxProcessingUnits(
      required=require_all_autoscaling_args
  ).AddToParser(autoscaling_pu_limits_group_parser)


def TargetConfig(required=True):
  return base.Argument(
      '--target-config',
      completer=InstanceConfigCompleter,
      required=required,
      help='Target Instance configuration to move the instances.')


def EnableDropProtection(required=False):
  return base.Argument(
      '--enable-drop-protection',
      required=required,
      dest='enable_drop_protection',
      action=arg_parsers.StoreTrueFalseAction,
      help='Enable database deletion protection on this database.',
  )


def OperationId(database=False):
  return base.Argument(
      'operation',
      metavar='OPERATION-ID',
      completer=DatabaseOperationCompleter if database else OperationCompleter,
      help='ID of the operation')


def Session(positional=True, required=True, text='Cloud Spanner session ID'):
  if positional:
    return base.Argument(
        'session', completer=DatabaseSessionCompleter, help=text)

  else:
    return base.Argument(
        '--session',
        required=required,
        completer=DatabaseSessionCompleter,
        help=text)


def ReplicaFlag(parser, name, text, required=True):
  return parser.add_argument(
      name,
      required=required,
      metavar='location=LOCATION,type=TYPE',
      action='store',
      type=arg_parsers.ArgList(
          custom_delim_char=':',
          min_length=1,
          element_type=arg_parsers.ArgDict(
              spec={
                  'location': str,
                  'type': str
              },
              required_keys=['location', 'type']),
      ),
      help=text)


def _TransformOperationDone(resource):
  """Combines done and throttled fields into a single column."""
  done_cell = '{0}'.format(resource.get('done', False))
  if resource.get('metadata', {}).get('throttled', False):
    done_cell += ' (throttled)'
  return done_cell


def _TransformDatabaseId(resource):
  """Gets database ID depending on operation type."""
  metadata = resource.get('metadata')
  base_type = 'type.googleapis.com/google.spanner.admin.database.v1.{}'
  op_type = metadata.get('@type')

  if op_type == base_type.format(
      'RestoreDatabaseMetadata') or op_type == base_type.format(
          'OptimizeRestoredDatabaseMetadata'):
    return metadata.get('name')
  return metadata.get('database')


def AddCommonListArgs(parser, additional_choices=None):
  """Add Common flags for the List operation group."""
  mutex_group = parser.add_group(mutex=True, required=True)
  mutex_group.add_argument(
      '--instance-config',
      completer=InstanceConfigCompleter,
      help='The ID of the instance configuration the operation is executing on.'
  )
  mutex_group.add_argument(
      '--instance',
      completer=InstanceCompleter,
      help='The ID of the instance the operation is executing on.')
  Database(
      positional=False,
      required=False,
      text='For database operations, the name of the database '
      'the operations are executing on.').AddToParser(parser)
  Backup(
      positional=False,
      required=False,
      text='For backup operations, the name of the backup '
      'the operations are executing on.').AddToParser(parser)

  type_choices = {
      'INSTANCE':
          'Returns instance operations for the given instance. '
          'Note, type=INSTANCE does not work with --database or --backup.',
      'DATABASE':
          'If only the instance is specified (--instance), returns all '
          'database operations associated with the databases in the '
          'instance. When a database is specified (--database), the command '
          'would return database operations for the given database.',
      'BACKUP':
          'If only the instance is specified (--instance), returns all '
          'backup operations associated with backups in the instance. When '
          'a backup is specified (--backup), only the backup operations for '
          'the given backup are returned.',
      'DATABASE_RESTORE':
          'Database restore operations are returned for all databases in '
          'the given instance (--instance only) or only those associated '
          'with the given database (--database)',
      'DATABASE_CREATE':
          'Database create operations are returned for all databases in '
          'the given instance (--instance only) or only those associated '
          'with the given database (--database)',
      'DATABASE_UPDATE_DDL':
          'Database update DDL operations are returned for all databases in '
          'the given instance (--instance only) or only those associated '
          'with the given database (--database)',
      'INSTANCE_CONFIG_CREATE':
          'Instance configuration create operations are returned for the '
          'given instance configuration (--instance-config).',
      'INSTANCE_CONFIG_UPDATE':
          'Instance configuration update operations are returned for the '
          'given instance configuration (--instance-config).'
  }

  if additional_choices is not None:
    type_choices.update(additional_choices)

  parser.add_argument(
      '--type',
      default='',
      type=lambda x: x.upper(),
      choices=type_choices,
      help='(optional) List only the operations of the given type.')

  parser.display_info.AddFormat("""
          table(
            name.basename():label=OPERATION_ID,
            metadata.statements.join(sep="\n"),
            done():label=DONE,
            metadata.'@type'.split('.').slice(-1:).join()
          )
        """)
  parser.display_info.AddCacheUpdater(None)
  parser.display_info.AddTransforms({'done': _TransformOperationDone})
  parser.display_info.AddTransforms({'database': _TransformDatabaseId})


def AddCommonDescribeArgs(parser):
  """Adds common args to describe operations parsers shared across all stages.

  The common arguments are Database, Backup and OperationId.

  Args:
    parser: argparse.ArgumentParser to register arguments with.
  """
  # TODO(b/215646847): Remove Common args function, after instance-config flag
  # is present in all (GA/Beta/Alpha) stages. Currently, it is only present in
  # the Alpha stage.
  Database(
      positional=False,
      required=False,
      text='For a database operation, the name of the database '
      'the operation is executing on.').AddToParser(parser)
  Backup(
      positional=False,
      required=False,
      text='For a backup operation, the name of the backup '
      'the operation is executing on.').AddToParser(parser)
  OperationId().AddToParser(parser)


def AddCommonCancelArgs(parser):
  """Adds common args to cancel operations parsers shared across all stages.

  The common arguments are Database, Backup and OperationId.

  Args:
    parser: argparse.ArgumentParser to register arguments with.
  """
  # TODO(b/215646847): Remove Common args function, after instance-config flag
  # is present in all (GA/Beta/Alpha) stages. Currently, it is only present in
  # the Alpha stage.
  Database(
      positional=False,
      required=False,
      text='For a database operation, the name of the database '
      'the operation is executing on.').AddToParser(parser)
  Backup(
      positional=False,
      required=False,
      text='For a backup operation, the name of the backup '
      'the operation is executing on.').AddToParser(parser)
  OperationId().AddToParser(parser)


def DatabaseRole():
  return base.Argument(
      '--database-role',
      required=False,
      completer=DatabaseRoleCompleter,
      help='Cloud Spanner database role to assume for this request.')


def GetSpannerMigrationSourceFlag():
  return base.Argument(
      '--source',
      required=True,
      help='Flag for specifying source database (e.g., PostgreSQL, MySQL, DynamoDB).'
  )


def GetSpannerMigrationPrefixFlag():
  return base.Argument('--prefix', help='File prefix for generated files.')


def GetSpannerMigrationSourceProfileFlag():
  return base.Argument(
      '--source-profile',
      help='Flag for specifying connection profile for source database (e.g.,'
      ' "file=<path>,format=dump").')


def GetSpannerMigrationTargetFlag():
  return base.Argument(
      '--target',
      help='Specifies the target database, defaults to Spanner '
      '(accepted values: Spanner) (default "Spanner").')


def GetSpannerMigrationTargetProfileFlag():
  return base.Argument(
      '--target-profile',
      required=True,
      help='Flag for specifying connection profile for target database '
      '(e.g., "dialect=postgresql)".')


def GetSpannerMigrationSessionFlag():
  return base.Argument(
      '--session',
      required=True,
      help='Specifies the file that you restore session state from.')


def GetSpannerMigrationSkipForeignKeysFlag():
  return base.Argument(
      '--skip-foreign-keys',
      action='store_true',
      help='Skip creating foreign keys after data migration is complete.')


def GetSpannerMigrationWriteLimitFlag():
  return base.Argument(
      '--write-limit',
      help='Number of parallel writers to Cloud Spanner during bulk data migrations (default 40).'
  )


def GetSpannerMigrationDryRunFlag():
  return base.Argument(
      '--dry-run',
      action='store_true',
      help='Flag for generating DDL and schema conversion report without'
      ' creating a Cloud Spanner database.')


def GetSpannerMigrationLogLevelFlag():
  return base.Argument(
      '--log-level',
      help='To configure the log level for the execution (INFO, VERBOSE).')


def GetSpannerMigrationWebOpenFlag():
  return base.Argument('--open', action='store_true',
                       help='Open the Spanner migration tool web interface in '
                       'the default browser.')


def GetSpannerMigrationWebPortFlag():
  return base.Argument(
      '--port',
      help=(
          'The port in which Spanner migration tool will run, defaults to 8080'
      ),
  )


def GetSpannerMigrationJobIdFlag():
  return base.Argument(
      '--job-id', required=True, help='The job Id of an existing migration job.'
  )


def GetSpannerMigrationDataShardIdsFlag():
  return base.Argument(
      '--data-shard-ids',
      help=(
          'Relevant to sharded migrations. Optional comma separated list of'
          ' data shard Ids, if nothing is specified, all shards are cleaned up.'
      ),
  )


def GetSpannerMigrationCleanupDatastreamResourceFlag():
  return base.Argument(
      '--datastream',
      action='store_true',
      help='Cleanup datastream resource(s).',
  )


def GetSpannerMigrationCleanupDataflowResourceFlag():
  return base.Argument(
      '--dataflow', action='store_true', help='Cleanup dataflow resource(s).'
  )


def GetSpannerMigrationCleanupPubsubResourceFlag():
  return base.Argument(
      '--pub-sub', action='store_true', help='Cleanup pubsub resource(s).'
  )


def GetSpannerMigrationCleanupMonitoringResourceFlag():
  return base.Argument(
      '--monitoring',
      action='store_true',
      help='Cleanup monitoring dashboard(s).',
  )
