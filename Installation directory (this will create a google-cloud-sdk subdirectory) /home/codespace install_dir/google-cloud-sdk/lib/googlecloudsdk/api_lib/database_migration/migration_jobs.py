# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Database Migration Service migration jobs API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import conversion_workspaces
from googlecloudsdk.api_lib.database_migration import filter_rewrite
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.resource import resource_property
import six


class Error(core_exceptions.Error):
  """Class for errors raised by container commands."""


class MigrationJobsClient(object):
  """Client for migration jobs service in the API."""

  _FIELDS_MAP = ['display_name', 'type', 'dump_path', 'source', 'destination']
  _REVERSE_MAP = ['vm_ip', 'vm_port', 'vm', 'vpc']

  def __init__(self, release_track):
    self.client = api_util.GetClientInstance(release_track)
    self.messages = api_util.GetMessagesModule(release_track)
    self._service = self.client.projects_locations_migrationJobs
    self.resource_parser = api_util.GetResourceParser(release_track)
    self.release_track = release_track

  def _ValidateArgs(self, args):
    self._ValidateDumpPath(args)

  def _ValidateDumpPath(self, args):
    if args.dump_path is None:
      return
    try:
      storage_util.ObjectReference.FromArgument(
          args.dump_path, allow_empty_object=False)
    except Exception as e:
      raise exceptions.InvalidArgumentException('dump-path', six.text_type(e))

  def _ValidateConversionWorkspaceArgs(self, conversion_workspace_ref, args):
    """Validate flags for conversion workspace.

    Args:
      conversion_workspace_ref: str, the reference of the conversion workspace.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Raises:
      BadArgumentException: commit-id or filter field is provided without
      specifying the conversion workspace
    """
    if conversion_workspace_ref is None:
      if args.IsKnownAndSpecified('commit_id'):
        raise exceptions.BadArgumentException(
            'commit-id',
            (
                'Conversion workspace commit-id can only be specified for'
                ' migration jobs associated with a conversion workspace.'
            ),
        )
      if args.IsKnownAndSpecified('filter'):
        raise exceptions.BadArgumentException(
            'filter',
            (
                'Filter can only be specified for migration jobs associated'
                ' with a conversion workspace.'
            ),
        )

  def _ValidateConversionWorkspaceMessageArgs(self, conversion_workspace, args):
    """Validate flags for conversion workspace.

    Args:
      conversion_workspace: str, the internal migration job conversion workspace
        message.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Raises:
      BadArgumentException: commit-id or filter field is provided without
      specifying the conversion workspace
    """
    if conversion_workspace.name is None:
      if args.IsKnownAndSpecified('commit_id'):
        raise exceptions.BadArgumentException(
            'commit-id',
            (
                'Conversion workspace commit-id can only be specified for'
                ' migration jobs associated with a conversion workspace.'
            ),
        )
      if args.IsKnownAndSpecified('filter'):
        raise exceptions.BadArgumentException(
            'filter',
            (
                'Filter can only be specified for migration jobs associated'
                ' with a conversion workspace.'
            ),
        )

  def _GetType(self, mj_type, type_value):
    return mj_type.TypeValueValuesEnum.lookup_by_name(type_value)

  def _GetDumpType(self, dump_type, type_value):
    return dump_type.DumpTypeValueValuesEnum.lookup_by_name(type_value)

  def _GetVpcPeeringConnectivity(self, args):
    return self.messages.VpcPeeringConnectivity(vpc=args.peer_vpc)

  def _GetReverseSshConnectivity(self, args):
    return self.messages.ReverseSshConnectivity(
        vm=args.vm,
        vmIp=args.vm_ip,
        vmPort=args.vm_port,
        vpc=args.vpc
    )

  def _GetStaticIpConnectivity(self):
    return self.messages.StaticIpConnectivity()

  def _UpdateLabels(self, args, migration_job, update_fields):
    """Updates labels of the migration job."""
    add_labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    remove_labels = labels_util.GetRemoveLabelsListFromArgs(args)
    value_type = self.messages.MigrationJob.LabelsValue
    update_result = labels_util.Diff(
        additions=add_labels,
        subtractions=remove_labels,
        clear=args.clear_labels
    ).Apply(value_type)
    if update_result.needs_update:
      migration_job.labels = update_result.labels
      update_fields.append('labels')

  def _GetConversionWorkspaceInfo(self, conversion_workspace_ref, args):
    """Returns the conversion worksapce info.

    Args:
      conversion_workspace_ref: str, the reference of the conversion workspace.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Raises:
      BadArgumentException: Unable to fetch latest commit for the specified
      conversion workspace.
    """
    if conversion_workspace_ref is not None:
      conversion_workspace_obj = self.messages.ConversionWorkspaceInfo(
          name=conversion_workspace_ref.RelativeName()
      )
      if args.commit_id is not None:
        conversion_workspace_obj.commitId = args.commit_id
      else:
        # Get conversion workspace's latest commit id.
        cw_client = conversion_workspaces.ConversionWorkspacesClient(
            self.release_track
        )
        conversion_workspace = cw_client.Describe(
            conversion_workspace_ref.RelativeName(),
        )
        if conversion_workspace.latestCommitId is None:
          raise exceptions.BadArgumentException(
              'conversion-workspace',
              (
                  'Unable to fetch latest commit for the specified conversion'
                  ' workspace. Conversion Workspace might not be committed.'
              ),
          )
        conversion_workspace_obj.commitId = conversion_workspace.latestCommitId
      return conversion_workspace_obj

  def _ComplementConversionWorkspaceInfo(self, conversion_workspace, args):
    """Returns the conversion workspace info with the supplied or the latest commit id.

    Args:
      conversion_workspace: the internal migration job conversion workspace
        message.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Raises:
      BadArgumentException: Unable to fetch latest commit for the specified
      conversion workspace.
      InvalidArgumentException: Invalid conversion workspace message on the
      migration job.
    """
    if conversion_workspace.name is None:
      raise exceptions.InvalidArgumentException(
          'conversion-workspace',
          (
              'The supplied migration job does not have a valid conversion'
              ' workspace attached to it'
          ),
      )
    if args.commit_id is not None:
      conversion_workspace.commitId = args.commit_id
      return conversion_workspace
    # Get conversion workspace's latest commit id.
    cw_client = conversion_workspaces.ConversionWorkspacesClient(
        self.release_track
    )
    cst_conversion_workspace = cw_client.Describe(
        conversion_workspace.name,
    )
    if cst_conversion_workspace.latestCommitId is None:
      raise exceptions.BadArgumentException(
          'conversion-workspace',
          (
              'Unable to fetch latest commit for the specified conversion'
              ' workspace. Conversion Workspace might not be committed.'
          ),
      )
    conversion_workspace.commitId = cst_conversion_workspace.latestCommitId
    return conversion_workspace

  def _GetPerformanceConfig(self, args):
    """Returns the performance config with dump parallel level.

    Args:
      args: argparse.Namespace, the arguments that this command was invoked
        with.
    """
    performance_config_obj = self.messages.PerformanceConfig
    return performance_config_obj(
        dumpParallelLevel=performance_config_obj.DumpParallelLevelValueValuesEnum.lookup_by_name(
            args.dump_parallel_level
        )
    )

  def _GetSqlServerDatabaseDetails(
      self, sqlserver_databases, sqlserver_encrypted_databases
  ):
    """Returns the sqlserver database details list.

    Args:
      sqlserver_databases: The list of databases to be migrated.
      sqlserver_encrypted_databases: JSON/YAML file for encryption settings for
        encrypted databases.

    Raises:
      Error: Empty list item in JSON/YAML file.
      Error: Encrypted Database name not found in database list.
      Error: Invalid JSON/YAML file.
    """
    database_details_class = (
        self.messages.SqlServerHomogeneousMigrationJobConfig.DatabaseDetailsValue
    )
    additional_properties = []
    encrypted_databases_list = []

    if sqlserver_encrypted_databases:
      for database in sqlserver_encrypted_databases:
        if database is None:
          raise Error('Empty list item in JSON/YAML file.')
        if database['databaseName'] not in sqlserver_databases:
          raise Error(
              'Encrypted Database name {dbName} not found in database list.'
              .format(dbName=database['databaseName'])
          )
        try:
          database_details = encoding.PyValueToMessage(
              self.messages.SqlServerDatabaseDetails,
              database['databaseDetails'],
          )
        except Exception as e:
          raise Error(e)
        encrypted_databases_list.append(database['databaseName'])
        additional_properties.append(
            database_details_class.AdditionalProperty(
                key=database['databaseName'], value=database_details
            )
        )

    for database in sqlserver_databases:
      if database in encrypted_databases_list:
        continue
      additional_properties.append(
          database_details_class.AdditionalProperty(
              key=database, value=self.messages.SqlServerDatabaseDetails()
          )
      )
    return database_details_class(additionalProperties=additional_properties)

  def _GetSqlserverHomogeneousMigrationJobConfig(self, args):
    """Returns the sqlserver homogeneous migration job config.

    Args:
      args: argparse.Namespace, the arguments that this command was invoked
        with.
    """
    sqlserver_homogeneous_migration_job_config_obj = (
        self.messages.SqlServerHomogeneousMigrationJobConfig(
            backupFilePattern=args.sqlserver_backup_file_pattern
        )
    )
    if args.IsKnownAndSpecified('sqlserver_databases'):
      sqlserver_homogeneous_migration_job_config_obj.databaseDetails = (
          self._GetSqlServerDatabaseDetails(
              args.sqlserver_databases, args.sqlserver_encrypted_databases
          )
      )
    return sqlserver_homogeneous_migration_job_config_obj

  def _GetMigrationJob(
      self,
      source_ref,
      destination_ref,
      conversion_workspace_ref,
      cmek_key_ref,
      args,
  ):
    """Returns a migration job."""
    migration_job_type = self.messages.MigrationJob
    labels = labels_util.ParseCreateArgs(
        args, self.messages.MigrationJob.LabelsValue
    )
    type_value = self._GetType(migration_job_type, args.type)
    source = source_ref.RelativeName()
    destination = destination_ref.RelativeName()
    params = {}
    if args.IsSpecified('peer_vpc'):
      params['vpcPeeringConnectivity'] = self._GetVpcPeeringConnectivity(args)
    elif args.IsSpecified('vm_ip'):
      params['reverseSshConnectivity'] = self._GetReverseSshConnectivity(args)
    elif args.IsSpecified('static_ip'):
      params['staticIpConnectivity'] = self._GetStaticIpConnectivity()

    migration_job_obj = migration_job_type(
        labels=labels,
        displayName=args.display_name,
        state=migration_job_type.StateValueValuesEnum.CREATING,
        type=type_value,
        dumpPath=args.dump_path,
        source=source,
        destination=destination,
        **params)
    if conversion_workspace_ref is not None:
      migration_job_obj.conversionWorkspace = self._GetConversionWorkspaceInfo(
          conversion_workspace_ref, args
      )
    if cmek_key_ref is not None:
      migration_job_obj.cmekKeyName = cmek_key_ref.RelativeName()

    if args.IsKnownAndSpecified('filter'):
      args.filter, server_filter = filter_rewrite.Rewriter().Rewrite(
          args.filter
      )
      migration_job_obj.filter = server_filter

    if args.IsKnownAndSpecified('dump_parallel_level'):
      migration_job_obj.performanceConfig = self._GetPerformanceConfig(args)

    if args.IsKnownAndSpecified('sqlserver_databases'):
      migration_job_obj.sqlserverHomogeneousMigrationJobConfig = (
          self._GetSqlserverHomogeneousMigrationJobConfig(args)
      )

    return migration_job_obj

  def _UpdateConnectivity(self, migration_job, args):
    """Update connectivity method for the migration job."""
    if args.IsSpecified('static_ip'):
      migration_job.staticIpConnectivity = self._GetStaticIpConnectivity()
      migration_job.vpcPeeringConnectivity = None
      migration_job.reverseSshConnectivity = None
      return

    if args.IsSpecified('peer_vpc'):
      migration_job.vpcPeeringConnectivity = self._GetVpcPeeringConnectivity(
          args)
      migration_job.reverseSshConnectivity = None
      migration_job.staticIpConnectivity = None
      return

    for field in self._REVERSE_MAP:
      if args.IsSpecified(field):
        migration_job.reverseSshConnectivity = self._GetReverseSshConnectivity(
            args)
        migration_job.vpcPeeringConnectivity = None
        migration_job.staticIpConnectivity = None
        return

  def _GetUpdateMask(self, args):
    """Returns update mask for specified fields."""
    update_fields = [resource_property.ConvertToCamelCase(field)
                     for field in sorted(self._FIELDS_MAP)
                     if args.IsSpecified(field)]
    update_fields.extend(
        ['reverseSshConnectivity.{0}'.format(
            resource_property.ConvertToCamelCase(field))
         for field in sorted(self._REVERSE_MAP) if args.IsSpecified(field)])
    if args.IsSpecified('peer_vpc'):
      update_fields.append('vpcPeeringConnectivity.vpc')
    if args.IsKnownAndSpecified('dump_parallel_level'):
      update_fields.append('performanceConfig.dumpParallelLevel')
    if args.IsKnownAndSpecified('filter'):
      update_fields.append('filter')
    if args.IsKnownAndSpecified('commit_id') or args.IsKnownAndSpecified(
        'filter'
    ):
      update_fields.append('conversionWorkspace.commitId')
    return  update_fields

  def _GetUpdatedMigrationJob(
      self, migration_job, source_ref, destination_ref, args):
    """Returns updated migration job and list of updated fields."""
    update_fields = self._GetUpdateMask(args)
    if args.IsSpecified('display_name'):
      migration_job.displayName = args.display_name
    if args.IsSpecified('type'):
      migration_job.type = self._GetType(self.messages.MigrationJob, args.type)
    if args.IsKnownAndSpecified('dump_type'):
      migration_job.dumpType = self._GetDumpType(
          self.messages.MigrationJob, args.dump_type
      )
    if args.IsSpecified('dump_path'):
      migration_job.dumpPath = args.dump_path
    if args.IsSpecified('source'):
      migration_job.source = source_ref.RelativeName()
    if args.IsSpecified('destination'):
      migration_job.destination = destination_ref.RelativeName()
    if args.IsKnownAndSpecified('dump_parallel_level'):
      migration_job.performanceConfig = self._GetPerformanceConfig(args)
    if args.IsKnownAndSpecified('filter'):
      args.filter, server_filter = filter_rewrite.Rewriter().Rewrite(
          args.filter
      )
      migration_job.filter = server_filter
    self._UpdateConnectivity(migration_job, args)
    self._UpdateLabels(args, migration_job, update_fields)
    return migration_job, update_fields

  def _GetExistingMigrationJob(self, name):
    get_req = (
        self.messages.DatamigrationProjectsLocationsMigrationJobsGetRequest(
            name=name
        )
    )
    return self._service.Get(get_req)

  def Create(
      self,
      parent_ref,
      migration_job_id,
      source_ref,
      destination_ref,
      conversion_workspace_ref=None,
      cmek_key_ref=None,
      args=None,
  ):
    """Creates a migration job.

    Args:
      parent_ref: a Resource reference to a parent
        datamigration.projects.locations resource for this migration job.
      migration_job_id: str, the name of the resource to create.
      source_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource.
      destination_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource.
      conversion_workspace_ref: a Resource reference to a
        datamigration.projects.locations.conversionWorkspaces resource.
      cmek_key_ref: a Resource reference to a
        cloudkms.projects.locations.keyRings.cryptoKeys resource.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the migration job.
    """
    self._ValidateArgs(args)
    self._ValidateConversionWorkspaceArgs(conversion_workspace_ref, args)

    migration_job = self._GetMigrationJob(
        source_ref,
        destination_ref,
        conversion_workspace_ref,
        cmek_key_ref,
        args,
    )

    request_id = api_util.GenerateRequestId()
    create_req_type = (
        self.messages.DatamigrationProjectsLocationsMigrationJobsCreateRequest
    )
    create_req = create_req_type(
        migrationJob=migration_job,
        migrationJobId=migration_job_id,
        parent=parent_ref,
        requestId=request_id)

    return self._service.Create(create_req)

  def Update(self, name, source_ref, destination_ref, args=None):
    """Updates a migration job.

    Args:
      name: str, the reference of the migration job to
          update.
      source_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource.
      destination_ref: a Resource reference to a
        datamigration.projects.locations.connectionProfiles resource.
      args: argparse.Namespace, The arguments that this command was
          invoked with.

    Returns:
      Operation: the operation for updating the migration job.678888888
    """
    self._ValidateArgs(args)

    current_mj = self._GetExistingMigrationJob(name)

    # since this property doesn't exist in older api versions
    if (
        hasattr(current_mj, 'conversionWorkspace')
        and current_mj.conversionWorkspace is not None
    ):
      self._ValidateConversionWorkspaceMessageArgs(
          current_mj.conversionWorkspace, args
      )

      current_mj.conversionWorkspace = self._ComplementConversionWorkspaceInfo(
          current_mj.conversionWorkspace, args
      )

    migration_job, update_fields = self._GetUpdatedMigrationJob(
        current_mj, source_ref, destination_ref, args)

    request_id = api_util.GenerateRequestId()
    update_req_type = (
        self.messages.DatamigrationProjectsLocationsMigrationJobsPatchRequest
    )
    update_req = update_req_type(
        migrationJob=migration_job,
        name=name,
        requestId=request_id,
        updateMask=','.join(update_fields)
    )

    return self._service.Patch(update_req)
