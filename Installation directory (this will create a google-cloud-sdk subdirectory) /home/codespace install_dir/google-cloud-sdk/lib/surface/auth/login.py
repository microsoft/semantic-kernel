# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""The auth command gets tokens via oauth2."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.auth import external_account as auth_external_account
from googlecloudsdk.api_lib.auth import service_account as auth_service_account
from googlecloudsdk.api_lib.auth import util as auth_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.auth import auth_util as command_auth_util
from googlecloudsdk.command_lib.auth import flags as auth_flags
from googlecloudsdk.command_lib.auth import workforce_login_config as workforce_login_config_util
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import creds as c_creds
from googlecloudsdk.core.credentials import devshell as c_devshell
from googlecloudsdk.core.credentials import exceptions as creds_exceptions
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.credentials import store as c_store


def ShouldContinueLogin(cred_config):
  """Prompts users if they try to login in managed environments.

  Args:
    cred_config: Json object loaded from the file specified in --cred-file.

  Returns:
    True if users want to continue the login command.
  """
  if c_devshell.IsDevshellEnvironment():
    message = textwrap.dedent("""
          You are already authenticated with gcloud when running
          inside the Cloud Shell and so do not need to run this
          command. Do you wish to proceed anyway?
          """)
    return console_io.PromptContinue(message=message)
  elif (c_gce.Metadata().connected and
        not auth_external_account.IsExternalAccountConfig(cred_config)):
    message = textwrap.dedent("""
          You are running on a Google Compute Engine virtual machine.
          It is recommended that you use service accounts for authentication.

          You can run:

            $ gcloud config set account `ACCOUNT`

          to switch accounts if necessary.

          Your credentials may be visible to others with access to this
          virtual machine. Are you sure you want to authenticate with
          your personal account?
          """)
    return console_io.PromptContinue(message=message)
  else:
    return True


def GetScopes(args):
  scopes = config.CLOUDSDK_SCOPES
  # Add REAUTH scope in case the user has 2fact activated.
  # This scope is only used here and when refreshing the access token.
  scopes += (config.REAUTH_SCOPE,)

  if args.enable_gdrive_access:
    scopes += (auth_util.GOOGLE_DRIVE_SCOPE,)
  return scopes


def ShouldUseCachedCredentials(args, scopes):
  """If the login should use the locally cached account."""
  if (not args.account) or args.force:
    return False
  try:
    creds = c_store.Load(account=args.account, scopes=scopes)
  except creds_exceptions.Error:
    return False
  if not creds:
    return False
  # Account already has valid creds, just switch to it.
  log.warning('Re-using locally stored credentials for [{}]. '
              'To fetch new credentials, re-run the command with the '
              '`--force` flag.'.format(args.account))
  return True


class Login(base.Command):
  """Authorize gcloud to access the Cloud Platform with Google user credentials.

  Obtains access credentials for your user account via a web-based authorization
  flow. When this command completes successfully, it sets the active account
  in the current configuration to the account specified. If no configuration
  exists, it creates a configuration named default.

  If valid credentials for an account are already available from a prior
  authorization, the account is set to active without rerunning the flow.

  Use `gcloud auth list` to view credentialed accounts.

  If you'd rather authorize without a web browser but still interact with
  the command line, use the `--no-browser` flag. To authorize without
  a web browser and non-interactively, create a service account with the
  appropriate scopes using the
  [Google Cloud Console](https://console.cloud.google.com) and use
  `gcloud auth activate-service-account` with the corresponding JSON key file.

  In addition to Google user credentials, authorization using workload identity
  federation, workforce identity federation, or service account keys is also
  supported.

  For authorization with external accounts or service accounts, the
  `--cred-file` flag must be specified with the path
  to the workload identity credential configuration file or service account key
  file (JSON).

  Login with workload and workforce identity federation is also supported in
  both gsutil and bq. This command is the recommended way of using external
  accounts.

  For more information on workload identity federation, see:
  [](https://cloud.google.com/iam/docs/workload-identity-federation).

  For more information on workforce identity federation, see:
  [](https://cloud.google.com/iam/docs/workforce-identity-federation).

  For more information on authorization and credential types, see:
  [](https://cloud.google.com/sdk/docs/authorizing).

  ## EXAMPLES

  To obtain access credentials for your user account, run:

    $ {command}

  To obtain access credentials using workload or workforce identity federation,
  run:

    $ {command} --cred-file=/path/to/configuration/file

  To obtain access credentials using a browser-based sign-in flow with workforce
  identity federation, run:

    $ {command} --login-config=/path/to/configuration/file
  """

  _remote_login_with_auth_proxy = False

  @staticmethod
  def Args(parser):
    """Set args for gcloud auth."""
    parser.add_argument(
        '--activate',
        action='store_true',
        default=True,
        help='Set the new account to active.',
    )
    # --do-not-activate for (hidden) backwards compatibility.
    parser.add_argument(
        '--do-not-activate',
        action='store_false',
        dest='activate',
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.',
    )
    parser.add_argument(
        '--brief', action='store_true', help='Minimal user output.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help=(
            'Re-run the web authorization flow even if the given account has '
            'valid credentials.'
        ),
    )
    parser.add_argument(
        '--enable-gdrive-access',
        action='store_true',
        help='Enable Google Drive access.',
    )
    parser.add_argument(
        '--update-adc',
        action='store_true',
        default=False,
        help=(
            'Write the obtained credentials to the well-known location for '
            'Application Default Credentials (ADC). Run '
            '$ gcloud auth application-default --help to learn more about ADC. '
            'Any credentials previously generated by '
            '`gcloud auth application-default login` will be overwritten.'
        ),
    )
    parser.add_argument(
        '--add-quota-project-to-adc',
        action='store_true',
        default=False,
        hidden=True,
        help=(
            "Read the project from gcloud's context and write to application "
            'default credentials as the quota project. Use this flag only '
            'when --update-adc is specified.'
        ),
    )
    parser.add_argument(
        'account',
        nargs='?',
        help=(
            'User account used for authorization. When the account specified '
            'has valid credentials in the local credential store these '
            'credentials will be re-used, otherwise a new credential will be '
            'fetched. If you need to fetch a new credential for an account '
            'with valid credentials stored, run the command with the --force '
            'flag.'
        )
    )
    parser.add_argument(
        '--cred-file',
        help=(
            'Path to the external account configuration file (workload identity'
            ' pool, generated by the Cloud Console or `gcloud iam'
            ' workload-identity-pools create-cred-config`) or service account'
            ' credential key file (JSON).'
        ),
    )
    parser.add_argument(
        '--login-config',
        help=(
            'Path to the workforce identity federation login configuration'
            ' file which can be generated using the `gcloud iam'
            ' workforce-pools create-login-config` command.'
        ),
        action=actions.StoreProperty(properties.VALUES.auth.login_config_file),
    )

    auth_flags.AddRemoteLoginFlags(parser)

    parser.display_info.AddFormat('none')

  def Run(self, args):
    """Run the authentication command."""
    if args.cred_file:
      if args.login_config:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--login-config cannot be specified with --cred-file.')
      cred_file = auth_util.GetCredentialsConfigFromFile(args.cred_file)
    else:
      cred_file = None

    scopes = GetScopes(args)

    if not ShouldContinueLogin(cred_file):
      return None

    if args.cred_file:
      return LoginWithCredFileConfig(cred_file, scopes, args.project,
                                     args.activate, args.brief, args.update_adc,
                                     args.add_quota_project_to_adc,
                                     args.account)
    if ShouldUseCachedCredentials(args, scopes):
      creds = c_store.Load(account=args.account, scopes=scopes)
      return LoginAs(args.account, creds, args.project, args.activate,
                     args.brief, args.update_adc, args.add_quota_project_to_adc)

    # No valid creds, do the web flow.
    flow_params = dict(
        no_launch_browser=not args.launch_browser,
        no_browser=args.no_browser,
        remote_bootstrap=args.remote_bootstrap)

    # 1. Try the 3PI web flow with --no-browser:
    #    This could be a 3PI flow initiated via --no-browser.
    #    If provider_name is present, then this is the 3PI flow.
    #    We can start the flow as is as the remote_bootstrap value will be used.
    if args.remote_bootstrap and 'provider_name' in args.remote_bootstrap:
      creds = auth_util.DoInstalledAppBrowserFlowGoogleAuth(
          config.CLOUDSDK_EXTERNAL_ACCOUNT_SCOPES,
          auth_proxy_redirect_uri='https://sdk.cloud.google/authcode.html',
          **flow_params
      )
      universe_domain_property = properties.VALUES.core.universe_domain
      if (
          creds
          and hasattr(creds, 'universe_domain')
          and creds.universe_domain != universe_domain_property.Get()
      ):
        # Get the account and handle universe domain conflict.
        account = auth_external_account.GetExternalAccountId(creds)
        auth_util.HandleUniverseDomainConflict(creds.universe_domain, account)
      return
    # 2. Try the 3PI web flow with a login configuration file.
    login_config_file = workforce_login_config_util.GetWorkforceLoginConfig()
    if login_config_file:
      if args.update_adc:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--update-adc cannot be used in a third party login flow. '
            'Please use `gcloud auth application-default login`.')
      if args.add_quota_project_to_adc:
        raise calliope_exceptions.ConflictingArgumentsException(
            '--add-quota-project-to-adc cannot be used in a third party login '
            'flow.')
      creds = workforce_login_config_util.DoWorkforceHeadfulLogin(
          login_config_file,
          auth_proxy_redirect_uri='https://sdk.cloud.google/authcode.html',
          **flow_params)

      account = auth_external_account.GetExternalAccountId(creds)
      c_store.Store(creds, account, config.CLOUDSDK_EXTERNAL_ACCOUNT_SCOPES)
      return LoginAs(account, creds, args.project, args.activate, args.brief,
                     args.update_adc, args.add_quota_project_to_adc)

    # 3. Try the 1P web flow.
    creds = auth_util.DoInstalledAppBrowserFlowGoogleAuth(
        scopes,
        auth_proxy_redirect_uri='https://sdk.cloud.google.com/authcode.html',
        **flow_params)
    if not creds:
      return
    account = command_auth_util.ExtractAndValidateAccount(args.account, creds)
    # We got new creds, and they are for the correct user.
    c_store.Store(creds, account, scopes)
    return LoginAs(account, creds, args.project, args.activate, args.brief,
                   args.update_adc, args.add_quota_project_to_adc)


def LoginWithCredFileConfig(cred_config, scopes, project, activate, brief,
                            update_adc, add_quota_project_to_adc, args_account):
  """Login with the provided configuration loaded from --cred-file.

  Args:
    cred_config (Mapping): The configuration dictionary representing the
      credentials. This is loaded from the --cred-file argument.
    scopes (Tuple[str]): The default OAuth scopes to use.
    project (Optional[str]): The optional project ID to activate / persist.
    activate (bool): Whether to set the new account associated with the
      credentials to active.
    brief (bool): Whether to use minimal user output.
    update_adc (bool): Whether to write the obtained credentials to the
      well-known location for Application Default Credentials (ADC).
    add_quota_project_to_adc (bool): Whether to add the quota project to the
      application default credentials file.
    args_account (Optional[str]): The optional ACCOUNT argument. When provided,
      this should match the account ID on the authenticated credentials.

  Returns:
    google.auth.credentials.Credentials: The authenticated stored credentials.

  Raises:
    calliope_exceptions.ConflictingArgumentsException: If conflicting arguments
      are provided.
    calliope_exceptions.InvalidArgumentException: If invalid arguments are
      provided.
  """
  # Remove reauth scope (only applicable to 1P user accounts).
  scopes = tuple(x for x in scopes if x != config.REAUTH_SCOPE)
  # Reject unsupported arguments.
  if add_quota_project_to_adc:
    raise calliope_exceptions.ConflictingArgumentsException(
        '[--add-quota-project-to-adc] cannot be specified with --cred-file')
  if auth_external_account.IsExternalAccountConfig(cred_config):
    creds = auth_external_account.CredentialsFromAdcDictGoogleAuth(cred_config)
    account = auth_external_account.GetExternalAccountId(creds)
    # Check interactive mode, if true, inject the _tokeninfo_username.
    # TODO(b/258323440): Once the SDK can handle the retrieving token info, we
    # don't need this injection any more.
    if hasattr(creds, 'interactive') and creds.interactive:
      setattr(creds, '_tokeninfo_username', account)
  elif auth_service_account.IsServiceAccountConfig(cred_config):
    creds = auth_service_account.CredentialsFromAdcDictGoogleAuth(cred_config)
    account = creds.service_account_email
  else:
    raise calliope_exceptions.InvalidArgumentException(
        '--cred-file',
        'Only external account or service account JSON credential file types '
        'are supported.')

  if args_account and args_account != account:
    raise calliope_exceptions.InvalidArgumentException(
        'ACCOUNT',
        'The given account name does not match the account name in the '
        'credential file. This argument can be omitted when using '
        'credential files.')
  # Check if account already exists in storage.
  try:
    # prevent_refresh must be set to True. We don't actually want to
    # use the existing credentials, but check for their presence. If a
    # refresh occurs but the credentials are no longer valid, this
    # will cause gcloud to crash.
    exist_creds = c_store.Load(
        account=account, scopes=scopes, prevent_refresh=True)
  except creds_exceptions.Error:
    exist_creds = None
  if exist_creds:
    message = textwrap.dedent("""
      You are already authenticated with '%s'.
      Do you wish to proceed and overwrite existing credentials?
      """)
    answer = console_io.PromptContinue(message=message % account, default=True)
    if not answer:
      return None
  # Store credentials and activate if --activate is true.
  c_store.Store(creds, account, scopes=scopes)
  return LoginAs(account, creds, project, activate, brief, update_adc, False)


def LoginAs(account, creds, project, activate, brief, update_adc,
            add_quota_project_to_adc):
  """Logs in with valid credentials."""
  if hasattr(creds, 'universe_domain'):
    auth_util.HandleUniverseDomainConflict(creds.universe_domain, account)

  _ValidateADCFlags(update_adc, add_quota_project_to_adc)
  if update_adc:
    _UpdateADC(creds, add_quota_project_to_adc)
  if not activate:
    return creds
  properties.PersistProperty(properties.VALUES.core.account, account)
  if project:
    properties.PersistProperty(properties.VALUES.core.project, project)

  if not brief:
    if c_creds.IsExternalAccountCredentials(creds):
      confirmation_msg = (
          'Authenticated with external account credentials for: [{0}].'.format(
              account))
    elif c_creds.IsExternalAccountUserCredentials(creds):
      confirmation_msg = (
          'Authenticated with external account user credentials for: '
          '[{0}].'.format(account))
    elif c_creds.IsServiceAccountCredentials(creds):
      confirmation_msg = (
          'Authenticated with service account credentials for: [{0}].'.format(
              account))
    elif c_creds.IsExternalAccountAuthorizedUserCredentials(creds):
      confirmation_msg = (
          'Authenticated with external account authorized user credentials '
          'for: [{0}].'.format(account))
    else:
      confirmation_msg = 'You are now logged in as [{0}].'.format(account)
    log.status.write(
        '\n{confirmation_msg}\n'
        'Your current project is [{project}].  You can change this setting '
        'by running:\n  $ gcloud config set project PROJECT_ID\n'.format(
            confirmation_msg=confirmation_msg,
            project=properties.VALUES.core.project.Get()))
  return creds


def _UpdateADC(creds, add_quota_project_to_adc):
  """Updates the ADC json with the credentials creds."""
  old_adc_json = command_auth_util.GetADCAsJson()
  command_auth_util.WriteGcloudCredentialsToADC(creds, add_quota_project_to_adc)
  new_adc_json = command_auth_util.GetADCAsJson()
  if new_adc_json and new_adc_json != old_adc_json:
    adc_msg = '\nApplication Default Credentials (ADC) were updated.'
    quota_project = command_auth_util.GetQuotaProjectFromADC()
    if quota_project:
      adc_msg = adc_msg + (
          "\n'{}' is added to ADC as the quota project.\nTo "
          'just update the quota project in ADC, use $gcloud auth '
          'application-default set-quota-project.'.format(quota_project))
    log.status.Print(adc_msg)


def _ValidateADCFlags(update_adc, add_quota_project_to_adc):
  if not update_adc and add_quota_project_to_adc:
    raise calliope_exceptions.InvalidArgumentException(
        '--add-quota-project-to-adc',
        '--add-quota-project-to-adc cannot be specified without specifying '
        '--update-adc.'
    )
