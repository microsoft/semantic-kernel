# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""endpoints deploy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.endpoints import config_reporter
from googlecloudsdk.api_lib.endpoints import exceptions
from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as services_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import http_encoding

import six.moves.urllib.parse


ADVICE_STRING = ('Advice found for changes in the new service config. If this '
                 'is a --validate-only run, the config push would have failed. '
                 'See the outputted report for failure reason(s). If this is '
                 'not a --validate-only run and you would like to ignore these '
                 'warnings, rerun the command with --force. NOTE: setting this '
                 'flag will ignore all change advice. For production systems, '
                 'best practice is to set this for a single execution only '
                 'after manually reviewing all changes with advice.')

FORCE_ADVICE_STRING = ('Advice found for changes in the new service config, '
                       'but proceeding anyway because --force is set...')

VALIDATE_NEW_PROMPT = ('The service {service_name} must exist in order to '
                       'validate the configuration. Do you want to create the '
                       'service in project {project_id}?')
VALIDATE_NEW_ERROR = ('The service {service_name} must exist in order to '
                      'validate the configuration. To create the service in '
                      'project {project_id}, rerun the command without the '
                      '--validate-only flag.')

NUM_ADVICE_TO_PRINT = 3


def _CommonArgs(parser):
  """Add common arguments for this command to the given parser."""
  parser.add_argument(
      'service_config_file',
      nargs='+',
      help=('The service configuration file (or files) containing the API '
            'specification to upload. Proto Descriptors, Open API (Swagger) '
            'specifications, and Google Service Configuration files in JSON '
            'and YAML formats are acceptable.'))
  base.ASYNC_FLAG.AddToParser(parser)


def GenerateManagementUrl(service):
  """Generate a service management url for this service."""
  # It is actually possible to deploy a service configuration for a service
  # which is not in the current project, as long as you have appropriate
  # permissions. Because of this, we need to explicitly query for the service's
  # project.
  messages = services_util.GetMessagesModule()
  client = services_util.GetClientInstance()
  get_request = messages.ServicemanagementServicesGetRequest(
      serviceName=service,
  )
  response = client.services.Get(get_request)
  project = response.producerProjectId

  return ('https://console.cloud.google.com/endpoints/api/'
          '{service}/overview?project={project}'.format(
              service=six.moves.urllib.parse.quote(service),
              project=six.moves.urllib.parse.quote(project)))


class _BaseDeploy(object):
  """Create deploy base class for all release tracks."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    _CommonArgs(parser)
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='If included, the command validates the service configuration(s), '
             'but does not deploy them. The service must exist in order to '
             'validate the configuration(s).')

    parser.add_argument(
        '--force',
        '-f',
        action='store_true',
        default=False,
        help='Force the deployment even if any hazardous changes to the '
             'service configuration are detected.')

  def MakeConfigFileMessage(self, file_contents, filename, file_type):
    """Constructs a ConfigFile message from a config file.

    Args:
      file_contents: The contents of the config file.
      filename: The full path to the config file.
      file_type: FileTypeValueValuesEnum describing the type of config file.

    Returns:
      The constructed ConfigFile message.
    """

    messages = services_util.GetMessagesModule()

    file_types = messages.ConfigFile.FileTypeValueValuesEnum
    if file_type != file_types.FILE_DESCRIPTOR_SET_PROTO:
      # File is human-readable text, not binary; needs to be encoded.
      file_contents = http_encoding.Encode(file_contents)
    return messages.ConfigFile(
        fileContents=file_contents,
        filePath=os.path.basename(filename),
        fileType=file_type,)

  def ShowConfigReport(self, service, service_config_id, log_func=log.warning):
    """Run and display results (if any) from the Push Advisor.

    Args:
      service: The name of the service for which to compare configs.
      service_config_id: The new config ID to compare against the active config.
      log_func: The function to which to pass advisory messages
        (default: log.warning).

    Returns:
      The number of advisory messages returned by the Push Advisor.
    """
    num_changes_with_advice = 0

    reporter = config_reporter.ConfigReporter(service)

    # Set the new config as the recently generated service config ID
    reporter.new_config.SetConfigId(service_config_id)

    # We always want to compare agaisnt the active config, so use default here
    reporter.old_config.SetConfigUseDefaultId()

    change_report = reporter.RunReport()
    if not change_report or not change_report.configChanges:
      return 0

    changes = change_report.configChanges

    for change in changes:
      if change.advices:
        if num_changes_with_advice < NUM_ADVICE_TO_PRINT:
          log_func('%s\n',
                   services_util.PushAdvisorConfigChangeToString(change))
        num_changes_with_advice += 1

    if num_changes_with_advice > NUM_ADVICE_TO_PRINT:
      log_func(
          '%s total changes with advice found, check config report file '
          'for full list.\n', num_changes_with_advice)

    return num_changes_with_advice

  def CheckPushAdvisor(self, unused_force=False):
    """Run the Push Advisor and return whether the command should abort.

    Args:
      unused_force: bool, unused in the default implementation.

    Returns:
      True if the deployment should be aborted due to warnings, otherwise
      False if it's safe to continue.
    """
    # Child classes must override this; otherwise, we'll always return False
    return False

  def AttemptToEnableService(self, service_name, is_async):
    """Attempt to enable a service. If lacking permission, log a warning.

    Args:
      service_name: The service to enable.
      is_async: If true, return immediately instead of waiting for the operation
          to finish.
    """
    project_id = properties.VALUES.core.project.Get(required=True)
    try:
      # Enable the produced service.
      enable_api.EnableService(project_id, service_name, is_async)
      # The above command will print a message to the human user, but it needs a
      # newline when the command is successful.
      log.status.Print('\n')
    except services_exceptions.EnableServicePermissionDeniedException:
      log.warning(('Attempted to enable service [{0}] on project [{1}], but '
                   'did not have required permissions. Please ensure this '
                   'service is enabled before using your Endpoints '
                   'service.\n').format(service_name, project_id))

  def Run(self, args):
    """Run 'endpoints services deploy'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the Update API call.

    Raises:
      BadFileExceptionn: if the provided service configuration files are
          invalid or cannot be read.
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()

    file_types = messages.ConfigFile.FileTypeValueValuesEnum
    self.service_name = self.service_version = config_contents = None
    config_files = []

    self.validate_only = args.validate_only

    # TODO(b/77867100): remove .proto support and deprecation warning.
    give_proto_deprecate_warning = False

    # If we're not doing a validate-only run, we don't want to output the
    # resource directly unless the user specifically requests it using the
    # --format flag. The Epilog will show useful information after deployment
    # is complete.
    if not self.validate_only and not args.IsSpecified('format'):
      args.format = 'none'

    for service_config_file in args.service_config_file:
      config_contents = services_util.ReadServiceConfigFile(service_config_file)

      if services_util.FilenameMatchesExtension(
          service_config_file, ['.json', '.yaml', '.yml']):
        # Try to load the file as JSON. If that fails, try YAML.
        service_config_dict = services_util.LoadJsonOrYaml(config_contents)
        if not service_config_dict:
          raise calliope_exceptions.BadFileException(
              'Could not read JSON or YAML from service config file '
              '[{0}].'.format(service_config_file))

        if 'swagger' in service_config_dict:
          if 'host' not in service_config_dict:
            raise calliope_exceptions.BadFileException((
                'Malformed input. Found Swagger service config in file [{}], '
                'but no host was specified. Add a host specification to the '
                'config file.').format(
                    service_config_file))
          if not self.service_name and service_config_dict.get('host'):
            self.service_name = service_config_dict.get('host')

          # Always use YAML for Open API because JSON is a subset of YAML.
          config_files.append(
              self.MakeConfigFileMessage(config_contents, service_config_file,
                                         file_types.OPEN_API_YAML))
        elif service_config_dict.get('type') == 'google.api.Service':
          if not self.service_name and service_config_dict.get('name'):
            self.service_name = service_config_dict.get('name')

          config_files.append(
              self.MakeConfigFileMessage(config_contents, service_config_file,
                                         file_types.SERVICE_CONFIG_YAML))
        elif 'name' in service_config_dict:
          # This is a special case. If we have been provided a Google Service
          # Configuration file which has a service 'name' field, but no 'type'
          # field, we have to assume that this is a normalized service config,
          # and can be uploaded via the CreateServiceConfig API. Therefore,
          # we can short circute the process here.
          if len(args.service_config_file) > 1:
            raise calliope_exceptions.BadFileException((
                'Ambiguous input. Found normalized service configuration in '
                'file [{0}], but received multiple input files. To upload '
                'normalized service config, please provide it separately from '
                'other input files to avoid ambiguity.').format(
                    service_config_file))

          # If this is a validate-only run, abort now, since this is not
          # supported in the ServiceConfigs.Create API
          if self.validate_only:
            raise exceptions.InvalidFlagError(
                'The --validate-only flag is not supported when using '
                'normalized service configs as input.')

          self.service_name = service_config_dict.get('name')
          config_files = []
          break
        else:
          raise calliope_exceptions.BadFileException((
              'Unable to parse Open API, or Google Service Configuration '
              'specification from {0}').format(service_config_file))

      elif services_util.IsProtoDescriptor(service_config_file):
        config_files.append(
            self.MakeConfigFileMessage(config_contents, service_config_file,
                                       file_types.FILE_DESCRIPTOR_SET_PROTO))
      elif services_util.IsRawProto(service_config_file):
        give_proto_deprecate_warning = True
        config_files.append(
            self.MakeConfigFileMessage(config_contents, service_config_file,
                                       file_types.PROTO_FILE))
      else:
        raise calliope_exceptions.BadFileException((
            'Could not determine the content type of file [{0}]. Supported '
            'extensions are .json .yaml .yml .pb and .descriptor').format(
                service_config_file))

    if give_proto_deprecate_warning:
      log.warning(
          'Support for uploading uncompiled .proto files is deprecated and '
          'will soon be removed. Use compiled descriptor sets (.pb) instead.\n')

    # Check if we need to create the service.
    was_service_created = False
    if not services_util.DoesServiceExist(self.service_name):
      project_id = properties.VALUES.core.project.Get(required=True)
      # Deploying, even with validate-only, cannot succeed without the service
      # being created
      if self.validate_only:
        if not console_io.CanPrompt():
          raise exceptions.InvalidConditionError(VALIDATE_NEW_ERROR.format(
              service_name=self.service_name, project_id=project_id))
        if not console_io.PromptContinue(
            VALIDATE_NEW_PROMPT.format(
                service_name=self.service_name, project_id=project_id)):
          return None
      services_util.CreateService(self.service_name, project_id)
      was_service_created = True

    if config_files:
      push_config_result = services_util.PushMultipleServiceConfigFiles(
          self.service_name, config_files, args.async_,
          validate_only=self.validate_only)
      self.service_config_id = (
          services_util.GetServiceConfigIdFromSubmitConfigSourceResponse(
              push_config_result)
      )
    else:
      push_config_result = services_util.PushNormalizedGoogleServiceConfig(
          self.service_name,
          properties.VALUES.core.project.Get(required=True),
          services_util.LoadJsonOrYaml(config_contents))
      self.service_config_id = push_config_result.id

    if not self.service_config_id:
      raise exceptions.InvalidConditionError(
          'Failed to retrieve Service Configuration Id.')

    # Run the Push Advisor to see if we need to warn the user of any
    # potentially hazardous changes to the service configuration.
    if self.CheckPushAdvisor(args.force):
      return None

    # Create a Rollout for the new service configuration
    if not self.validate_only:
      percentages = messages.TrafficPercentStrategy.PercentagesValue()
      percentages.additionalProperties.append(
          (messages.TrafficPercentStrategy.PercentagesValue.AdditionalProperty(
              key=self.service_config_id, value=100.0)))
      traffic_percent_strategy = messages.TrafficPercentStrategy(
          percentages=percentages)
      rollout = messages.Rollout(
          serviceName=self.service_name,
          trafficPercentStrategy=traffic_percent_strategy,)
      rollout_create = messages.ServicemanagementServicesRolloutsCreateRequest(
          rollout=rollout,
          serviceName=self.service_name,
      )
      rollout_operation = client.services_rollouts.Create(rollout_create)
      services_util.ProcessOperationResult(rollout_operation, args.async_)

      if was_service_created:
        self.AttemptToEnableService(self.service_name, args.async_)

    return push_config_result

  def Epilog(self, resources_were_displayed):
    # Print this to screen not to the log because the output is needed by the
    # human user. Only print this when not doing a validate-only run.
    if resources_were_displayed and not self.validate_only:
      log.status.Print(('Service Configuration [{0}] uploaded for '
                        'service [{1}]\n').format(self.service_config_id,
                                                  self.service_name))

      management_url = GenerateManagementUrl(self.service_name)
      log.status.Print('To manage your API, go to: ' + management_url)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Deploy(_BaseDeploy, base.Command):
  # pylint: disable=line-too-long
  """Deploys a service configuration for the given service name.

     This command is used to deploy a service configuration for a service
     to Google Service Management. As input, it takes one or more paths
     to service configurations that should be uploaded. These configuration
     files can be Proto Descriptors, Open API (Swagger) specifications,
     or Google Service Configuration files in JSON or YAML formats.

     If a service name is present in multiple configuration files (given
     in the `host` field in OpenAPI specifications or the `name` field in
     Google Service Configuration files), the first one will take precedence.

     This command will block until deployment is complete unless the
     `--async` flag is passed.

     ## EXAMPLES
     To deploy a single Open API service configuration, run:

       $ {command} ~/my_app/openapi.json

     To run the deployment asynchronously (non-blocking), run:

       $ {command} ~/my_app/openapi.json --async

     To deploy a service config with a Proto, run:

       $ {command} ~/my_app/service-config.yaml ~/my_app/service-protos.pb
  """
  # pylint: enable=line-too-long


# TODO(b/65455903) Once PushAdvisor is ready to be included by default,
# merge this back into _BaseDeploy and rename it to Deploy.
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DeployBetaAlpha(_BaseDeploy, base.Command):
  # pylint: disable=line-too-long
  """Deploys a service configuration for the given service name.

     This command is used to deploy a service configuration for a service
     to Google Service Management. As input, it takes one or more paths
     to service configurations that should be uploaded. These configuration
     files can be Proto Descriptors, Open API (Swagger) specifications,
     or Google Service Configuration files in JSON or YAML formats.

     If a service name is present in multiple configuration files (given
     in the `host` field in OpenAPI specifications or the `name` field in
     Google Service Configuration files), the first one will take precedence.

     When deploying a new service configuration to an already-existing
     service, some safety checks will be made comparing the new configuration
     to the active configuration. If any actionable advice is provided, it
     will be printed out to the log, and the deployment will be halted. It is
     recommended that these warnings be addressed before proceeding, but they
     can be overridden with the --force flag.

     This command will block until deployment is complete unless the
     `--async` flag is passed.

     ## EXAMPLES
     To deploy a single Open API service configuration, run:

       $ {command} ~/my_app/openapi.json

     To run the deployment asynchronously (non-blocking), run:

       $ {command} ~/my_app/openapi.json --async

     To deploy a service config with a Proto, run:

       $ {command} ~/my_app/service-config.yaml ~/my_app/service-protos.pb
  """
  # pylint: enable=line-too-long

  def CheckPushAdvisor(self, force=False):
    """Run the Push Advisor and return whether the command should abort.

    Args:
      force: bool, if True, this method will return False even if warnings are
        generated.

    Returns:
      True if the deployment should be aborted due to warnings, otherwise
      False if it's safe to continue.
    """
    log_func = log.warning if force else log.error
    num_advices = self.ShowConfigReport(
        self.service_name, self.service_config_id, log_func)
    if num_advices > 0:
      if force:
        log_func(('{0}\n').format(FORCE_ADVICE_STRING))
      else:
        log_func(('{0}\n').format(ADVICE_STRING))
        return True

    return False
