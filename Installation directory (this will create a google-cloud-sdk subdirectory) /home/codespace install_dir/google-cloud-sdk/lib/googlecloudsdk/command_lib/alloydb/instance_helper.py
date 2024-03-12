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
"""Helper functions for constructing and validating AlloyDB instance requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.parser_errors import DetailedArgumentError
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties


def ConstructCreateRequestFromArgsGA(
    client, alloydb_messages, project_ref, args
):
  """Validates command line input arguments and passes parent's resources for GA track.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    project_ref: parent resource path of the resource being created
    args: Command line input arguments.

  Returns:
    Fully-constructed request to create an AlloyDB instance.
  """
  instance_resource = _ConstructInstanceFromArgs(client, alloydb_messages, args)

  return (
      alloydb_messages.AlloydbProjectsLocationsClustersInstancesCreateRequest(
          instance=instance_resource,
          instanceId=args.instance,
          parent=project_ref.RelativeName(),
      )
  )


def ConstructCreateRequestFromArgsBeta(
    client, alloydb_messages, project_ref, args
):
  """Validates command line input arguments and passes parent's resources for beta tracks.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    project_ref: Parent resource path of the resource being created
    args: Command line input arguments.

  Returns:
    Fully-constructed request to create an AlloyDB instance.
  """
  instance_resource = _ConstructInstanceFromArgsBeta(
      client, alloydb_messages, args)

  return (
      alloydb_messages.AlloydbProjectsLocationsClustersInstancesCreateRequest(
          instance=instance_resource,
          instanceId=args.instance,
          parent=project_ref.RelativeName(),
      )
  )


def ConstructCreateRequestFromArgsAlpha(
    client, alloydb_messages, project_ref, args
):
  """Validates command line input arguments and passes parent's resources for alpha track.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    project_ref: Parent resource path of the resource being created
    args: Command line input arguments.

  Returns:
    Fully-constructed request to create an AlloyDB instance.
  """
  instance_resource = _ConstructInstanceFromArgsAlpha(
      client, alloydb_messages, args)

  return (
      alloydb_messages.AlloydbProjectsLocationsClustersInstancesCreateRequest(
          instance=instance_resource,
          instanceId=args.instance,
          parent=project_ref.RelativeName(),
      )
  )


def _ConstructInstanceFromArgs(client, alloydb_messages, args):
  """Validates command line input arguments and passes parent's resources to create an AlloyDB instance.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    args: Command line input arguments.

  Returns:
    An AlloyDB instance to create with the specified command line arguments.
  """
  instance_resource = alloydb_messages.Instance()

  # set availability-type if provided
  instance_resource.availabilityType = ParseAvailabilityType(
      alloydb_messages, args.availability_type)
  instance_resource.machineConfig = alloydb_messages.MachineConfig(
      cpuCount=args.cpu_count)
  instance_ref = client.resource_parser.Create(
      'alloydb.projects.locations.clusters.instances',
      projectsId=properties.VALUES.core.project.GetOrFail,
      locationsId=args.region,
      clustersId=args.cluster,
      instancesId=args.instance)
  instance_resource.name = instance_ref.RelativeName()

  instance_resource.databaseFlags = labels_util.ParseCreateArgs(
      args,
      alloydb_messages.Instance.DatabaseFlagsValue,
      labels_dest='database_flags')
  instance_resource.instanceType = _ParseInstanceType(alloydb_messages,
                                                      args.instance_type)

  if (
      instance_resource.instanceType
      == alloydb_messages.Instance.InstanceTypeValueValuesEnum.READ_POOL
  ):
    instance_resource.readPoolConfig = alloydb_messages.ReadPoolConfig(
        nodeCount=args.read_pool_node_count
    )

  instance_resource.queryInsightsConfig = _QueryInsightsConfig(
      alloydb_messages,
      insights_config_query_string_length=args.insights_config_query_string_length,
      insights_config_query_plans_per_minute=args.insights_config_query_plans_per_minute,
      insights_config_record_application_tags=args.insights_config_record_application_tags,
      insights_config_record_client_address=args.insights_config_record_client_address,
  )

  instance_resource.clientConnectionConfig = _ClientConnectionConfig(
      alloydb_messages,
      args.ssl_mode,
      args.require_connectors,
  )

  return instance_resource


def _ConstructInstanceFromArgsBeta(client, alloydb_messages, args):
  """Validates command line input arguments and passes parent's resources to create an AlloyDB instance for beta track.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    args: Command line input arguments.

  Returns:
    An AlloyDB instance to create with the specified command line arguments.
  """
  instance_resource = _ConstructInstanceFromArgs(client, alloydb_messages, args)
  instance_resource.networkConfig = _NetworkConfig(
      alloydb_messages,
      args.assign_inbound_public_ip,
      None,
  )
  return instance_resource


def _ConstructInstanceFromArgsAlpha(client, alloydb_messages, args):
  """Validates command line input arguments and passes parent's resources to create an AlloyDB instance for alpha track.

  Args:
    client: Client for api_utils.py class.
    alloydb_messages: Messages module for the API client.
    args: Command line input arguments.

  Returns:
    An AlloyDB instance to create with the specified command line arguments.
  """
  instance_resource = _ConstructInstanceFromArgsBeta(
      client, alloydb_messages, args)
  return instance_resource


def ConstructPatchRequestFromArgs(alloydb_messages, instance_ref, args):
  """Constructs the request to update an AlloyDB instance.

  Args:
    alloydb_messages: Messages module for the API client.
    instance_ref: parent resource path of the resource being updated
    args: Command line input arguments.

  Returns:
    Fully-constructed request to update an AlloyDB instance.
  """
  instance_resource, paths = ConstructInstanceAndUpdatePathsFromArgs(
      alloydb_messages, instance_ref, args)
  mask = ','.join(paths) if paths else None

  return (
      alloydb_messages.AlloydbProjectsLocationsClustersInstancesPatchRequest(
          instance=instance_resource,
          name=instance_ref.RelativeName(),
          updateMask=mask))


def ConstructInstanceAndUpdatePathsFromArgs(
    alloydb_messages, instance_ref, args):
  """Validates command line arguments and creates the instance and update paths.

  Args:
    alloydb_messages: Messages module for the API client.
    instance_ref: parent resource path of the resource being updated
    args: Command line input arguments.

  Returns:
    An AlloyDB instance and paths for update.
  """
  availability_type_path = 'availabilityType'
  database_flags_path = 'databaseFlags'
  cpu_count_path = 'machineConfig.cpuCount'
  read_pool_node_count_path = 'readPoolConfig.nodeCount'
  insights_config_query_string_length_path = (
      'queryInsightsConfig.queryStringLength'
  )
  insights_config_query_plans_per_minute_path = (
      'queryInsightsConfig.queryPlansPerMinute'
  )
  insights_config_record_application_tags_path = (
      'queryInsightsConfig.recordApplicationTags'
  )
  insights_config_record_client_address_path = (
      'queryInsightsConfig.recordClientAddress'
  )

  instance_resource = alloydb_messages.Instance()
  paths = []

  instance_resource.name = instance_ref.RelativeName()

  availability_type = ParseAvailabilityType(
      alloydb_messages, args.availability_type)
  if availability_type:
    instance_resource.availabilityType = availability_type
    paths.append(availability_type_path)

  database_flags = labels_util.ParseCreateArgs(
      args,
      alloydb_messages.Instance.DatabaseFlagsValue,
      labels_dest='database_flags')
  if database_flags:
    instance_resource.databaseFlags = database_flags
    paths.append(database_flags_path)

  if args.cpu_count:
    instance_resource.machineConfig = alloydb_messages.MachineConfig(
        cpuCount=args.cpu_count)
    paths.append(cpu_count_path)

  if args.read_pool_node_count:
    instance_resource.readPoolConfig = alloydb_messages.ReadPoolConfig(
        nodeCount=args.read_pool_node_count)
    paths.append(read_pool_node_count_path)

  if args.insights_config_query_string_length:
    paths.append(insights_config_query_string_length_path)
  if args.insights_config_query_plans_per_minute:
    paths.append(insights_config_query_plans_per_minute_path)
  if args.insights_config_record_application_tags is not None:
    paths.append(insights_config_record_application_tags_path)
  if args.insights_config_record_client_address is not None:
    paths.append(insights_config_record_client_address_path)

  instance_resource.queryInsightsConfig = _QueryInsightsConfig(
      alloydb_messages,
      args.insights_config_query_string_length,
      args.insights_config_query_plans_per_minute,
      args.insights_config_record_application_tags,
      args.insights_config_record_client_address,
  )

  # Check if require_connectors is set to True/False, then update
  if args.require_connectors is not None:
    require_connectors_path = 'clientConnectionConfig.requireConnectors'
    paths.append(require_connectors_path)
  if args.ssl_mode:
    ssl_mode_path = 'clientConnectionConfig.sslConfig.sslMode'
    paths.append(ssl_mode_path)
  if args.require_connectors is not None or args.ssl_mode:
    instance_resource.clientConnectionConfig = _ClientConnectionConfig(
        alloydb_messages, args.ssl_mode, args.require_connectors
    )

  return instance_resource, paths


def _QueryInsightsConfig(
    alloydb_messages,
    insights_config_query_string_length=None,
    insights_config_query_plans_per_minute=None,
    insights_config_record_application_tags=None,
    insights_config_record_client_address=None,
):
  """Generates the insights config for the instance.

  Args:
    alloydb_messages: module, Message module for the API client.
    insights_config_query_string_length: number, length of the query string to
      be stored.
    insights_config_query_plans_per_minute: number, number of query plans to
      sample every minute.
    insights_config_record_application_tags: boolean, True if application tags
      should be recorded.
    insights_config_record_client_address: boolean, True if client address
      should be recorded.

  Returns:
    alloydb_messages.QueryInsightsInstanceConfig or None
  """

  should_generate_config = any([
      insights_config_query_string_length is not None,
      insights_config_query_plans_per_minute is not None,
      insights_config_record_application_tags is not None,
      insights_config_record_client_address is not None,
  ])
  if not should_generate_config:
    return None

  # Config exists, generate insights config.
  insights_config = alloydb_messages.QueryInsightsInstanceConfig()
  if insights_config_query_string_length is not None:
    insights_config.queryStringLength = insights_config_query_string_length
  if insights_config_query_plans_per_minute is not None:
    insights_config.queryPlansPerMinute = insights_config_query_plans_per_minute
  if insights_config_record_application_tags is not None:
    insights_config.recordApplicationTags = (
        insights_config_record_application_tags
    )
  if insights_config_record_client_address is not None:
    insights_config.recordClientAddress = insights_config_record_client_address

  return insights_config


def _ClientConnectionConfig(
    alloydb_messages,
    ssl_mode=None,
    require_connectors=None,
):
  """Generates the client connection config for the instance.

  Args:
    alloydb_messages: module, Message module for the API client.
    ssl_mode: string, SSL mode to use when connecting to the database.
    require_connectors: boolean, whether or not to enforce connections to the
      database to go through a connector (ex: Auth Proxy).

  Returns:
    alloydb_messages.ClientConnectionConfig
  """

  should_generate_config = any([
      ssl_mode is not None,
      require_connectors is not None,
  ])
  if not should_generate_config:
    return None

  # Config exists, generate client connection config.
  client_connection_config = alloydb_messages.ClientConnectionConfig()
  client_connection_config.requireConnectors = require_connectors
  ssl_config = alloydb_messages.SslConfig()
  # Set SSL mode if provided
  ssl_config.sslMode = _ParseSSLMode(alloydb_messages, ssl_mode)
  client_connection_config.sslConfig = ssl_config

  return client_connection_config


def ParseAvailabilityType(alloydb_messages, availability_type):
  if availability_type:
    return alloydb_messages.Instance.AvailabilityTypeValueValuesEnum.lookup_by_name(
        availability_type.upper())
  return None


def _ParseInstanceType(alloydb_messages, instance_type):
  if instance_type:
    return alloydb_messages.Instance.InstanceTypeValueValuesEnum.lookup_by_name(
        instance_type.upper())
  return None


def _ParseUpdateMode(alloydb_messages, update_mode):
  if update_mode:
    return alloydb_messages.UpdatePolicy.ModeValueValuesEnum.lookup_by_name(
        update_mode.upper())
  return None


def _ParseSSLMode(alloydb_messages, ssl_mode):
  if ssl_mode == 'ENCRYPTED_ONLY':
    return alloydb_messages.SslConfig.SslModeValueValuesEnum.ENCRYPTED_ONLY
  elif ssl_mode == 'ALLOW_UNENCRYPTED_AND_ENCRYPTED':
    return (
        alloydb_messages.SslConfig.SslModeValueValuesEnum.ALLOW_UNENCRYPTED_AND_ENCRYPTED
    )
  return None


def _NetworkConfig(
    alloydb_messages,
    assign_inbound_public_ip=None,
    authorized_external_networks=None,
):
  """Generates the instance network config for the instance.

  Args:
    alloydb_messages: module, Message module for the API client.
    assign_inbound_public_ip: string, whether or not to enable Public-IP.
    authorized_external_networks: list, list of external networks authorized to
      access the instance.

  Returns:
    alloydb_messages.NetworkConfig
  """

  should_generate_config = any([
      assign_inbound_public_ip,
      authorized_external_networks is not None,
  ])
  if not should_generate_config:
    return None

  # Config exists, generate instance network config.
  instance_network_config = alloydb_messages.InstanceNetworkConfig()

  if assign_inbound_public_ip:
    instance_network_config.enablePublicIp = _ParseAssignInboundPublicIp(
        assign_inbound_public_ip
    )
  if authorized_external_networks is not None:
    if (assign_inbound_public_ip is not None
        and not instance_network_config.enablePublicIp):
      raise DetailedArgumentError('Cannot update an instance\'s authorized '
                                  'networks and disable Public-IP. You must do '
                                  'one or the other. Note, that disabling '
                                  'Public-IP will clear the list of authorized '
                                  'networks.')
    instance_network_config.authorizedExternalNetworks = (
        _ParseAuthorizedExternalNetworks(
            alloydb_messages,
            authorized_external_networks,
            instance_network_config.enablePublicIp
        )
    )
  return instance_network_config


def _ParseAssignInboundPublicIp(assign_inbound_public_ip):
  """Parses the assign_inbound_public_ip flag.

  Args:
    assign_inbound_public_ip: string, the Public-IP mode to use.

  Returns:
    boolean, whether or not Public-IP is enabled.

  Raises:
    ValueError if try to use any other value besides NO_PUBLIC_IP during
    instance creation, or if use an unrecognized argument.
  """
  if assign_inbound_public_ip == 'NO_PUBLIC_IP':
    return False
  if assign_inbound_public_ip == 'ASSIGN_IPV4':
    return True
  raise DetailedArgumentError(
      'Unrecognized argument. Please use NO_PUBLIC_IP or ASSIGN_IPV4.'
  )


def _ParseAuthorizedExternalNetworks(
    alloydb_messages, authorized_external_networks, public_ip_enabled
):
  """Parses the authorized_external_networks flag.

  Args:
    alloydb_messages: Messages module for the API client.
    authorized_external_networks: list, list of authorized networks.
    public_ip_enabled: boolean, whether or not Public-IP is enabled.

  Returns:
    list of alloydb_messages.AuthorizedNetwork
  """
  auth_networks = []
  if public_ip_enabled is not None and not public_ip_enabled:
    return auth_networks
  for network in authorized_external_networks:
    network = alloydb_messages.AuthorizedNetwork(
        cidrRange=str(network)
    )
    auth_networks.append(network)
  return auth_networks


def ConstructPatchRequestFromArgsBeta(alloydb_messages, instance_ref, args):
  """Constructs the request to update an AlloyDB instance."""
  instance_resource, paths = ConstructInstanceAndUpdatePathsFromArgsBeta(
      alloydb_messages, instance_ref, args
  )
  mask = ','.join(paths) if paths else None

  return alloydb_messages.AlloydbProjectsLocationsClustersInstancesPatchRequest(
      instance=instance_resource,
      name=instance_ref.RelativeName(),
      updateMask=mask,
  )


def ConstructPatchRequestFromArgsAlpha(alloydb_messages, instance_ref, args):
  """Constructs the request to update an AlloyDB instance."""
  instance_resource, paths = ConstructInstanceAndUpdatePathsFromArgsAlpha(
      alloydb_messages, instance_ref, args
  )
  mask = ','.join(paths) if paths else None

  return alloydb_messages.AlloydbProjectsLocationsClustersInstancesPatchRequest(
      instance=instance_resource,
      name=instance_ref.RelativeName(),
      updateMask=mask,
  )


def ConstructInstanceAndUpdatePathsFromArgsBeta(
    alloydb_messages, instance_ref, args
):
  """Validates command line arguments and creates the instance and update paths for beta track.

  Args:
    alloydb_messages: Messages module for the API client.
    instance_ref: parent resource path of the resource being updated
    args: Command line input arguments.

  Returns:
    An AlloyDB instance and paths for update.
  """
  instance_resource, paths = ConstructInstanceAndUpdatePathsFromArgs(
      alloydb_messages, instance_ref, args
  )

  if args.update_mode:
    instance_resource.updatePolicy = alloydb_messages.UpdatePolicy(
        mode=_ParseUpdateMode(alloydb_messages, args.update_mode)
    )
    update_mode_path = 'updatePolicy.mode'
    paths.append(update_mode_path)

  if (args.assign_inbound_public_ip
      or args.authorized_external_networks is not None):
    instance_resource.networkConfig = _NetworkConfig(
        alloydb_messages,
        args.assign_inbound_public_ip,
        args.authorized_external_networks,
    )
    # If we are disabling public ip then update the whole networkConfig as we
    # also need to clear the list of authorized networks
    if (args.assign_inbound_public_ip
        and not instance_resource.networkConfig.enablePublicIp):
      paths.append('networkConfig')
    else:
      if args.assign_inbound_public_ip:
        paths.append('networkConfig.enablePublicIp')
      if args.authorized_external_networks is not None:
        paths.append('networkConfig.authorizedExternalNetworks')

  return instance_resource, paths


def ConstructInstanceAndUpdatePathsFromArgsAlpha(
    alloydb_messages, instance_ref, args
):
  """Validates command line arguments and creates the instance and update paths for alpha track.

  Args:
    alloydb_messages: Messages module for the API client.
    instance_ref: parent resource path of the resource being updated
    args: Command line input arguments.

  Returns:
    An AlloyDB instance and paths for update.
  """
  instance_resource, paths = ConstructInstanceAndUpdatePathsFromArgsBeta(
      alloydb_messages, instance_ref, args
  )

  return instance_resource, paths
