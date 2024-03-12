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

"""`gcloud api-gateway api-configs create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import cloudsdk.google.protobuf.descriptor_pb2 as descriptor

from googlecloudsdk.api_lib.api_gateway import api_configs as api_configs_client
from googlecloudsdk.api_lib.api_gateway import apis as apis_client
from googlecloudsdk.api_lib.api_gateway import base as apigateway_base
from googlecloudsdk.api_lib.api_gateway import operations as operations_client
from googlecloudsdk.api_lib.endpoints import services_util as endpoints
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.api_gateway import common_flags
from googlecloudsdk.command_lib.api_gateway import operations_util
from googlecloudsdk.command_lib.api_gateway import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core.util import http_encoding

MAX_SERVICE_CONFIG_ID_LENGTH = 50


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Add a new config to an API."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          NOTE: If the specified API does not exist it will be created.""",
      'EXAMPLES':
          """\
        To create an API config for the API 'my-api' with an OpenAPI spec, run:

          $ {command} my-config --api=my-api --openapi-spec=path/to/openapi_spec.yaml
        """,
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.AddDisplayNameArg(parser)
    labels_util.AddCreateLabelsFlags(parser)
    resource_args.AddApiConfigResourceArg(parser, 'created', positional=True)
    common_flags.AddBackendAuthServiceAccountFlag(parser)

    group = parser.add_group(mutex=True,
                             required=True,
                             help='Configuration files for the API.')
    group.add_argument(
        '--openapi-spec',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        help=('The OpenAPI v2 specifications containing service '
              'configuration information, and API specification for the gateway'
              '.'))

    group.add_argument(
        '--grpc-files',
        type=arg_parsers.ArgList(),
        metavar='FILE',
        help=('Files describing the GRPC service. Google Service Configuration '
              'files in JSON or YAML formats as well as Proto '
              'descriptors should be listed.'))

  def Run(self, args):
    apis = apis_client.ApiClient()
    api_configs = api_configs_client.ApiConfigClient()
    ops = operations_client.OperationsClient()

    api_config_ref = args.CONCEPTS.api_config.Parse()
    api_ref = api_config_ref.Parent()

    # Check to see if Api exists, create if not
    if not apis.DoesExist(api_ref):
      res = apis.Create(api_ref)
      operations_util.PrintOperationResult(
          res.name, ops,
          wait_string='Waiting for API [{}] to be created'.format(
              api_ref.Name()))

    open_api_docs = []
    svc_configs = []
    grpc_svc_defs = []
    # When we add gRPC support back, we can remove the 'hasattr' call.
    if hasattr(args, 'grpc_files') and args.grpc_files:
      args.grpc_files = [f.strip() for f in args.grpc_files]
      svc_configs, grpc_svc_defs = self.__GrpcMessages(args.grpc_files)
    else:
      args.openapi_spec = [f.strip() for f in args.openapi_spec]
      open_api_docs = self.__OpenApiMessage(args.openapi_spec)

    # Create ApiConfig object.
    # Only piece affected by async right now
    resp = api_configs.Create(api_config_ref,
                              labels=args.labels,
                              display_name=args.display_name,
                              backend_auth=args.backend_auth_service_account,
                              managed_service_configs=svc_configs,
                              grpc_service_defs=grpc_svc_defs,
                              open_api_docs=open_api_docs)

    wait = 'Waiting for API Config [{0}] to be created for API [{1}]'.format(
        api_config_ref.Name(), api_ref.Name())

    return operations_util.PrintOperationResult(
        resp.name,
        ops,
        service=api_configs.service,
        wait_string=wait,
        is_async=args.async_)

  def __OpenApiMessage(self, open_api_specs):
    """Parses the Open API scoped configuraiton files into their necessary API Gateway message types.

    Args:
      open_api_specs: Specs to be used with the API Gateway API Configuration

    Returns:
      List of ApigatewayApiConfigOpenApiDocument messages

    Raises:
      BadFileException: If there is something wrong with the files
    """
    messages = apigateway_base.GetMessagesModule()
    config_files = []
    for config_file in open_api_specs:
      config_contents = endpoints.ReadServiceConfigFile(config_file)

      config_dict = self.__ValidJsonOrYaml(config_file, config_contents)
      if config_dict:
        if 'swagger' in config_dict:
          # Always use YAML for OpenAPI because JSON is a subset of YAML.
          document = self.__MakeApigatewayApiConfigFileMessage(config_contents,
                                                               config_file)
          config_files.append(messages.ApigatewayApiConfigOpenApiDocument(
              document=document))
        elif 'openapi' in config_dict:
          raise calliope_exceptions.BadFileException(
              'API Gateway does not currently support OpenAPI v3 configurations.'
              )
        else:
          raise calliope_exceptions.BadFileException(
              'The file {} is not a valid OpenAPI v2 configuration file.'
              .format(config_file))
      else:
        raise calliope_exceptions.BadFileException(
            'OpenAPI files should be of JSON or YAML format')
    return config_files

  def __GrpcMessages(self, files):
    """Parses the GRPC scoped configuraiton files into their necessary API Gateway message types.

    Args:
      files: Files to be sent in as managed service configs and GRPC service
      definitions

    Returns:
      List of ApigatewayApiConfigFileMessage, list of
      ApigatewayApiConfigGrpcServiceDefinition messages

    Raises:
      BadFileException: If there is something wrong with the files
    """

    grpc_service_definitions = []
    service_configs = []
    for config_file in files:
      config_contents = endpoints.ReadServiceConfigFile(config_file)
      config_dict = self.__ValidJsonOrYaml(config_file, config_contents)
      if config_dict:
        if config_dict.get('type') == 'google.api.Service':
          service_configs.append(
              self.__MakeApigatewayApiConfigFileMessage(config_contents,
                                                        config_file))
        else:
          raise calliope_exceptions.BadFileException(
              'The file {} is not a valid api configuration file. The '
              'configuration type is expected to be of "google.api.Service".'.
              format(config_file))
      elif endpoints.IsProtoDescriptor(config_file):
        grpc_service_definitions.append(
            self.__MakeApigatewayApiConfigGrpcServiceDefinitionMessage(
                config_contents, config_file))
      elif endpoints.IsRawProto(config_file):
        raise calliope_exceptions.BadFileException(
            ('[{}] cannot be used as it is an uncompiled proto'
             ' file. However, uncompiled proto files can be included for'
             ' display purposes when compiled as a source for a passed in proto'
             ' descriptor.'
             ).format(config_file))
      else:
        raise calliope_exceptions.BadFileException(
            ('Could not determine the content type of file [{0}]. Supported '
             'extensions are .descriptor .json .pb .yaml and .yml'
            ).format(config_file))
    return service_configs, grpc_service_definitions

  def __ValidJsonOrYaml(self, file_name, file_contents):
    """Whether or not this is a valid json or yaml file.

    Args:
      file_name: Name of the file
      file_contents: data for the file

    Returns:
      Boolean for whether or not this is a JSON or YAML

    Raises:
      BadFileException: File appears to be json or yaml but cannot be parsed.
    """
    if endpoints.FilenameMatchesExtension(file_name,
                                          ['.json', '.yaml', '.yml']):
      config_dict = endpoints.LoadJsonOrYaml(file_contents)
      if config_dict:
        return config_dict
      else:
        raise calliope_exceptions.BadFileException(
            'Could not read JSON or YAML from config file '
            '[{0}].'.format(file_name))
    else:
      return False

  def __MakeApigatewayApiConfigFileMessage(self, file_contents, filename,
                                           is_binary=False):
    """Constructs a ConfigFile message from a config file.

    Args:
      file_contents: The contents of the config file.
      filename: The path to the config file.
      is_binary: If set to true, the file_contents won't be encoded.

    Returns:
      The constructed ApigatewayApiConfigFile message.
    """

    messages = apigateway_base.GetMessagesModule()
    if not is_binary:
      # File is human-readable text, not binary; needs to be encoded.
      file_contents = http_encoding.Encode(file_contents)
    return messages.ApigatewayApiConfigFile(
        contents=file_contents,
        path=os.path.basename(filename),
    )

  def __MakeApigatewayApiConfigGrpcServiceDefinitionMessage(self,
                                                            proto_desc_contents,
                                                            proto_desc_file):
    """Constructs a GrpcServiceDefinition message from a proto descriptor and the provided list of input files.

    Args:
      proto_desc_contents: The contents of the proto descriptor file.
      proto_desc_file: The path to the proto descriptor file.

    Returns:
      The constructed ApigatewayApiConfigGrpcServiceDefinition message.
    """

    messages = apigateway_base.GetMessagesModule()
    fds = descriptor.FileDescriptorSet.FromString(proto_desc_contents)
    proto_desc_dir = os.path.dirname(proto_desc_file)
    grpc_sources = []
    included_source_paths = []
    not_included_source_paths = []

    # Iterate over the file descriptors dependency files and attempt to resolve
    # the gRPC source proto files from it.
    for file_descriptor in fds.file:
      source_path = os.path.join(proto_desc_dir, file_descriptor.name)
      if os.path.exists(source_path):
        source_contents = endpoints.ReadServiceConfigFile(source_path)
        file = self.__MakeApigatewayApiConfigFileMessage(source_contents,
                                                         source_path)
        included_source_paths.append(source_path)
        grpc_sources.append(file)
      else:
        not_included_source_paths.append(source_path)

    if not_included_source_paths:
      log.warning('Proto descriptor\'s source protos [{0}] were not found on'
                  ' the file system and will not be included in the submitted'
                  ' GRPC service definition. If you meant to include these'
                  ' files, ensure the proto compiler was invoked in the same'
                  ' directory where the proto descriptor [{1}] now resides.'.
                  format(', '.join(not_included_source_paths), proto_desc_file))

    # Log which files are being passed in as to ensure the user is informed of
    # all files being passed into the gRPC service definition.
    if included_source_paths:
      log.info('Added the source protos [{0}] to the GRPC service definition'
               ' for the provided proto descriptor [{1}].'.
               format(', '.join(included_source_paths), proto_desc_file))

    file_descriptor_set = self.__MakeApigatewayApiConfigFileMessage(
        proto_desc_contents, proto_desc_file, True)
    return messages.ApigatewayApiConfigGrpcServiceDefinition(
                fileDescriptorSet=file_descriptor_set, source=grpc_sources)
