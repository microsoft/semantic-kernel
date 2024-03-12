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
"""Cloud Datastream connection profiles API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.datastream import exceptions as ds_exceptions
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io


def GetConnectionProfileURI(resource):
  connection_profile = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='datastream.projects.locations.connectionProfiles')
  return connection_profile.SelfLink()


class ConnectionProfilesClient:
  """Client for connection profiles service in the API."""

  def __init__(self, client=None, messages=None):
    self._client = client or util.GetClientInstance()
    self._messages = messages or util.GetMessagesModule()
    self._service = self._client.projects_locations_connectionProfiles
    self._resource_parser = util.GetResourceParser()

  def _ValidateArgs(self, args):
    self._ValidateSslConfigArgs(args)

  def _ValidateSslConfigArgs(self, args):
    self._ValidateCertificateFormat(args.ca_certificate, 'CA certificate')
    self._ValidateCertificateFormat(args.client_certificate,
                                    'client certificate')
    self._ValidateCertificateFormat(args.client_key, 'client key')

  def _ValidateCertificateFormat(self, certificate, name):
    if not certificate:
      return True
    cert = certificate.strip()
    cert_lines = cert.split('\n')
    if (not cert_lines[0].startswith('-----') or
        not cert_lines[-1].startswith('-----')):
      raise exceptions.InvalidArgumentException(
          name,
          'The certificate does not appear to be in PEM format: \n{0}'.format(
              cert))

  def _GetSslConfig(self, args):
    return self._messages.MysqlSslConfig(
        clientKey=args.client_key,
        clientCertificate=args.client_certificate,
        caCertificate=args.ca_certificate)

  def _GetMySqlProfile(self, args):
    ssl_config = self._GetSslConfig(args)
    return self._messages.MysqlProfile(
        hostname=args.mysql_hostname,
        port=args.mysql_port,
        username=args.mysql_username,
        password=args.mysql_password,
        sslConfig=ssl_config)

  def _GetOracleProfile(self, args):
    return self._messages.OracleProfile(
        hostname=args.oracle_hostname,
        port=args.oracle_port,
        username=args.oracle_username,
        password=args.oracle_password,
        databaseService=args.database_service)

  def _GetPostgresqlProfile(self, args):
    return self._messages.PostgresqlProfile(
        hostname=args.postgresql_hostname,
        port=args.postgresql_port,
        username=args.postgresql_username,
        password=args.postgresql_password,
        database=args.postgresql_database)

  def _GetGCSProfile(self, args, release_track):
    # TODO(b/207467120): remove bucket_name arg check.
    if release_track == base.ReleaseTrack.BETA:
      bucket = args.bucket_name
    else:
      bucket = args.bucket

    gcs_profile = self._messages.GcsProfile(bucket=bucket)
    gcs_profile.rootPath = args.root_path if args.root_path else '/'
    return gcs_profile

  def _ParseSslConfig(self, data):
    return self._messages.MysqlSslConfig(
        clientKey=data.get('client_key'),
        clientCertificate=data.get('client_certificate'),
        caCertificate=data.get('ca_certificate'))

  def _ParseMySqlProfile(self, data):
    if not data:
      return {}
    ssl_config = self._ParseSslConfig(data)
    return self._messages.MysqlProfile(
        hostname=data.get('hostname'),
        port=data.get('port'),
        username=data.get('username'),
        password=data.get('password'),
        sslConfig=ssl_config)

  def _ParseOracleProfile(self, data):
    if not data:
      return {}
    return self._messages.OracleProfile(
        hostname=data.get('hostname'),
        port=data.get('port'),
        username=data.get('username'),
        password=data.get('password'),
        databaseService=data.get('database_service'))

  def _ParsePostgresqlProfile(self, data):
    if not data:
      return {}
    return self._messages.PostgresqlProfile(
        hostname=data.get('hostname'),
        port=data.get('port'),
        username=data.get('username'),
        password=data.get('password'),
        database=data.get('database'))

  def _ParseGCSProfile(self, data):
    if not data:
      return {}
    return self._messages.GcsProfile(
        bucket=data.get('bucket_name'), rootPath=data.get('root_path'))

  def _GetForwardSshTunnelConnectivity(self, args):
    return self._messages.ForwardSshTunnelConnectivity(
        hostname=args.forward_ssh_hostname,
        port=args.forward_ssh_port,
        username=args.forward_ssh_username,
        privateKey=args.forward_ssh_private_key,
        password=args.forward_ssh_password)

  def _GetConnectionProfile(self, cp_type, connection_profile_id, args,
                            release_track):
    """Returns a connection profile according to type."""
    labels = labels_util.ParseCreateArgs(
        args, self._messages.ConnectionProfile.LabelsValue)
    connection_profile_obj = self._messages.ConnectionProfile(
        name=connection_profile_id, labels=labels,
        displayName=args.display_name)

    if cp_type == 'MYSQL':
      connection_profile_obj.mysqlProfile = self._GetMySqlProfile(args)
    elif cp_type == 'ORACLE':
      connection_profile_obj.oracleProfile = self._GetOracleProfile(args)
    elif cp_type == 'POSTGRESQL':
      connection_profile_obj.postgresqlProfile = self._GetPostgresqlProfile(
          args)
    elif cp_type == 'GOOGLE-CLOUD-STORAGE':
      connection_profile_obj.gcsProfile = self._GetGCSProfile(
          args, release_track)
    elif cp_type == 'BIGQUERY':
      connection_profile_obj.bigqueryProfile = self._messages.BigQueryProfile()
    else:
      raise exceptions.InvalidArgumentException(
          cp_type,
          'The connection profile type {0} is either unknown or not supported yet.'
          .format(cp_type))

    # TODO(b/207467120): deprecate BETA client.
    if release_track == base.ReleaseTrack.BETA:
      private_connectivity_ref = args.CONCEPTS.private_connection_name.Parse()
    else:
      private_connectivity_ref = args.CONCEPTS.private_connection.Parse()

    if private_connectivity_ref:
      connection_profile_obj.privateConnectivity = self._messages.PrivateConnectivity(
          privateConnection=private_connectivity_ref.RelativeName())
    elif args.forward_ssh_hostname:
      connection_profile_obj.forwardSshConnectivity = self._GetForwardSshTunnelConnectivity(
          args)
    elif args.static_ip_connectivity:
      connection_profile_obj.staticServiceIpConnectivity = {}

    return connection_profile_obj

  def _ParseConnectionProfileObjectFile(
      self, connection_profile_object_file, release_track
  ):
    """Parses a connection-profile-file into the ConnectionProfile message."""
    if release_track != base.ReleaseTrack.BETA:
      return util.ParseMessageAndValidateSchema(
          connection_profile_object_file,
          'ConnectionProfile',
          self._messages.ConnectionProfile,
      )

    data = console_io.ReadFromFileOrStdin(
        connection_profile_object_file, binary=False)
    try:
      connection_profile_data = yaml.load(data)
    except Exception as e:
      raise ds_exceptions.ParseError('Cannot parse YAML:[{0}]'.format(e))

    display_name = connection_profile_data.get('display_name')
    labels = connection_profile_data.get('labels')
    connection_profile_msg = self._messages.ConnectionProfile(
        displayName=display_name,
        labels=labels)

    oracle_profile = self._ParseOracleProfile(
        connection_profile_data.get('oracle_profile', {}))
    mysql_profile = self._ParseMySqlProfile(
        connection_profile_data.get('mysql_profile', {}))
    postgresql_profile = self._ParsePostgresqlProfile(
        connection_profile_data.get('postgresql_profile', {}))
    gcs_profile = self._ParseGCSProfile(
        connection_profile_data.get('gcs_profile', {}))
    if oracle_profile:
      connection_profile_msg.oracleProfile = oracle_profile
    elif mysql_profile:
      connection_profile_msg.mysqlProfile = mysql_profile
    elif postgresql_profile:
      connection_profile_msg.postgresqlProfile = postgresql_profile
    elif gcs_profile:
      connection_profile_msg.gcsProfile = gcs_profile

    if 'static_service_ip_connectivity' in connection_profile_data:
      connection_profile_msg.staticServiceIpConnectivity = connection_profile_data.get(
          'static_service_ip_connectivity')
    elif 'forward_ssh_connectivity' in connection_profile_data:
      connection_profile_msg.forwardSshConnectivity = connection_profile_data.get(
          'forward_ssh_connectivity')
    elif 'private_connectivity' in connection_profile_data:
      connection_profile_msg.privateConnectivity = connection_profile_data.get(
          'private_connectivity')
    else:
      raise ds_exceptions.ParseError(
          'Cannot parse YAML: missing connectivity method.')

    return connection_profile_msg

  def _UpdateForwardSshTunnelConnectivity(
      self, connection_profile,
      args, update_fields):
    """Updates Forward SSH tunnel connectivity config."""
    if args.IsSpecified('forward_ssh_hostname'):
      connection_profile.forwardSshConnectivity.hostname = args.forward_ssh_hostname
      update_fields.append('forwardSshConnectivity.hostname')
    if args.IsSpecified('forward_ssh_port'):
      connection_profile.forwardSshConnectivity.port = args.forward_ssh_port
      update_fields.append('forwardSshConnectivity.port')
    if args.IsSpecified('forward_ssh_username'):
      connection_profile.forwardSshConnectivity.username = args.forward_ssh_username
      update_fields.append('forwardSshConnectivity.username')
    if args.IsSpecified('forward_ssh_private_key'):
      connection_profile.forwardSshConnectivity.privateKey = args.forward_ssh_private_key
      update_fields.append('forwardSshConnectivity.privateKey')
    if args.IsSpecified('forward_ssh_password'):
      connection_profile.forwardSshConnectivity.privateKey = args.forward_ssh_password
      update_fields.append('forwardSshConnectivity.password')

  def _UpdateGCSProfile(self, connection_profile, release_track, args,
                        update_fields):
    """Updates GOOGLE CLOUD STORAGE connection profile."""
    # TODO(b/207467120): remove bucket_name arg check.
    if release_track == base.ReleaseTrack.BETA and args.IsSpecified(
        'bucket_name'):
      connection_profile.gcsProfile.bucket = args.bucket_name
      update_fields.append('gcsProfile.bucket')
    if release_track == base.ReleaseTrack.GA and args.IsSpecified('bucket'):
      connection_profile.gcsProfile.bucket = args.bucket
      update_fields.append('gcsProfile.bucket')
    if args.IsSpecified('root_path'):
      connection_profile.gcsProfile.rootPath = args.root_path
      update_fields.append('gcsProfile.rootPath')

  def _UpdateOracleProfile(self,
                           connection_profile,
                           args,
                           update_fields):
    """Updates Oracle connection profile."""
    if args.IsSpecified('oracle_hostname'):
      connection_profile.oracleProfile.hostname = args.oracle_hostname
      update_fields.append('oracleProfile.hostname')
    if args.IsSpecified('oracle_port'):
      connection_profile.oracleProfile.port = args.oracle_port
      update_fields.append('oracleProfile.port')
    if args.IsSpecified('oracle_username'):
      connection_profile.oracleProfile.username = args.oracle_username
      update_fields.append('oracleProfile.username')
    if args.IsSpecified('oracle_password'):
      connection_profile.oracleProfile.password = args.oracle_password
      update_fields.append('oracleProfile.password')
    if args.IsSpecified('database_service'):
      connection_profile.oracleProfile.databaseService = args.database_service
      update_fields.append('oracleProfile.databaseService')

  def _UpdateMysqlSslConfig(
      self, connection_profile,
      args, update_fields):
    """Updates Mysql SSL config."""
    if args.IsSpecified('client_key'):
      connection_profile.mysqlProfile.sslConfig.clientKey = args.client_key
      update_fields.append('mysqlProfile.sslConfig.clientKey')
    if args.IsSpecified('client_certificate'):
      connection_profile.mysqlProfile.sslConfig.clientCertificate = args.client_certificate
      update_fields.append('mysqlProfile.sslConfig.clientCertificate')
    if args.IsSpecified('ca_certificate'):
      connection_profile.mysqlProfile.sslConfig.caCertificate = args.ca_certificate
      update_fields.append('mysqlProfile.sslConfig.caCertificate')

  def _UpdateMySqlProfile(self,
                          connection_profile,
                          args, update_fields):
    """Updates MySQL connection profile."""
    if args.IsSpecified('mysql_hostname'):
      connection_profile.mysqlProfile.hostname = args.mysql_hostname
      update_fields.append('mysqlProfile.hostname')
    if args.IsSpecified('mysql_port'):
      connection_profile.mysqlProfile.port = args.mysql_port
      update_fields.append('mysqlProfile.port')
    if args.IsSpecified('mysql_username'):
      connection_profile.mysqlProfile.username = args.mysql_username
      update_fields.append('mysqlProfile.username')
    if args.IsSpecified('mysql_password'):
      connection_profile.mysqlProfile.password = args.mysql_password
      update_fields.append('mysqlProfile.password')

    self._UpdateMysqlSslConfig(connection_profile, args, update_fields)

  def _UpdatePostgresqlProfile(self, connection_profile, args, update_fields):
    """Updates Postgresql connection profile."""
    if args.IsSpecified('postgresql_hostname'):
      connection_profile.postgresqlProfile.hostname = args.postgresql_hostname
      update_fields.append('postgresqlProfile.hostname')
    if args.IsSpecified('postgresql_port'):
      connection_profile.postgresqlProfile.port = args.postgresql_port
      update_fields.append('postgresqlProfile.port')
    if args.IsSpecified('postgresql_username'):
      connection_profile.postgresqlProfile.username = args.postgresql_username
      update_fields.append('postgresqlProfile.username')
    if args.IsSpecified('postgresql_password'):
      connection_profile.postgresqlProfile.password = args.postgresql_password
      update_fields.append('postgresqlProfile.password')
    if args.IsSpecified('postgresql_database'):
      connection_profile.postgresqlProfile.database = args.postgresql_database
      update_fields.append('postgresqlProfile.database')

  def _GetExistingConnectionProfile(self, name):
    get_req = self._messages.DatastreamProjectsLocationsConnectionProfilesGetRequest(
        name=name
    )
    return self._service.Get(get_req)

  def _UpdateLabels(self, connection_profile, args):
    """Updates labels of the connection profile."""
    add_labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    remove_labels = labels_util.GetRemoveLabelsListFromArgs(args)
    value_type = self._messages.ConnectionProfile.LabelsValue
    update_result = labels_util.Diff(
        additions=add_labels,
        subtractions=remove_labels,
        clear=args.clear_labels
    ).Apply(value_type, connection_profile.labels)
    if update_result.needs_update:
      connection_profile.labels = update_result.labels

  def _GetUpdatedConnectionProfile(self, connection_profile, cp_type,
                                   release_track, args):
    """Returns updated connection profile and list of updated fields."""
    update_fields = []
    if args.IsSpecified('display_name'):
      connection_profile.displayName = args.display_name
      update_fields.append('displayName')

    if cp_type == 'MYSQL':
      self._UpdateMySqlProfile(
          connection_profile, args, update_fields)
    elif cp_type == 'ORACLE':
      self._UpdateOracleProfile(connection_profile, args, update_fields)
    elif cp_type == 'POSTGRESQL':
      self._UpdatePostgresqlProfile(connection_profile, args, update_fields)
    elif cp_type == 'GOOGLE-CLOUD-STORAGE':
      self._UpdateGCSProfile(connection_profile, release_track, args,
                             update_fields)
    elif cp_type == 'BIGQUERY':
      # There are currently no parameters that can be updated in a bigquery CP.
      pass
    else:
      raise exceptions.InvalidArgumentException(
          cp_type,
          'The connection profile type {0} is either unknown or not supported yet.'
          .format(cp_type))

    # TODO(b/207467120): deprecate BETA client.
    if release_track == base.ReleaseTrack.BETA:
      private_connectivity_ref = args.CONCEPTS.private_connection_name.Parse()
    else:
      private_connectivity_ref = args.CONCEPTS.private_connection.Parse()

    if private_connectivity_ref:
      connection_profile.privateConnectivity = self._messages.PrivateConnectivity(
          privateConnectionName=private_connectivity_ref.RelativeName())
      update_fields.append('privateConnectivity')
    elif args.forward_ssh_hostname:
      self._UpdateForwardSshTunnelConnectivity(
          connection_profile, args, update_fields)
    elif args.static_ip_connectivity:
      connection_profile.staticServiceIpConnectivity = {}
      update_fields.append('staticServiceIpConnectivity')

    self._UpdateLabels(connection_profile, args)
    return connection_profile, update_fields

  def Create(self,
             parent_ref,
             connection_profile_id,
             cp_type,
             release_track,
             args=None):
    """Creates a connection profile.

    Args:
      parent_ref: a Resource reference to a parent datastream.projects.locations
        resource for this connection profile.
      connection_profile_id: str, the name of the resource to create.
      cp_type: str, the type of the connection profile ('MYSQL', ''
      release_track: Some arguments are added based on the command release
        track.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the connection profile.
    """
    self._ValidateArgs(args)

    connection_profile = self._GetConnectionProfile(cp_type,
                                                    connection_profile_id, args,
                                                    release_track)
    # TODO(b/207467120): only use flags from args.
    force = False
    if release_track == base.ReleaseTrack.BETA or args.force:
      force = True

    request_id = util.GenerateRequestId()
    create_req_type = self._messages.DatastreamProjectsLocationsConnectionProfilesCreateRequest
    create_req = create_req_type(
        connectionProfile=connection_profile,
        connectionProfileId=connection_profile.name,
        parent=parent_ref,
        requestId=request_id,
        force=force)

    return self._service.Create(create_req)

  def Update(self, name, cp_type, release_track, args=None):
    """Updates a connection profile.

    Args:
      name: str, the reference of the connection profile to
          update.
      cp_type: str, the type of the connection profile ('MYSQL', 'ORACLE')
      release_track: Some arguments are added based on the command release
        track.
      args: argparse.Namespace, The arguments that this command was
          invoked with.

    Returns:
      Operation: the operation for updating the connection profile.
    """
    self._ValidateArgs(args)

    current_cp = self._GetExistingConnectionProfile(name)

    updated_cp, update_fields = self._GetUpdatedConnectionProfile(
        current_cp, cp_type, release_track, args)

    # TODO(b/207467120): only use flags from args.
    force = False
    if release_track == base.ReleaseTrack.BETA or args.force:
      force = True

    request_id = util.GenerateRequestId()
    update_req_type = self._messages.DatastreamProjectsLocationsConnectionProfilesPatchRequest
    update_req = update_req_type(
        connectionProfile=updated_cp,
        name=updated_cp.name,
        updateMask=','.join(update_fields),
        requestId=request_id,
        force=force)

    return self._service.Patch(update_req)

  def List(self, project_id, args):
    """Get the list of connection profiles in a project.

    Args:
      project_id: The project ID to retrieve
      args: parsed command line arguments

    Returns:
      An iterator over all the matching connection profiles.
    """
    location_ref = self._resource_parser.Create(
        'datastream.projects.locations',
        projectsId=project_id,
        locationsId=args.location)

    list_req_type = self._messages.DatastreamProjectsLocationsConnectionProfilesListRequest
    list_req = list_req_type(
        parent=location_ref.RelativeName(),
        filter=args.filter,
        orderBy=','.join(args.sort_by) if args.sort_by else None)

    return list_pager.YieldFromList(
        service=self._client.projects_locations_connectionProfiles,
        request=list_req,
        limit=args.limit,
        batch_size=args.page_size,
        field='connectionProfiles',
        batch_size_attribute='pageSize')

  def Discover(self, parent_ref, release_track, args):
    """Discover a connection profile.

    Args:
      parent_ref: a Resource reference to a parent datastream.projects.locations
        resource for this connection profile.
      release_track: Some arguments are added based on the command release
        track.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for discovering the connection profile.
    """
    request = self._messages.DiscoverConnectionProfileRequest()
    if args.connection_profile_name:
      connection_profile_ref = args.CONCEPTS.connection_profile_name.Parse()
      request.connectionProfileName = connection_profile_ref.RelativeName()
    elif args.connection_profile_object_file:
      request.connectionProfile = self._ParseConnectionProfileObjectFile(
          args.connection_profile_object_file, release_track
      )

    if args.recursive or args.full_hierarchy:
      request.fullHierarchy = True
    elif args.recursive_depth:
      request.hierarchyDepth = (int)(args.recursive_depth)
    elif args.hierarchy_depth:
      request.hierarchyDepth = (int)(args.hierarchy_depth)
    else:
      request.fullHierarchy = False

    if args.mysql_rdbms_file:
      request.mysqlRdbms = util.ParseMysqlRdbmsFile(self._messages,
                                                    args.mysql_rdbms_file,
                                                    release_track)
    elif args.oracle_rdbms_file:
      request.oracleRdbms = util.ParseOracleRdbmsFile(self._messages,
                                                      args.oracle_rdbms_file,
                                                      release_track)
    elif args.postgresql_rdbms_file:
      request.postgresqlRdbms = util.ParsePostgresqlRdbmsFile(
          self._messages, args.postgresql_rdbms_file)
    discover_req_type = self._messages.DatastreamProjectsLocationsConnectionProfilesDiscoverRequest
    discover_req = discover_req_type(
        discoverConnectionProfileRequest=request, parent=parent_ref)
    return self._service.Discover(discover_req)

  def GetUri(self, name):
    """Get the URL string for a connection profile.

    Args:
      name: connection profile's full name.

    Returns:
      URL of the connection profile resource
    """

    uri = self._resource_parser.ParseRelativeName(
        name, collection='datastream.projects.locations.connectionProfiles')
    return uri.SelfLink()
