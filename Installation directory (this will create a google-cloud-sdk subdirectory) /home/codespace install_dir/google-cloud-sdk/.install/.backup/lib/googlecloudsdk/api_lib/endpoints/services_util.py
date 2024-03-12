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

"""Common helper methods for Service Management commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager

from googlecloudsdk.api_lib.endpoints import exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import retry
import six


EMAIL_REGEX = re.compile(r'^.+@([^.@][^@]+)$')
FINGERPRINT_REGEX = re.compile(
    r'^([a-f0-9][a-f0-9]:){19}[a-f0-9][a-f0-9]$', re.IGNORECASE)
OP_BASE_CMD = 'gcloud endpoints operations '
OP_DESCRIBE_CMD = OP_BASE_CMD + 'describe {0}'
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'
SERVICES_COLLECTION = 'servicemanagement.services'
CONFIG_COLLECTION = 'servicemanagement.services.configs'

ALL_IAM_PERMISSIONS = [
    'servicemanagement.services.get',
    'servicemanagement.services.getProjectSettings',
    'servicemanagement.services.delete',
    'servicemanagement.services.update',
    'servicemanagement.services.bind',
    'servicemanagement.services.updateProjectSettings',
    'servicemanagement.services.check',
    'servicemanagement.services.report',
    'servicemanagement.services.setIamPolicy',
    'servicemanagement.services.getIamPolicy',
]


def GetMessagesModule():
  return apis.GetMessagesModule('servicemanagement', 'v1')


def GetClientInstance():
  return apis.GetClientInstance('servicemanagement', 'v1')


def GetServiceManagementServiceName():
  return 'servicemanagement.googleapis.com'


def GetValidatedProject(project_id):
  """Validate the project ID, if supplied, otherwise return the default project.

  Args:
    project_id: The ID of the project to validate. If None, gcloud's default
                project's ID will be returned.

  Returns:
    The validated project ID.
  """
  if project_id:
    properties.VALUES.core.project.Validate(project_id)
  else:
    project_id = properties.VALUES.core.project.Get(required=True)
  return project_id


def GetProjectSettings(service, consumer_project_id, view):
  """Returns the project settings for a given service, project, and view.

  Args:
    service: The service for which to return project settings.
    consumer_project_id: The consumer project id for which to return settings.
    view: The view (CONSUMER_VIEW or PRODUCER_VIEW).

  Returns:
    A ProjectSettings message with the settings populated.
  """
  # Shorten the request names for better readability
  get_request = (GetMessagesModule()
                 .ServicemanagementServicesProjectSettingsGetRequest)

  # Get the current list of quota settings to see if the quota override
  # exists in the first place.
  request = get_request(
      serviceName=service,
      consumerProjectId=consumer_project_id,
      view=view,
  )

  return GetClientInstance().services_projectSettings.Get(request)


def GetProducedListRequest(project_id):
  return GetMessagesModule().ServicemanagementServicesListRequest(
      producerProjectId=project_id
  )


def PrettyPrint(resource, print_format='json'):
  """Prints the given resource.

  Args:
    resource: The resource to print out.
    print_format: The print_format value to pass along to the resource_printer.
  """
  resource_printer.Print(
      resources=[resource],
      print_format=print_format,
      out=log.out)


def PushAdvisorChangeTypeToString(change_type):
  """Convert a ConfigChange.ChangeType enum to a string.

  Args:
    change_type: The ConfigChange.ChangeType enum to convert.

  Returns:
    An easily readable string representing the ConfigChange.ChangeType enum.
  """
  messages = GetMessagesModule()
  enums = messages.ConfigChange.ChangeTypeValueValuesEnum
  if change_type in [enums.ADDED, enums.REMOVED, enums.MODIFIED]:
    return six.text_type(change_type).lower()
  else:
    return '[unknown]'


def PushAdvisorConfigChangeToString(config_change):
  """Convert a ConfigChange message to a printable string.

  Args:
    config_change: The ConfigChange message to convert.

  Returns:
    An easily readable string representing the ConfigChange message.
  """
  result = ('Element [{element}] (old value = {old_value}, '
            'new value = {new_value}) was {change_type}. Advice:\n').format(
                element=config_change.element,
                old_value=config_change.oldValue,
                new_value=config_change.newValue,
                change_type=PushAdvisorChangeTypeToString(
                    config_change.changeType))

  for advice in config_change.advices:
    result += '\t* {0}'.format(advice.description)

  return result


def GetActiveRolloutForService(service):
  """Return the latest Rollout for a service.

  This function returns the most recent Rollout that has a status of SUCCESS
  or IN_PROGRESS.

  Args:
    service: The name of the service for which to retrieve the active Rollout.

  Returns:
    The Rollout message corresponding to the active Rollout for the service.
  """
  client = GetClientInstance()
  messages = GetMessagesModule()
  statuses = messages.Rollout.StatusValueValuesEnum
  allowed_statuses = [statuses.SUCCESS, statuses.IN_PROGRESS]

  req = messages.ServicemanagementServicesRolloutsListRequest(
      serviceName=service)

  result = list(
      list_pager.YieldFromList(
          client.services_rollouts,
          req,
          predicate=lambda r: r.status in allowed_statuses,
          limit=1,
          batch_size_attribute='pageSize',
          field='rollouts',
      )
  )

  return result[0] if result else None


def GetActiveServiceConfigIdsFromRollout(rollout):
  """Get the active service config IDs from a Rollout message.

  Args:
    rollout: The rollout message to inspect.

  Returns:
    A list of active service config IDs as indicated in the rollout message.
  """
  if rollout and rollout.trafficPercentStrategy:
    return [p.key for p in rollout.trafficPercentStrategy.percentages
            .additionalProperties]
  else:
    return []


def GetActiveServiceConfigIdsForService(service):
  active_rollout = GetActiveRolloutForService(service)
  return GetActiveServiceConfigIdsFromRollout(active_rollout)


def FilenameMatchesExtension(filename, extensions):
  """Checks to see if a file name matches one of the given extensions.

  Args:
    filename: The full path to the file to check
    extensions: A list of candidate extensions.

  Returns:
    True if the filename matches one of the extensions, otherwise False.
  """
  f = filename.lower()
  for ext in extensions:
    if f.endswith(ext.lower()):
      return True
  return False


def IsProtoDescriptor(filename):
  return FilenameMatchesExtension(
      filename, ['.pb', '.descriptor', '.proto.bin'])


def IsRawProto(filename):
  return FilenameMatchesExtension(filename, ['.proto'])


def ReadServiceConfigFile(file_path):
  try:
    if IsProtoDescriptor(file_path):
      return files.ReadBinaryFileContents(file_path)
    return files.ReadFileContents(file_path)
  except files.Error as ex:
    raise calliope_exceptions.BadFileException(
        'Could not open service config file [{0}]: {1}'.format(file_path, ex))


def PushNormalizedGoogleServiceConfig(service_name, project, config_dict,
                                      config_id=None):
  """Pushes a given normalized Google service configuration.

  Args:
    service_name: name of the service
    project: the producer project Id
    config_dict: the parsed contents of the Google Service Config file.
    config_id: The id name for the config

  Returns:
    Result of the ServicesConfigsCreate request (a Service object)
  """
  messages = GetMessagesModule()
  client = GetClientInstance()

  # Be aware: DictToMessage takes the value first and message second;
  # JsonToMessage takes the message first and value second
  service_config = encoding.DictToMessage(config_dict, messages.Service)
  service_config.producerProjectId = project
  service_config.id = config_id
  create_request = (
      messages.ServicemanagementServicesConfigsCreateRequest(
          serviceName=service_name,
          service=service_config,
      ))
  return client.services_configs.Create(create_request)


def GetServiceConfigIdFromSubmitConfigSourceResponse(response):
  return response.get('serviceConfig', {}).get('id')


def PushMultipleServiceConfigFiles(service_name, config_files, is_async,
                                   validate_only=False, config_id=None):
  """Pushes a given set of service configuration files.

  Args:
    service_name: name of the service.
    config_files: a list of ConfigFile message objects.
    is_async: whether to wait for aync operations or not.
    validate_only: whether to perform a validate-only run of the operation
                     or not.
    config_id: an optional name for the config

  Returns:
    Full response from the SubmitConfigSource request.

  Raises:
    ServiceDeployErrorException: the SubmitConfigSource API call returned a
      diagnostic with a level of ERROR.
  """
  messages = GetMessagesModule()
  client = GetClientInstance()

  config_source = messages.ConfigSource(id=config_id)
  config_source.files.extend(config_files)

  config_source_request = messages.SubmitConfigSourceRequest(
      configSource=config_source,
      validateOnly=validate_only,
  )
  submit_request = (
      messages.ServicemanagementServicesConfigsSubmitRequest(
          serviceName=service_name,
          submitConfigSourceRequest=config_source_request,
      ))
  api_response = client.services_configs.Submit(submit_request)
  operation = ProcessOperationResult(api_response, is_async)

  response = operation.get('response', {})
  diagnostics = response.get('diagnostics', [])

  num_errors = 0
  for diagnostic in diagnostics:
    kind = diagnostic.get('kind', '').upper()
    logger = log.error if kind == 'ERROR' else log.warning
    msg = '{l}: {m}\n'.format(
        l=diagnostic.get('location'), m=diagnostic.get('message'))
    logger(msg)

    if kind == 'ERROR':
      num_errors += 1

  if num_errors > 0:
    exception_msg = ('{0} diagnostic error{1} found in service configuration '
                     'deployment. See log for details.').format(
                         num_errors, 's' if num_errors > 1 else '')
    raise exceptions.ServiceDeployErrorException(exception_msg)

  return response


def PushOpenApiServiceConfig(
    service_name, spec_file_contents, spec_file_path, is_async,
    validate_only=False):
  """Pushes a given Open API service configuration.

  Args:
    service_name: name of the service
    spec_file_contents: the contents of the Open API spec file.
    spec_file_path: the path of the Open API spec file.
    is_async: whether to wait for aync operations or not.
    validate_only: whether to perform a validate-only run of the operation
                   or not.

  Returns:
    Full response from the SubmitConfigSource request.
  """
  messages = GetMessagesModule()

  config_file = messages.ConfigFile(
      fileContents=spec_file_contents,
      filePath=spec_file_path,
      # Always use YAML because JSON is a subset of YAML.
      fileType=(messages.ConfigFile.
                FileTypeValueValuesEnum.OPEN_API_YAML),
  )
  return PushMultipleServiceConfigFiles(service_name, [config_file], is_async,
                                        validate_only=validate_only)


def DoesServiceExist(service_name):
  """Check if a service resource exists.

  Args:
    service_name: name of the service to check if exists.

  Returns:
    Whether or not the service exists.
  """
  messages = GetMessagesModule()
  client = GetClientInstance()
  get_request = messages.ServicemanagementServicesGetRequest(
      serviceName=service_name,
  )
  try:
    client.services.Get(get_request)
  except (apitools_exceptions.HttpForbiddenError,
          apitools_exceptions.HttpNotFoundError):
    # Older versions of service management backend return a 404 when service is
    # new, but more recent versions return a 403. Check for either one for now.
    return False
  else:
    return True


def CreateService(service_name, project, is_async=False):
  """Creates a Service resource.

  Args:
    service_name: name of the service to be created.
    project: the project Id
    is_async: If False, the method will block until the operation completes.
  """
  messages = GetMessagesModule()
  client = GetClientInstance()
  # create service
  create_request = messages.ManagedService(
      serviceName=service_name,
      producerProjectId=project,
  )
  result = client.services.Create(create_request)

  GetProcessedOperationResult(result, is_async=is_async)


def ValidateFingerprint(fingerprint):
  return re.match(FINGERPRINT_REGEX, fingerprint) is not None


def ValidateEmailString(email):
  """Returns true if the input is a valid email string.

  This method uses a somewhat rudimentary regular expression to determine
  input validity, but it should suffice for basic sanity checking.

  It also verifies that the email string is no longer than 254 characters,
  since that is the specified maximum length.

  Args:
    email: The email string to validate

  Returns:
    A bool -- True if the input is valid, False otherwise
  """
  return EMAIL_REGEX.match(email or '') is not None and len(email) <= 254


def ProcessOperationResult(result, is_async=False):
  """Validate and process Operation outcome for user display.

  Args:
    result: The message to process (expected to be of type Operation)'
    is_async: If False, the method will block until the operation completes.

  Returns:
    The processed Operation message in Python dict form
  """
  op = GetProcessedOperationResult(result, is_async)
  if is_async:
    cmd = OP_WAIT_CMD.format(op.get('name'))
    log.status.Print('Asynchronous operation is in progress... '
                     'Use the following command to wait for its '
                     'completion:\n {0}\n'.format(cmd))
  else:
    cmd = OP_DESCRIBE_CMD.format(op.get('name'))
    log.status.Print('Operation finished successfully. '
                     'The following command can describe '
                     'the Operation details:\n {0}\n'.format(cmd))
  return op


def GetProcessedOperationResult(result, is_async=False):
  """Validate and process Operation result message for user display.

  This method checks to make sure the result is of type Operation and
  converts the StartTime field from a UTC timestamp to a local datetime
  string.

  Args:
    result: The message to process (expected to be of type Operation)'
    is_async: If False, the method will block until the operation completes.

  Returns:
    The processed message in Python dict form
  """
  if not result:
    return

  messages = GetMessagesModule()

  RaiseIfResultNotTypeOf(result, messages.Operation)

  result_dict = encoding.MessageToDict(result)

  if not is_async:
    op_name = result_dict['name']
    op_ref = resources.REGISTRY.Parse(
        op_name,
        collection='servicemanagement.operations')
    log.status.Print(
        'Waiting for async operation {0} to complete...'.format(op_name))
    result_dict = encoding.MessageToDict(WaitForOperation(
        op_ref, GetClientInstance()))

  return result_dict


def RaiseIfResultNotTypeOf(test_object, expected_type, nonetype_ok=False):
  if nonetype_ok and test_object is None:
    return
  if not isinstance(test_object, expected_type):
    raise TypeError('result must be of type %s' % expected_type)


def WaitForOperation(operation_ref, client):
  """Waits for an operation to complete.

  Args:
    operation_ref: A reference to the operation on which to wait.
    client: The client object that contains the GetOperation request object.

  Raises:
    TimeoutError: if the operation does not complete in time.
    OperationErrorException: if the operation fails.

  Returns:
    The Operation object, if successful. Raises an exception on failure.
  """
  WaitForOperation.operation_response = None
  messages = GetMessagesModule()
  operation_id = operation_ref.operationsId

  def _CheckOperation(operation_id):  # pylint: disable=missing-docstring
    request = messages.ServicemanagementOperationsGetRequest(
        operationsId=operation_id,
    )

    result = client.operations.Get(request)

    if result.done:
      WaitForOperation.operation_response = result
      return True
    else:
      return False

  # Wait for no more than 30 minutes while retrying the Operation retrieval
  try:
    retry.Retryer(exponential_sleep_multiplier=1.1, wait_ceiling_ms=10000,
                  max_wait_ms=30*60*1000).RetryOnResult(
                      _CheckOperation, [operation_id], should_retry_if=False,
                      sleep_ms=1500)
  except retry.MaxRetrialsException:
    raise exceptions.TimeoutError('Timed out while waiting for '
                                  'operation {0}. Note that the operation '
                                  'is still pending.'.format(operation_id))

  # Check to see if the operation resulted in an error
  if WaitForOperation.operation_response.error is not None:
    raise exceptions.OperationErrorException(
        'The operation with ID {0} resulted in a failure.'.format(operation_id))

  # If we've gotten this far, the operation completed successfully,
  # so return the Operation object
  return WaitForOperation.operation_response


def LoadJsonOrYaml(input_string):
  """Tries to load input string as JSON first, then YAML if that fails.

  Args:
    input_string: The string to convert to a dictionary

  Returns:
    A dictionary of the resulting decoding, or None if neither format could be
    detected.
  """
  def TryJson():
    try:
      return json.loads(input_string)
    except ValueError:
      log.info('No JSON detected in service config. Trying YAML...')

  def TryYaml():
    try:
      return yaml.load(input_string)
    except yaml.YAMLParseError as e:
      if hasattr(e.inner_error, 'problem_mark'):
        mark = e.inner_error.problem_mark
        log.error('Service config YAML had an error at position (%s:%s)'
                  % (mark.line+1, mark.column+1))

  # First, try to decode JSON. If that fails, try to decode YAML.
  return TryJson() or TryYaml()


def CreateRollout(service_config_id, service_name, is_async=False):
  """Creates a Rollout for a Service Config within it's service.

  Args:
    service_config_id: The service config id
    service_name: The name of the service
    is_async: (Optional) Wheter or not operation should be asynchronous

  Returns:
    The rollout object or long running operation if is_async is true
  """
  messages = GetMessagesModule()
  client = GetClientInstance()

  percentages = messages.TrafficPercentStrategy.PercentagesValue()
  percentages.additionalProperties.append(
      (messages.TrafficPercentStrategy.PercentagesValue.AdditionalProperty(
          key=service_config_id, value=100.0)))
  traffic_percent_strategy = messages.TrafficPercentStrategy(
      percentages=percentages)
  rollout = messages.Rollout(
      serviceName=service_name,
      trafficPercentStrategy=traffic_percent_strategy,)
  rollout_create = messages.ServicemanagementServicesRolloutsCreateRequest(
      rollout=rollout,
      serviceName=service_name,
  )
  rollout_operation = client.services_rollouts.Create(rollout_create)
  op = ProcessOperationResult(rollout_operation, is_async)

  return op.get('response', None)
