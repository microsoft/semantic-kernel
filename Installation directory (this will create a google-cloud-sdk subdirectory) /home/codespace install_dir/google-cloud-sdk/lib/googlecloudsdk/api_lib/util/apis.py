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

"""Library for obtaining API clients and messages."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.util import api_enablement
from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.api_lib.util import apis_util
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import gapic_util
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis import apis_map

import six


class Error(exceptions.Error):
  """A base class for apis helper errors."""
  pass


class GapicRestUnsupportedError(Error):
  """An error for the unsupported REST transport on GAPIC Clients."""

  def __init__(self):
    super(
        GapicRestUnsupportedError,
        self).__init__('REST transport is not yet supported for GAPIC Clients')


def AddUnreleasedAPIs(unreleased_apis_map):
  # Add in unreleased APIs so that they can be looked up via main api map.
  for api_name, api_versions in six.iteritems(unreleased_apis_map.MAP):
    for api_version, api_def in six.iteritems(api_versions):
      _AddToApisMap(api_name, api_version, api_def)


def _AddToApisMap(api_name, api_version, api_def):
  """Adds the APIDef specified by the given arguments to the APIs map.

  This method should only be used for runtime patching of the APIs map.
  Additions to the map should ensure that there is only one and only one default
  version for each API.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The version of the API.
    api_def: APIDef for the API version.
  """
  # pylint:disable=protected-access
  api_name, _ = apis_internal._GetApiNameAndAlias(api_name)

  # Register API version as default if this API did not exist,
  # otherwise we'll set the first APIs map
  api_versions = apis_map.MAP.get(api_name, {})
  api_def.default_version = not api_versions

  api_versions[api_version] = api_def
  apis_map.MAP[api_name] = api_versions


def SetDefaultVersion(api_name, api_version):
  """Resets default version for given api."""
  # pylint:disable=protected-access
  api_def = apis_internal.GetApiDef(api_name, api_version)
  # pylint:disable=protected-access
  default_version = apis_internal._GetDefaultVersion(api_name)
  # pylint:disable=protected-access
  default_api_def = apis_internal.GetApiDef(api_name, default_version)
  default_api_def.default_version = False
  api_def.default_version = True


def GetVersions(api_name):
  """Return available versions for given api.

  Args:
    api_name: str, The API name (or the command surface name, if different).

  Raises:
    UnknownAPIError: If api_name does not exist in the APIs map.

  Returns:
    list, of version names.
  """
  # pylint:disable=protected-access
  return apis_internal._GetVersions(api_name)


def ResolveVersion(api_name, api_version=None):
  """Resolves the version for an API based on the APIs map and API overrides.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The API version.

  Raises:
    apis_internal.UnknownAPIError: If api_name does not exist in the APIs map.

  Returns:
    str, The resolved version.
  """
  # pylint:disable=protected-access
  api_name, api_name_alias = apis_internal._GetApiNameAndAlias(api_name)
  if api_name not in apis_map.MAP:
    raise apis_util.UnknownAPIError(api_name)

  version_overrides = properties.VALUES.api_client_overrides.AllValues()

  # First try to get api specific override, then try full surface override.
  api_version_override = None
  if api_version:
    api_version_override = version_overrides.get(
        '{}/{}'.format(api_name_alias, api_version), None)
  if not api_version_override:
    api_version_override = version_overrides.get(api_name_alias, api_version)

  return (api_version_override or
          # pylint:disable=protected-access
          apis_internal._GetDefaultVersion(api_name))


API_ENABLEMENT_ERROR_EXPECTED_STATUS_CODE = 403  # retry status code
RESOURCE_EXHAUSTED_STATUS_CODE = 429


def GetApiEnablementInfo(exception):
  """Returns the API Enablement info or None if prompting is not necessary.

  Args:
    exception (apitools_exceptions.HttpError): Exception if an error occurred.

  Returns:
    tuple[str]: The project, service token, exception tuple to be used for
      prompting to enable the API.

  Raises:
    api_exceptions.HttpException: If gcloud should not prompt to enable the API.
  """
  parsed_error = api_exceptions.HttpException(exception)
  if (parsed_error.payload.status_code !=
      API_ENABLEMENT_ERROR_EXPECTED_STATUS_CODE):
    return None

  enablement_info = api_enablement.GetApiEnablementInfo(
      parsed_error.payload.status_message)
  if enablement_info:
    return enablement_info + (parsed_error,)
  return None


def PromptToEnableApi(project, service_token, exception,
                      is_batch_request=False):
  """Prompts to enable the API and throws if the answer is no.

  Args:
    project (str): The project that the API is not enabled on.
    service_token (str): The service token of the API to prompt for.
    exception (api_Exceptions.HttpException): Exception to throw if the prompt
      is denied.
    is_batch_request: If the request is a batch request. This determines how to
      get apitools to retry the request.

  Raises:
    api_exceptions.HttpException: API not enabled error if the user chooses to
      not enable the API.
  """
  api_enable_attempted = api_enablement.PromptToEnableApi(
      project, service_token)
  if api_enable_attempted:
    if not is_batch_request:
      raise apitools_exceptions.RequestError('Retry')
  else:
    raise exception


def CheckResponse(skip_activation_prompt=False):
  """Returns a callback for checking API errors."""
  state = {'already_prompted_to_enable': False}

  def _CheckForApiEnablementError(response_as_error):
    # If it was an API enablement error,
    # prompt the user to enable the API. If yes, we make that call and then
    # raise a RequestError, which will prompt the caller to retry. If not, we
    # raise the actual HTTP error.
    enablement_info = GetApiEnablementInfo(response_as_error)
    if enablement_info:
      if state['already_prompted_to_enable'] or skip_activation_prompt:
        raise apitools_exceptions.RequestError('Retry')
      state['already_prompted_to_enable'] = True
      PromptToEnableApi(*enablement_info)

  def _CheckResponse(response):
    """Checks API error.

    If it's an enablement error, prompt to enable & retry.
    If it's a resource exhausted error, no retry & return.

    Args:
      response: response that had an error.

    Raises:
      apitools_exceptions.RequestError: error which should signal apitools to
        retry.
      api_exceptions.HttpException: the parsed error.
    """
    # This will throw if there was a specific type of error. If not, then we can
    # parse and deal with our own class of errors.
    if response is None:
      # Caller shouldn't call us if the response is None, but handle anyway.
      raise apitools_exceptions.RequestError(
          'Request to url %s did not return a response.' %
          response.request_url)
    # If it was a resource exhausted error, return
    elif response.status_code == RESOURCE_EXHAUSTED_STATUS_CODE:
      return
    elif response.status_code >= 500:
      raise apitools_exceptions.BadStatusCodeError.FromResponse(response)
    elif response.retry_after:
      raise apitools_exceptions.RetryAfterError.FromResponse(response)

    response_as_error = apitools_exceptions.HttpError.FromResponse(response)

    if properties.VALUES.core.should_prompt_to_enable_api.GetBool():
      _CheckForApiEnablementError(response_as_error)

  return _CheckResponse


def GetClientClass(api_name, api_version):
  """Returns the client class for the API specified in the args.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The version of the API.

  Returns:
    base_api.BaseApiClient, Client class for the specified API.
  """
  # pylint:disable=protected-access
  return apis_internal._GetClientClass(api_name, api_version)


def GetClientInstance(
    api_name,
    api_version,
    no_http=False,
    http_timeout_sec=None,
    skip_activation_prompt=False,
):
  """Returns an instance of the API client specified in the args.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The version of the API.
    no_http: bool, True to not create an http object for this client.
    http_timeout_sec: int, seconds for http timeout, default if None.
    skip_activation_prompt: bool, if true, do not prompt for service activation.

  Returns:
    base_api.BaseApiClient, An instance of the specified API client.
  """
  # pylint:disable=protected-access
  return apis_internal._GetClientInstance(
      api_name,
      api_version,
      no_http,
      None,
      CheckResponse(skip_activation_prompt),
      http_timeout_sec=http_timeout_sec,
  )


def GetGapicClientClass(api_name,
                        api_version,
                        transport=apis_util.GapicTransport.GRPC):
  """Returns the GAPIC client class for the API specified in the args.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The version of the API.
    transport: apis_util.GapicTransport, The transport class to obtain.

  Raises:
    GapicRestUnsupportedError: If transport is REST.

  Returns:
    The specified GAPIC API Client class.
  """
  if transport == apis_util.GapicTransport.REST:
    raise GapicRestUnsupportedError()
  # pylint:disable=protected-access
  return apis_internal._GetGapicClientClass(
      api_name, api_version, transport_choice=transport)


def GetGapicClientInstance(api_name,
                           api_version,
                           address_override_func=None,
                           transport=apis_util.GapicTransport.GRPC):
  """Returns an instance of the GAPIC API client specified in the args.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The version of the API.
    address_override_func: function, function to call to override the client
      host. It takes a single argument which is the original host.
    transport: apis_util.GapicTransport, The transport to be used by the client.

  Raises:
    GapicRestUnsupportedError: If transport is REST.

  Returns:
    An instance of the specified GAPIC API client.
  """
  if transport == apis_util.GapicTransport.REST:
    raise GapicRestUnsupportedError()
  credentials = gapic_util.GetGapicCredentials()
  # pylint:disable=protected-access
  return apis_internal._GetGapicClientInstance(
      api_name,
      api_version,
      credentials,
      address_override_func=address_override_func,
      transport_choice=transport)


def GetEffectiveApiEndpoint(api_name, api_version, client_class=None):
  """Returns effective endpoint for given api."""
  # pylint:disable=protected-access
  return apis_internal._GetEffectiveApiEndpoint(api_name,
                                                api_version,
                                                client_class)


def GetMessagesModule(api_name, api_version):
  """Returns the messages module for the API specified in the args.

  Args:
    api_name: str, The API name (or the command surface name, if different).
    api_version: str, The version of the API.

  Returns:
    Module containing the definitions of messages for the specified API.
  """
  # pylint:disable=protected-access
  api_def = apis_internal.GetApiDef(api_name, api_version)
  # fromlist below must not be empty, see:
  # http://stackoverflow.com/questions/2724260/why-does-pythons-import-require-fromlist.
  return __import__(api_def.apitools.messages_full_modulepath,
                    fromlist=['something'])


def UniversifyAddress(address):
  return apis_internal.UniversifyAddress(address)
