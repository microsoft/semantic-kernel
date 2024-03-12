# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Support library for the auth command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import textwrap

from google.auth import jwt
from googlecloudsdk.api_lib.auth import exceptions as auth_exceptions
from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.iamcredentials import util as impersonation_util
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from oauth2client import client
from oauth2client import service_account
from oauth2client.contrib import gce as oauth2client_gce


SERVICEUSAGE_PERMISSION = 'serviceusage.services.use'


class MissingPermissionOnQuotaProjectError(c_creds.ADCError):
  """An error when ADC does not have permission to bill a quota project."""


class AddQuotaProjectError(c_creds.ADCError):
  """An error when quota project ID is added to creds that don't support it."""


def IsGceAccountCredentials(cred):
  """Checks if the credential is a Compute Engine service account credential."""
  # Import only when necessary to decrease the startup time. Move it to
  # global once google-auth is ready to replace oauth2client.
  # pylint: disable=g-import-not-at-top
  import google.auth.compute_engine as google_auth_gce

  return (isinstance(cred, oauth2client_gce.AppAssertionCredentials) or
          isinstance(cred, google_auth_gce.credentials.Credentials))


def IsServiceAccountCredential(cred):
  """Checks if the credential is a service account credential."""
  # Import only when necessary to decrease the startup time. Move it to
  # global once google-auth is ready to replace oauth2client.
  # pylint: disable=g-import-not-at-top
  import google.oauth2.service_account as google_auth_service_account

  return (isinstance(cred, service_account.ServiceAccountCredentials) or
          isinstance(cred, google_auth_service_account.Credentials))


def IsImpersonationCredential(cred):
  """Checks if the credential is an impersonated service account credential."""
  return (impersonation_util.
          ImpersonationAccessTokenProvider.IsImpersonationCredential(cred))


def ValidIdTokenCredential(cred):
  return (IsImpersonationCredential(cred) or
          IsServiceAccountCredential(cred) or
          IsGceAccountCredentials(cred))


def PromptIfADCEnvVarIsSet():
  """Warns users if ADC environment variable is set."""
  override_file = config.ADCEnvVariable()
  if override_file:
    message = textwrap.dedent("""
          The environment variable [{envvar}] is set to:
            [{override_file}]
          Credentials will still be generated to the default location:
            [{default_file}]
          To use these credentials, unset this environment variable before
          running your application.
          """.format(
              envvar=client.GOOGLE_APPLICATION_CREDENTIALS,
              override_file=override_file,
              default_file=config.ADCFilePath()))
    console_io.PromptContinue(
        message=message, throw_if_unattended=True, cancel_on_no=True)


def WriteGcloudCredentialsToADC(creds, add_quota_project=False):
  """Writes gclouds's credential from auth login to ADC json."""
  # TODO(b/190114370): We will also support writing service account creds.
  if (not c_creds.IsUserAccountCredentials(creds) and
      not c_creds.IsExternalAccountCredentials(creds)):
    log.warning('Credentials cannot be written to application default '
                'credentials because it is not a user or external account '
                'credential.')
    return
  # Quota project ID should not be added to non-user credentials.
  if c_creds.IsExternalAccountCredentials(creds) and add_quota_project:
    raise AddQuotaProjectError(
        'The application default credentials are external account credentials, '
        'quota project cannot be added.')

  PromptIfADCEnvVarIsSet()
  if add_quota_project:
    c_creds.ADC(creds).DumpExtendedADCToFile()
  else:
    c_creds.ADC(creds).DumpADCToFile()


def GetADCAsJson():
  """Reads ADC from disk and converts it to a json object."""
  if not os.path.isfile(config.ADCFilePath()):
    return None
  with files.FileReader(config.ADCFilePath()) as f:
    return json.load(f)


def GetQuotaProjectFromADC():
  """Reads the quota project ID from ADC json file and return it."""
  adc_json = GetADCAsJson()
  try:
    return adc_json['quota_project_id']
  except (KeyError, TypeError):
    return None


def AssertADCExists():
  adc_path = config.ADCFilePath()
  if not os.path.isfile(adc_path):
    raise c_exc.BadFileException(
        'Application default credentials have not been set up. '
        'Run $ gcloud auth application-default login to set it up first.')


def ADCIsUserAccount():
  """Returns whether the ADC credentials correspond to a user account or not."""
  cred_file = config.ADCFilePath()
  creds, _ = c_creds.GetGoogleAuthDefault().load_credentials_from_file(
      cred_file)
  return (c_creds.IsUserAccountCredentials(creds) or
          c_creds.IsExternalAccountUserCredentials(creds))


def AdcHasGivenPermissionOnProject(project_id, permissions):
  AssertADCExists()
  project_ref = project_util.ParseProject(project_id)
  return _AdcHasGivenPermissionOnProjectHelper(project_ref, permissions)


def _AdcHasGivenPermissionOnProjectHelper(project_ref, permissions):
  cred_file_override_old = properties.VALUES.auth.credential_file_override.Get()
  try:
    properties.VALUES.auth.credential_file_override.Set(config.ADCFilePath())
    granted_permissions = projects_api.TestIamPermissions(
        project_ref, permissions).permissions
    return set(permissions) == set(granted_permissions)
  finally:
    properties.VALUES.auth.credential_file_override.Set(cred_file_override_old)


# Create this function to ease unit test mocks.
def GetAdcRealPath(adc_path):
  return os.path.realpath(adc_path)


def LogADCIsWritten(adc_path):
  """Prints the confirmation when ADC file was successfully written."""
  real_path = adc_path
  if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
    real_path = GetAdcRealPath(adc_path)
  log.status.Print('\nCredentials saved to file: [{}]'.format(real_path))
  log.status.Print(
      '\nThese credentials will be used by any library that requests '
      'Application Default Credentials (ADC).')
  # See https://bugs.python.org/issue40377 for the issue with python
  # from Microsoft store. The ADC file is transparently redirected to a
  # different path which client libraries do not expect, so cannot locate.
  if real_path != adc_path:
    log.warning('You may be running gcloud with a python interpreter installed '
                'from Microsoft Store which is not supported by this command. '
                'Run `gcloud topic startup` for instructions to select a '
                'different python interpreter. Otherwise, you have to '
                'set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` '
                'to the file path `{}`. See '
                'https://cloud.google.com/docs/authentication/'
                'getting-started#setting_the_environment_variable '
                'for more information.'.format(real_path))


def LogQuotaProjectAdded(quota_project):
  log.status.Print(
      '\nQuota project "{}" was added to ADC which can be used by Google '
      'client libraries for billing and quota. Note that some services may '
      'still bill the project owning the resource.'.format(quota_project))


def LogQuotaProjectNotFound():
  log.warning('\nCannot find a quota project to add to ADC. You might receive '
              'a "quota exceeded" or "API not enabled" error. Run $ gcloud '
              'auth application-default set-quota-project to add '
              'a quota project.')


def LogMissingPermissionOnQuotaProject(quota_project):
  log.warning(
      '\nCannot add the project "{}" to ADC as the quota project because the '
      'account in ADC does not have the "{}" permission on this project. '
      'You might receive a "quota_exceeded" or "API not enabled" error. '
      'Run $ gcloud auth application-default set-quota-project to add a quota '
      'project.'.format(quota_project, SERVICEUSAGE_PERMISSION))


def LogQuotaProjectDisabled():
  log.warning(
      '\nQuota project is disabled. You might receive a "quota exceeded" or '
      '"API not enabled" error. Run $ gcloud auth application-default '
      'set-quota-project to add a quota project.')


def DumpADC(credentials, quota_project_disabled=False):
  """Dumps the given credentials to ADC file.

  Args:
     credentials: a credentials from oauth2client or google-auth libraries, the
       credentials to dump.
     quota_project_disabled: bool, If quota project is explicitly disabled by
       users using flags.
  """
  adc_path = c_creds.ADC(credentials).DumpADCToFile()
  LogADCIsWritten(adc_path)
  if quota_project_disabled:
    LogQuotaProjectDisabled()


def DumpADCOptionalQuotaProject(credentials):
  """Dumps the given credentials to ADC file with an optional quota project.

  Loads quota project from gcloud's context and writes it to application default
  credentials file if the credentials has the "serviceusage.services.use"
  permission on the quota project..

  Args:
     credentials: a credentials from oauth2client or google-auth libraries, the
       credentials to dump.
  """
  adc_path = c_creds.ADC(credentials).DumpADCToFile()
  LogADCIsWritten(adc_path)

  quota_project = c_creds.GetQuotaProject(
      credentials, force_resource_quota=True)
  if not quota_project:
    LogQuotaProjectNotFound()
  elif AdcHasGivenPermissionOnProject(
      quota_project, permissions=[SERVICEUSAGE_PERMISSION]):
    c_creds.ADC(credentials).DumpExtendedADCToFile(quota_project=quota_project)
    LogQuotaProjectAdded(quota_project)
  else:
    LogMissingPermissionOnQuotaProject(quota_project)


def AddQuotaProjectToADC(quota_project):
  """Adds the quota project to the existing ADC file.

  Quota project is only added to ADC when the credentials have the
  "serviceusage.services.use" permission on the project.

  Args:
    quota_project: str, The project id of a valid GCP project to add to ADC.

  Raises:
    MissingPermissionOnQuotaProjectError: If the credentials do not have the
      "serviceusage.services.use" permission.
  """
  AssertADCExists()
  if not ADCIsUserAccount():
    raise c_exc.BadFileException(
        'The application default credentials are not user credentials, quota '
        'project cannot be added.')

  credentials, _ = c_creds.GetGoogleAuthDefault().load_credentials_from_file(
      config.ADCFilePath())
  previous_quota_project = credentials.quota_project_id

  adc_path = c_creds.ADC(credentials).DumpExtendedADCToFile(
      quota_project=quota_project)

  try:
    if not AdcHasGivenPermissionOnProject(
        quota_project, permissions=[SERVICEUSAGE_PERMISSION]):
      raise MissingPermissionOnQuotaProjectError(
          'Cannot add the project "{}" to application default credentials (ADC) '
          'as a quota project because the account in ADC does not have the '
          '"{}" permission on this project.'.format(quota_project,
                                                    SERVICEUSAGE_PERMISSION))
  except Exception:
    # Rollback the quota project before surfacing any exception that occurred.
    c_creds.ADC(credentials).DumpExtendedADCToFile(
        quota_project=previous_quota_project)
    raise

  LogADCIsWritten(adc_path)
  LogQuotaProjectAdded(quota_project)


def DumpImpersonatedServiceAccountToADC(credentials, target_principal,
                                        delegates):
  adc_path = c_creds.ADC(credentials, target_principal,
                         delegates).DumpADCToFile()
  LogADCIsWritten(adc_path)


def ExtractAndValidateAccount(account, creds):
  """Extracts account from creds and validates it against account."""
  decoded_id_token = jwt.decode(creds.id_token, verify=False)
  web_flow_account = decoded_id_token['email']
  if account and account.lower() != web_flow_account.lower():
    raise auth_exceptions.WrongAccountError(
        'You attempted to log in as account [{account}] but the received '
        'credentials were for account [{web_flow_account}].\n\n'
        'Please check that your browser is logged in as account [{account}] '
        'and that you are using the correct browser profile.'.format(
            account=account, web_flow_account=web_flow_account
        )
    )
  return web_flow_account
