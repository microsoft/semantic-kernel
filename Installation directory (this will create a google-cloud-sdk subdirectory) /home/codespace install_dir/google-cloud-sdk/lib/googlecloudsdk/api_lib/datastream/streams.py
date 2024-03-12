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
"""Cloud Datastream connection profiles API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import exceptions as ds_exceptions
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io

_DEFAULT_API_VERSION = 'v1'


def GetStreamURI(resource):
  stream = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='datastream.projects.locations.streams')
  return stream.SelfLink()


class StreamsClient:
  """Client for streams service in the API."""

  def __init__(self, client=None, messages=None):
    self._client = client or util.GetClientInstance()
    self._messages = messages or util.GetMessagesModule()
    self._service = self._client.projects_locations_streams
    self._resource_parser = util.GetResourceParser()

  def _GetBackfillAllStrategy(self, release_track, args):
    """Gets BackfillAllStrategy message based on Stream objects source type."""
    if args.oracle_excluded_objects:
      return self._messages.BackfillAllStrategy(
          oracleExcludedObjects=util.ParseOracleRdbmsFile(
              self._messages, args.oracle_excluded_objects, release_track))
    elif args.mysql_excluded_objects:
      return self._messages.BackfillAllStrategy(
          mysqlExcludedObjects=util.ParseMysqlRdbmsFile(
              self._messages, args.mysql_excluded_objects, release_track))
    elif args.postgresql_excluded_objects:
      return self._messages.BackfillAllStrategy(
          postgresqlExcludedObjects=util.ParsePostgresqlRdbmsFile(
              self._messages, args.postgresql_excluded_objects))
    return self._messages.BackfillAllStrategy()

  def _ParseOracleSourceConfig(self, oracle_source_config_file, release_track):
    """Parses a oracle_sorce_config into the OracleSourceConfig message."""
    if release_track == base.ReleaseTrack.BETA:
      return self._ParseOracleSourceConfigBeta(
          oracle_source_config_file, release_track
      )

    return util.ParseMessageAndValidateSchema(
        oracle_source_config_file,
        'OracleSourceConfig',
        self._messages.OracleSourceConfig,
    )

  def _ParseOracleSourceConfigBeta(
      self, oracle_source_config_file, release_track
  ):
    """Parses a oracle_sorce_config into the OracleSourceConfig message."""
    data = console_io.ReadFromFileOrStdin(
        oracle_source_config_file, binary=False)
    try:
      oracle_source_config_head_data = yaml.load(data)
    except yaml.YAMLParseError as e:
      raise ds_exceptions.ParseError('Cannot parse YAML:[{0}]'.format(e))

    oracle_sorce_config_data_object = oracle_source_config_head_data.get(
        'oracle_source_config'
    )
    oracle_source_config = (
        oracle_sorce_config_data_object
        if oracle_sorce_config_data_object
        else oracle_source_config_head_data
    )

    include_objects_raw = oracle_source_config.get(
        util.GetRDBMSV1alpha1ToV1FieldName('include_objects', release_track),
        {})
    include_objects_data = util.ParseOracleSchemasListToOracleRdbmsMessage(
        self._messages, include_objects_raw, release_track)

    exclude_objects_raw = oracle_source_config.get(
        util.GetRDBMSV1alpha1ToV1FieldName('exclude_objects', release_track),
        {})
    exclude_objects_data = util.ParseOracleSchemasListToOracleRdbmsMessage(
        self._messages, exclude_objects_raw, release_track)

    oracle_source_config_msg = self._messages.OracleSourceConfig(
        includeObjects=include_objects_data,
        excludeObjects=exclude_objects_data,
    )

    if oracle_source_config.get('max_concurrent_cdc_tasks'):
      oracle_source_config_msg.maxConcurrentCdcTasks = oracle_source_config.get(
          'max_concurrent_cdc_tasks')

    return oracle_source_config_msg

  def _ParseMysqlSourceConfig(self, mysql_source_config_file, release_track):
    """Parses a mysql_sorce_config into the MysqlSourceConfig message."""
    if release_track == base.ReleaseTrack.BETA:
      return self._ParseMysqlSourceConfigBeta(
          mysql_source_config_file, release_track
      )

    return util.ParseMessageAndValidateSchema(
        mysql_source_config_file,
        'MysqlSourceConfig',
        self._messages.MysqlSourceConfig,
    )

  def _ParseMysqlSourceConfigBeta(
      self, mysql_source_config_file, release_track
  ):
    """Parses an old mysql_sorce_config into the MysqlSourceConfig message."""
    data = console_io.ReadFromFileOrStdin(
        mysql_source_config_file, binary=False)
    try:
      mysql_sorce_config_head_data = yaml.load(data)
    except yaml.YAMLParseError as e:
      raise ds_exceptions.ParseError('Cannot parse YAML:[{0}]'.format(e))

    mysql_sorce_config_data_object = mysql_sorce_config_head_data.get(
        'mysql_source_config'
    )
    mysql_source_config = (
        mysql_sorce_config_data_object
        if mysql_sorce_config_data_object
        else mysql_sorce_config_head_data
    )

    include_objects_raw = mysql_source_config.get(
        util.GetRDBMSV1alpha1ToV1FieldName('include_objects', release_track),
        {})
    include_objects_data = util.ParseMysqlSchemasListToMysqlRdbmsMessage(
        self._messages, include_objects_raw, release_track)

    exclude_objects_raw = mysql_source_config.get(
        util.GetRDBMSV1alpha1ToV1FieldName('exclude_objects', release_track),
        {})
    exclude_objects_data = util.ParseMysqlSchemasListToMysqlRdbmsMessage(
        self._messages, exclude_objects_raw, release_track)

    mysql_sourec_config_msg = self._messages.MysqlSourceConfig(
        includeObjects=include_objects_data,
        excludeObjects=exclude_objects_data,
    )

    if mysql_source_config.get('max_concurrent_cdc_tasks'):
      mysql_sourec_config_msg.maxConcurrentCdcTasks = mysql_source_config.get(
          'max_concurrent_cdc_tasks')

    return mysql_sourec_config_msg

  def _ParsePostgresqlSourceConfig(self, postgresql_source_config_file):
    """Parses a postgresql_sorce_config into the PostgresqlSourceConfig message."""

    return util.ParseMessageAndValidateSchema(
        postgresql_source_config_file,
        'PostgresqlSourceConfig',
        self._messages.PostgresqlSourceConfig,
    )

  def _ParseGcsDestinationConfig(
      self, gcs_destination_config_file, release_track
  ):
    """Parses a GcsDestinationConfig into the GcsDestinationConfig message."""

    if release_track == base.ReleaseTrack.BETA:
      return self._ParseGcsDestinationConfigBeta(gcs_destination_config_file)

    return util.ParseMessageAndValidateSchema(
        gcs_destination_config_file,
        'GcsDestinationConfig',
        self._messages.GcsDestinationConfig,
    )

  def _ParseGcsDestinationConfigBeta(self, gcs_destination_config_file):
    """Parses a gcs_destination_config into the GcsDestinationConfig message."""
    data = console_io.ReadFromFileOrStdin(
        gcs_destination_config_file, binary=False)
    try:
      gcs_destination_head_config_data = yaml.load(data)
    except yaml.YAMLParseError as e:
      raise ds_exceptions.ParseError('Cannot parse YAML:[{0}]'.format(e))

    gcs_destination_config_data_object = gcs_destination_head_config_data.get(
        'gcs_destination_config'
    )
    gcs_destination_config_data = (
        gcs_destination_config_data_object
        if gcs_destination_config_data_object
        else gcs_destination_head_config_data
    )

    path = gcs_destination_config_data.get('path', '')
    file_rotation_mb = gcs_destination_config_data.get('file_rotation_mb', {})
    file_rotation_interval = gcs_destination_config_data.get(
        'file_rotation_interval', {})
    gcs_dest_config_msg = self._messages.GcsDestinationConfig(
        path=path, fileRotationMb=file_rotation_mb,
        fileRotationInterval=file_rotation_interval)
    if 'avro_file_format' in gcs_destination_config_data:
      gcs_dest_config_msg.avroFileFormat = self._messages.AvroFileFormat()
    elif 'json_file_format' in gcs_destination_config_data:
      json_file_format_data = gcs_destination_config_data.get(
          'json_file_format')
      gcs_dest_config_msg.jsonFileFormat = self._messages.JsonFileFormat(
          compression=json_file_format_data.get('compression'),
          schemaFileFormat=json_file_format_data.get('schema_file_format'))
    else:
      raise ds_exceptions.ParseError(
          'Cannot parse YAML: missing file format.')
    return gcs_dest_config_msg

  def _ParseBigqueryDestinationConfig(self, config_file):
    """Parses a BigQueryDestinationConfig into the BigQueryDestinationConfig message."""
    return util.ParseMessageAndValidateSchema(
        config_file,
        'BigQueryDestinationConfig',
        self._messages.BigQueryDestinationConfig,
    )

  def _GetStream(self, stream_id, release_track, args):
    """Returns a stream object."""
    labels = labels_util.ParseCreateArgs(
        args, self._messages.Stream.LabelsValue)
    stream_obj = self._messages.Stream(
        name=stream_id, labels=labels, displayName=args.display_name)

    # TODO(b/207467120): use CONCEPTS.source only.
    if release_track == base.ReleaseTrack.BETA:
      source_connection_profile_ref = args.CONCEPTS.source_name.Parse()
    else:
      source_connection_profile_ref = args.CONCEPTS.source.Parse()

    stream_source_config = self._messages.SourceConfig()
    stream_source_config.sourceConnectionProfile = (
        source_connection_profile_ref.RelativeName())
    if args.oracle_source_config:
      stream_source_config.oracleSourceConfig = self._ParseOracleSourceConfig(
          args.oracle_source_config, release_track)
    elif args.mysql_source_config:
      stream_source_config.mysqlSourceConfig = self._ParseMysqlSourceConfig(
          args.mysql_source_config, release_track)
    elif args.postgresql_source_config:
      stream_source_config.postgresqlSourceConfig = (
          self._ParsePostgresqlSourceConfig(args.postgresql_source_config)
      )
    stream_obj.sourceConfig = stream_source_config

    # TODO(b/207467120): use CONCEPTS.destination only.
    if release_track == base.ReleaseTrack.BETA:
      destination_connection_profile_ref = args.CONCEPTS.destination_name.Parse(
      )
    else:
      destination_connection_profile_ref = args.CONCEPTS.destination.Parse()

    stream_destination_config = self._messages.DestinationConfig()
    stream_destination_config.destinationConnectionProfile = (
        destination_connection_profile_ref.RelativeName())
    if args.gcs_destination_config:
      stream_destination_config.gcsDestinationConfig = (
          self._ParseGcsDestinationConfig(
              args.gcs_destination_config, release_track
          )
      )
    elif args.bigquery_destination_config:
      stream_destination_config.bigqueryDestinationConfig = (
          self._ParseBigqueryDestinationConfig(
              args.bigquery_destination_config))
    stream_obj.destinationConfig = stream_destination_config

    if args.backfill_none:
      stream_obj.backfillNone = self._messages.BackfillNoneStrategy()
    elif args.backfill_all:
      backfill_all_strategy = self._GetBackfillAllStrategy(release_track, args)
      stream_obj.backfillAll = backfill_all_strategy

    return stream_obj

  def _GetExistingStream(self, name):
    get_req = self._messages.DatastreamProjectsLocationsStreamsGetRequest(
        name=name
    )
    return self._service.Get(get_req)

  def _UpdateLabels(self, stream, args):
    """Updates labels of the stream."""
    add_labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    remove_labels = labels_util.GetRemoveLabelsListFromArgs(args)
    value_type = self._messages.Stream.LabelsValue
    update_result = labels_util.Diff(
        additions=add_labels,
        subtractions=remove_labels,
        clear=args.clear_labels
    ).Apply(value_type, stream.labels)
    if update_result.needs_update:
      stream.labels = update_result.labels

  def _UpdateListWithFieldNamePrefixes(
      self, update_fields, prefix_to_check, prefix_to_add):
    """Returns an updated list of field masks with necessary prefixes."""
    temp_fields = [
        prefix_to_add + field
        for field in update_fields
        if field.startswith(prefix_to_check)
    ]
    update_fields = [
        x for x in update_fields if (not x.startswith(prefix_to_check))
    ]
    update_fields.extend(temp_fields)
    return update_fields

  def _GetUpdatedStream(self, stream, release_track, args):
    """Returns updated stream."""
    # Verify command flag names align with Stream object field names.
    update_fields = []
    user_update_mask = args.update_mask or ''
    user_update_mask_list = user_update_mask.split(',')

    if release_track == base.ReleaseTrack.BETA:
      user_update_mask_list = util.UpdateV1alpha1ToV1MaskFields(
          user_update_mask_list)

    update_fields.extend(user_update_mask_list)

    if args.IsSpecified('display_name'):
      stream.displayName = args.display_name

    # TODO(b/207467120): use source field only.
    if release_track == base.ReleaseTrack.BETA:
      source_connection_profile_ref = args.CONCEPTS.source_name.Parse()
      source_field_name = 'source_name'
    else:
      source_connection_profile_ref = args.CONCEPTS.source.Parse()
      source_field_name = 'source'
    if args.IsSpecified(source_field_name):
      stream.sourceConfig.sourceConnectionProfile = (
          source_connection_profile_ref.RelativeName())
      if source_field_name in update_fields:
        update_fields.remove(source_field_name)
        update_fields.append('source_config.source_connection_profile')

    if args.IsSpecified('oracle_source_config'):
      stream.sourceConfig.oracleSourceConfig = self._ParseOracleSourceConfig(
          args.oracle_source_config, release_track)
      # Fix field names in update mask
      update_fields = self._UpdateListWithFieldNamePrefixes(
          update_fields, 'oracle_source_config', 'source_config.')

    elif args.IsSpecified('mysql_source_config'):
      stream.sourceConfig.mysqlSourceConfig = self._ParseMysqlSourceConfig(
          args.mysql_source_config, release_track)
      update_fields = self._UpdateListWithFieldNamePrefixes(
          update_fields, 'mysql_source_config', 'source_config.')

    elif args.IsSpecified('postgresql_source_config'):
      stream.sourceConfig.postgresqlSourceConfig = (
          self._ParsePostgresqlSourceConfig(args.postgresql_source_config)
      )
      update_fields = self._UpdateListWithFieldNamePrefixes(
          update_fields, 'postgresql_source_config', 'source_config.')

    # TODO(b/207467120): use source field only.
    if release_track == base.ReleaseTrack.BETA:
      destination_connection_profile_ref = (
          args.CONCEPTS.destination_name.Parse())
      destination_field_name = 'destination_name'
    else:
      destination_connection_profile_ref = (args.CONCEPTS.destination.Parse())
      destination_field_name = 'destination'
    if args.IsSpecified(destination_field_name):
      stream.destinationConfig.destinationConnectionProfile = (
          destination_connection_profile_ref.RelativeName())
      if destination_field_name in update_fields:
        update_fields.remove(destination_field_name)
        update_fields.append(
            'destination_config.destination_connection_profile')

    if args.IsSpecified('gcs_destination_config'):
      stream.destinationConfig.gcsDestinationConfig = (
          self._ParseGcsDestinationConfig(
              args.gcs_destination_config, release_track
          )
      )
      update_fields = self._UpdateListWithFieldNamePrefixes(
          update_fields, 'gcs_destination_config', 'destination_config.')
    elif args.IsSpecified('bigquery_destination_config'):
      stream.destinationConfig.bigqueryDestinationConfig = (
          self._ParseBigqueryDestinationConfig(
              args.bigquery_destination_config))
      update_fields = self._UpdateListWithFieldNamePrefixes(
          update_fields, 'bigquery_destination_config', 'destination_config.')

    if args.IsSpecified('backfill_none'):
      stream.backfillNone = self._messages.BackfillNoneStrategy()
      # NOMUTANTS--This path has been verified by manual tests.
      try:
        stream.reset('backfillAll')
      except AttributeError:
        # Attempt to remove a backfill all
        # previous definition, but doesn't exist.
        pass

    elif args.IsSpecified('backfill_all'):
      backfill_all_strategy = self._GetBackfillAllStrategy(release_track, args)
      stream.backfillAll = backfill_all_strategy
      # NOMUTANTS--This path has been verified by manual tests.
      try:
        stream.reset('backfillNone')
      except AttributeError:
        # Attempt to remove a backfill none previous definition,
        # but it doesn't exist.
        pass

    if args.IsSpecified('state'):
      stream.state = self._messages.Stream.StateValueValuesEnum(
          (args.state).upper())

    self._UpdateLabels(stream, args)
    return stream, update_fields

  def Create(self, parent_ref, stream_id, release_track, args=None):
    """Creates a stream.

    Args:
      parent_ref: a Resource reference to a parent datastream.projects.locations
        resource for this stream.
      stream_id: str, the name of the resource to create.
      release_track: Some arguments are added based on the command release
        track.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the stream.
    """
    stream = self._GetStream(stream_id, release_track, args)
    validate_only = args.validate_only
    force = args.force

    request_id = util.GenerateRequestId()
    create_req_type = self._messages.DatastreamProjectsLocationsStreamsCreateRequest
    create_req = create_req_type(
        stream=stream,
        streamId=stream.name,
        parent=parent_ref,
        requestId=request_id,
        validateOnly=validate_only,
        force=force)

    return self._service.Create(create_req)

  def Update(self, name, release_track, args=None):
    """Updates a stream.

    Args:
      name: str, the reference of the stream to
          update.
      release_track: Some arguments are added based on the command release
        track.
      args: argparse.Namespace, The arguments that this command was
          invoked with.

    Returns:
      Operation: the operation for updating the connection profile.
    """
    validate_only = args.validate_only
    force = args.force

    current_stream = self._GetExistingStream(name)

    updated_stream, update_fields = self._GetUpdatedStream(
        current_stream, release_track, args)

    request_id = util.GenerateRequestId()
    update_req_type = self._messages.DatastreamProjectsLocationsStreamsPatchRequest
    update_req = update_req_type(
        stream=updated_stream,
        name=updated_stream.name,
        requestId=request_id,
        validateOnly=validate_only,
        force=force
    )
    if args.update_mask:
      update_req.updateMask = ','.join(update_fields)

    return self._service.Patch(update_req)
