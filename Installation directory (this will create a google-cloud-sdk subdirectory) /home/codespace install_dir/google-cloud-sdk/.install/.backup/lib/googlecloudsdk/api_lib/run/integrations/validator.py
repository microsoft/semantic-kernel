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
"""Used to validate integrations are setup correctly for deployment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Dict, List

from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.command_lib.runapps import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_API_ENABLEMENT_CONFIRMATION_TEXT = {
    'firebasehosting.googleapis.com': (
        'By enabling the Firebase Hosting API you are agreeing to the Firebase'
        ' Terms of Service. Learn more at https://firebase.google.com/terms'
    )
}


def GetIntegrationValidator(integration_type: str):
  """Gets the integration validator based on the integration type."""
  type_metadata = types_utils.GetTypeMetadata(integration_type)

  if type_metadata is None:
    raise ValueError(
        'Integration type: [{}] has not been defined in types_utils'
        .format(integration_type))

  return Validator(type_metadata)


def _ConstructPrompt(apis_not_enabled: List[str]) -> str:
  """Returns a prompt to enable APIs with any custom text per-API.

  Args:
    apis_not_enabled: APIs that are to be enabled.
  Returns: prompt string to be displayed for confirmation.
  """
  if not apis_not_enabled:
    return ''
  base_prompt = (
      'Do you want to enable these APIs to continue (this will take a few'
      ' minutes)?'
  )

  prompt = ''
  for api in apis_not_enabled:
    if api in _API_ENABLEMENT_CONFIRMATION_TEXT:
      prompt += _API_ENABLEMENT_CONFIRMATION_TEXT[api] + '\n'

  prompt += base_prompt
  return prompt


def EnableApis(apis_not_enabled: List[str], project_id: str):
  """Enables the given API on the given project.

  Args:
    apis_not_enabled: the apis that needs enablement
    project_id: the project ID
  """
  apis_to_enable = '\n\t'.join(apis_not_enabled)
  console_io.PromptContinue(
      default=False,
      cancel_on_no=True,
      message=(
          'The following APIs are not enabled on project [{0}]:\n\t{1}'
          .format(project_id, apis_to_enable)
      ),
      prompt_string=_ConstructPrompt(apis_not_enabled),
  )

  log.status.Print(
      'Enabling APIs on project [{0}]...'.format(project_id))
  op = serviceusage.BatchEnableApiCall(project_id, apis_not_enabled)
  if not op.done:
    op = services_util.WaitOperation(op.name, serviceusage.GetOperation)
    services_util.PrintOperation(op)


def CheckApiEnablements(types: List[str]):
  """Checks if all GCP APIs required by the given types are enabled.

  If some required APIs are not enabled, it will prompt the user to enable them.
  If they do not want to enable them, the process will exit.

  Args:
    types: list of types to check.
  """
  project_id = properties.VALUES.core.project.Get()
  apis_not_enabled = []
  for typekit in types:
    try:
      validator = GetIntegrationValidator(typekit)
      apis = validator.GetDisabledGcpApis(project_id)
      if apis:
        apis_not_enabled.extend(apis)
    except ValueError:
      continue
  if apis_not_enabled:
    EnableApis(apis_not_enabled, project_id)


class Validator:
  """Validates an integration is setup correctly for deployment."""

  def __init__(self, type_metadata: types_utils.TypeMetadata):
    self.type_metadata = type_metadata

  def ValidateEnabledGcpApis(self):
    """Validates user has all GCP APIs enabled for an integration.

    If the user does not have all the GCP APIs enabled they will
    be prompted to enable them.  If they do not want to enable them,
    then the process will exit.
    """
    project_id = properties.VALUES.core.project.Get()
    apis_not_enabled = self.GetDisabledGcpApis(project_id)

    if apis_not_enabled:
      EnableApis(apis_not_enabled, project_id)

  def GetDisabledGcpApis(self, project_id: str) -> List[str]:
    """Returns all GCP APIs needed for an integration.

    Args:
      project_id: The project's ID

    Returns:
      A list where each item is a GCP API that is not enabled.
    """
    required_apis = set(self.type_metadata.required_apis).union(
        types_utils.BASELINE_APIS
    )
    project_id = properties.VALUES.core.project.Get()
    apis_not_enabled = [
        # iterable is sorted for scenario tests.  The order of API calls
        # should happen in the same order each time for the scenario tests.
        api
        for api in sorted(required_apis)
        if not enable_api.IsServiceEnabled(project_id, api)
    ]
    return apis_not_enabled

  def ValidateCreateParameters(self, parameters: Dict[str, str], service: str):
    """Validates parameters provided for creating an integration.

    Three things are done for all integrations created:
      1. Check that parameters passed in are valid (exist in types_utils
        mapping) and are not misspelled. These are parameters that will
        be recognized by the control plane.
      2. Check that all required parameters are provided.
      3. Check that default values are set for parameters
        that are not provided.

    Note that user provided params may be modified in place
    if default values are missing.

    Args:
      parameters: A dict where the key, value mapping is provided by the user.
      service: The service to bind to the new integration.
    """
    self._ValidateProvidedParams(parameters)
    self._CheckServiceFlag(service, required=True)
    self._CheckForInvalidCreateParameters(parameters)
    self._ValidateRequiredParams(parameters)
    self._SetupDefaultParams(parameters)

  def ValidateUpdateParameters(self, parameters):
    """Checks that certain parameters have not been updated.

    This firstly checks that the parameters provided exist in the mapping
    and thus are recognized the control plane.

    Args:
      parameters: A dict where the key, value mapping is provided by the user.
    """
    self._ValidateProvidedParams(parameters)
    self._CheckForInvalidUpdateParameters(parameters)

  def _CheckForInvalidCreateParameters(self, user_provided_params):
    """Raises an exception that lists the parameters that can't be changed."""
    invalid_params = []
    for param in self.type_metadata.parameters:
      if not param.create_allowed and param.name in user_provided_params:
        invalid_params.append(param.name)

    if invalid_params:
      raise exceptions.ArgumentError(
          ('The following parameters are not allowed in create command: {}')
          .format(self._RemoveEncoding(invalid_params))
      )

  def _CheckForInvalidUpdateParameters(self, user_provided_params):
    """Raises an exception that lists the parameters that can't be changed."""
    invalid_params = []
    for param in self.type_metadata.parameters:
      if not param.update_allowed and param.name in user_provided_params:
        invalid_params.append(param.name)

    if invalid_params:
      raise exceptions.ArgumentError(
          ('The following parameters: {} cannot be changed once the ' +
           'integration has been created')
          .format(self._RemoveEncoding(invalid_params))
      )

    for exclusive_groups in self.type_metadata.update_exclusive_groups:
      found = 0
      group_params = set(exclusive_groups.params)
      # Generate a stable order list of the param for output.
      params_list_str = ', '.join(sorted(group_params))
      for param_name in group_params:
        if param_name in user_provided_params:
          found += 1
      if found > 1:
        raise exceptions.ArgumentError(
            ('At most one of these parameters can be specified: {}'
            ).format(params_list_str))
      if exclusive_groups.required and found == 0:
        raise exceptions.ArgumentError(
            ('At least one of these parameters must be specified: {}')
            .format(params_list_str)
        )

  def _CheckServiceFlag(self, service, required=False):
    """Raises an exception that lists the parameters that can't be changed."""
    disable_service_flags = self.type_metadata.disable_service_flags
    if disable_service_flags and service:
      raise exceptions.ArgumentError(
          ('--service not allowed for integration type [{}]'.format(
              self.type_metadata.integration_type)))
    if not disable_service_flags and not service and required:
      raise exceptions.ArgumentError(('--service is required'))

  def _ValidateProvidedParams(self, user_provided_params):
    """Checks that the user provided parameters exist in the mapping."""
    invalid_params = []
    allowed_params = [
        param.name for param in self.type_metadata.parameters
    ]
    for param in user_provided_params:
      if param not in allowed_params:
        invalid_params.append(param)

    if invalid_params:
      raise exceptions.ArgumentError(
          'The following parameters: {} are not allowed'.format(
              self._RemoveEncoding(invalid_params))
      )

  def _ValidateRequiredParams(self, user_provided_params):
    """Checks that required parameters are provided by the user."""
    missing_required_params = []
    for param in self.type_metadata.parameters:
      if param.required and param.name not in user_provided_params:
        missing_required_params.append(param.name)

    if missing_required_params:
      raise exceptions.ArgumentError(
          ('The following parameters: {} are required to create an ' +
           'integration of type [{}]').format(
               self._RemoveEncoding(missing_required_params),
               self.type_metadata.integration_type))

  def _RemoveEncoding(self, elements):
    """Removes encoding for each element in the list.

    This causes inconsistencies in the scenario test when the output
    looks like [u'domain'] instead of ['domain']

    Args:
      elements: list

    Returns:
      list[str], encoding removed from each element.
    """
    return [str(x) for x in elements]

  def _SetupDefaultParams(self, user_provided_params):
    """Ensures that default parameters have a value if not set."""
    for param in self.type_metadata.parameters:
      if param.default and param.name not in user_provided_params:
        user_provided_params[param.name] = param.default
