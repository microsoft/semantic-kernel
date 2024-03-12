# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Workflow to set up gcloud environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.command_lib import init_util
from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.diagnostics import network_diagnostics
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms

import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Init(base.Command):
  """Initialize or reinitialize gcloud.

  {command} launches an interactive Getting Started workflow for the gcloud
  command-line tool.
  It performs the following setup steps:

  - Authorizes gcloud and other SDK tools to access Google Cloud using
    your user account credentials, or from an account of your choosing whose
    credentials are already available.
  - Sets up a new or existing configuration.
  - Sets properties in that configuration, including the current project and
    optionally, the default Google Compute Engine region and zone you'd like to
    use.

  {command} can be used for initial setup of gcloud and to create new or
  reinitialize gcloud configurations. More information about configurations can
  be found by running `gcloud topic configurations`.

  Properties set by {command} are local and persistent, and are not affected by
  remote changes to the project. For example, the default Compute Engine zone in
  your configuration remains stable, even if you or another user changes the
  project-level default zone in the Cloud Platform Console.

  To sync the configuration, re-run `{command}`.

  ## EXAMPLES

  To launch an interactive Getting Started workflow, run:

    $ {command}

  To launch an interactive Getting Started workflow without diagnostics, run:

    $ {command} --skip-diagnostics

  """

  category = base.SDK_TOOLS_CATEGORY

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'obsolete_project_arg',
        nargs='?',
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    parser.add_argument(
        '--console-only',
        '--no-launch-browser',
        help=(
            'Prevent the command from launching a browser for '
            'authorization. Use this flag if you are on a machine that '
            'does not have a browser and you cannot install the '
            'gcloud CLI on another machine with a browser.'
        ),
        action='store_true',
    )
    parser.add_argument(
        '--no-browser',
        help=(
            'Prevent the command from launching a browser for '
            'authorization. Use this flag if you are on a machine that '
            'does not have a browser but you can install the '
            'gcloud CLI on another machine with a browser.'
        ),
        action='store_true',
    )
    parser.add_argument(
        '--skip-diagnostics',
        action='store_true',
        help='Do not run diagnostics.',
    )
    parser.add_argument(
        '--universe-domain',
        type=str,
        hidden=True,
        help=(
            'If set, creates the configuration with the specified'
            ' [core/universe_domain].'
        ),
    )

  def Run(self, args):
    """Allows user to select configuration, and initialize it."""
    if args.obsolete_project_arg:
      raise c_exc.InvalidArgumentException(
          args.obsolete_project_arg,
          '`gcloud init` has changed and no longer takes a PROJECT argument. '
          'Please use `gcloud source repos clone` to clone this '
          'project\'s source repositories.')

    log.status.write('Welcome! This command will take you through '
                     'the configuration of gcloud.\n\n')

    if properties.VALUES.core.disable_prompts.GetBool():
      raise c_exc.InvalidArgumentException(
          'disable_prompts/--quiet',
          'gcloud init command cannot run with disabled prompts.')

    configuration_name = self._PickConfiguration()
    if not configuration_name:
      return
    log.status.write('Your current configuration has been set to: [{0}]\n\n'
                     .format(configuration_name))

    if not args.skip_diagnostics:
      log.status.write('You can skip diagnostics next time by using the '
                       'following flag:\n')
      log.status.write('  gcloud init --skip-diagnostics\n\n')
      network_passed = network_diagnostics.NetworkDiagnostic().RunChecks()
      if not network_passed:
        if not console_io.PromptContinue(
            message='Network errors detected.',
            prompt_string='Would you like to continue anyway',
            default=False):
          log.status.write('You can re-run diagnostics with the following '
                           'command:\n')
          log.status.write('  gcloud info --run-diagnostics\n\n')
          return

    if args.universe_domain:
      properties.PersistProperty(
          properties.VALUES.core.universe_domain, args.universe_domain
      )
      return

    # User project quota is now the global default, but this command calls
    # legacy APIs where it should be disabled.
    with base.WithLegacyQuota():
      if not self._PickAccount(
          args.console_only, args.no_browser, preselected=args.account
      ):
        return

      if not self._PickProject(preselected=args.project):
        return

      self._PickDefaultRegionAndZone()

      self._CreateBotoConfig()

      self._Summarize(configuration_name)

  def _PickAccount(self, console_only, no_browser, preselected=None):
    """Checks if current credentials are valid, if not runs auth login.

    Args:
      console_only: bool, True if the auth flow shouldn't use the browser
      no_browser: bool, True if the auth flow shouldn't use the browser and
        should ask another gcloud installation to help with the browser flow.
      preselected: str, disable prompts and use this value if not None

    Returns:
      bool, True if valid credentials are setup.
    """

    new_credentials = False
    accounts = c_store.AvailableAccounts()
    if accounts:
      # There is at least one credentialed account.
      if preselected:
        # Try to use the preselected account. Fail if its not credentialed.
        account = preselected
        if account not in accounts:
          log.status.write('\n[{0}] is not one of your credentialed accounts '
                           '[{1}].\n'.format(account, ','.join(accounts)))
          return False
        # Fall through to the set the account property.
      else:
        # Prompt for the account to use.
        idx = console_io.PromptChoice(
            accounts + ['Log in with a new account'],
            message='Choose the account you would like to use to perform '
                    'operations for this configuration:',
            prompt_string=None)
        if idx is None:
          return False
        if idx < len(accounts):
          account = accounts[idx]
        else:
          new_credentials = True
    elif preselected:
      # Preselected account specified but there are no credentialed accounts.
      log.status.write('\n[{0}] is not a credentialed account.\n'.format(
          preselected))
      return False
    else:
      # Must log in with new credentials.
      answer = console_io.PromptContinue(
          prompt_string='You must log in to continue. Would you like to log in')
      if not answer:
        return False
      new_credentials = True
    if new_credentials:
      # Call `gcloud auth login` to get new credentials.
      # `gcloud auth login` may have user interaction, do not suppress it.
      if console_only:
        browser_args = ['--no-launch-browser']
      elif no_browser:
        browser_args = ['--no-browser']
      else:
        browser_args = []
      if not self._RunCmd(['auth', 'login'],
                          ['--force', '--brief'] + browser_args,
                          disable_user_output=False):
        return False
      # `gcloud auth login` already did `gcloud config set account`.
    else:
      # Set the config account to the already credentialed account.
      properties.PersistProperty(properties.VALUES.core.account, account)

    log.status.write('You are logged in as: [{0}].\n\n'
                     .format(properties.VALUES.core.account.Get()))
    return True

  def _PickConfiguration(self):
    """Allows user to re-initialize, create or pick new configuration.

    Returns:
      Configuration name or None.
    """
    configs = named_configs.ConfigurationStore.AllConfigs()
    active_config = named_configs.ConfigurationStore.ActiveConfig()

    if not configs or active_config.name not in configs:
      # Listing the configs will automatically create the default config.  The
      # only way configs could be empty here is if there are no configurations
      # and the --configuration flag or env var is set to something that does
      # not exist.  If configs has items, but the active config is not in there,
      # that similarly means that hey are using the flag or the env var and that
      # config does not exist.  In either case, just create it and go with that
      # one as the one that as they have already selected it.
      named_configs.ConfigurationStore.CreateConfig(active_config.name)
      # Need to active it in the file, not just the environment.
      active_config.Activate()
      return active_config.name

    # If there is a only 1 config, it is the default, and there are no
    # properties set, assume it was auto created and that it should be
    # initialized as if it didn't exist.
    if len(configs) == 1:
      default_config = configs.get(named_configs.DEFAULT_CONFIG_NAME, None)
      if default_config and not default_config.GetProperties():
        default_config.Activate()
        return default_config.name

    choices = []
    log.status.write('Settings from your current configuration [{0}] are:\n'
                     .format(active_config.name))
    log.status.flush()
    log.status.write(yaml.dump(properties.VALUES.AllValues()))
    log.out.flush()
    log.status.write('\n')
    log.status.flush()
    choices.append(
        'Re-initialize this configuration [{0}] with new settings '.format(
            active_config.name))
    choices.append('Create a new configuration')
    config_choices = [name for name, c in sorted(six.iteritems(configs))
                      if not c.is_active]
    choices.extend('Switch to and re-initialize '
                   'existing configuration: [{0}]'.format(name)
                   for name in config_choices)
    idx = console_io.PromptChoice(choices, message='Pick configuration to use:')
    if idx is None:
      return None
    if idx == 0:  # If reinitialize was selected.
      self._CleanCurrentConfiguration()
      return active_config.name
    if idx == 1:  # Second option is to create new configuration.
      return self._CreateConfiguration()
    config_name = config_choices[idx - 2]
    named_configs.ConfigurationStore.ActivateConfig(config_name)
    return config_name

  def _PickProject(self, preselected=None):
    """Allows user to select a project.

    Args:
      preselected: str, use this value if not None

    Returns:
      str, project_id or None if was not selected.
    """
    project_id = init_util.PickProject(preselected=preselected)
    if project_id is not None:
      properties.PersistProperty(properties.VALUES.core.project, project_id)
      log.status.write('Your current project has been set to: [{0}].\n\n'
                       .format(project_id))
    return project_id

  def _PickDefaultRegionAndZone(self):
    """Pulls metadata properties for region and zone and sets them in gcloud."""
    try:
      # Use --quiet flag to skip the enable api prompt.
      project_info = self._RunCmd(['compute', 'project-info', 'describe'],
                                  params=['--quiet'])
    except Exception:  # pylint:disable=broad-except
      log.status.write("""\
Not setting default zone/region (this feature makes it easier to use
[gcloud compute] by setting an appropriate default value for the
--zone and --region flag).
See https://cloud.google.com/compute/docs/gcloud-compute section on how to set
default compute region and zone manually. If you would like [gcloud init] to be
able to do this for you the next time you run it, make sure the
Compute Engine API is enabled for your project on the
https://console.developers.google.com/apis page.

""")
      return None

    default_zone = None
    default_region = None
    if project_info is not None:
      project_info = resource_projector.MakeSerializable(project_info)
      metadata = project_info.get('commonInstanceMetadata', {})
      for item in metadata.get('items', []):
        if item['key'] == 'google-compute-default-zone':
          default_zone = item['value']
        elif item['key'] == 'google-compute-default-region':
          default_region = item['value']

    # We could not determine zone automatically. Before offering choices for
    # zone and/or region ask user if he/she wants to do this.
    if not default_zone:
      answer = console_io.PromptContinue(
          prompt_string=('Do you want to configure a default Compute '
                         'Region and Zone?'))
      if not answer:
        return

    # Same logic applies to region and zone properties.
    def SetProperty(name, default_value, list_command):
      """Set named compute property to default_value or get via list command."""
      if not default_value:
        values = self._RunCmd(list_command)
        if values is None:
          return
        values = list(values)
        message = (
            'Which Google Compute Engine {0} would you like to use as project '
            'default?\n'
            'If you do not specify a {0} via a command line flag while working '
            'with Compute Engine resources, the default is assumed.').format(
                name)
        idx = console_io.PromptChoice(
            [value['name'] for value in values]
            + ['Do not set default {0}'.format(name)],
            message=message, prompt_string=None, allow_freeform=True,
            freeform_suggester=usage_text.TextChoiceSuggester())
        if idx is None or idx == len(values):
          return
        default_value = values[idx]
      properties.PersistProperty(properties.VALUES.compute.Property(name),
                                 default_value['name'])
      log.status.write('Your project default Compute Engine {0} has been set '
                       'to [{1}].\nYou can change it by running '
                       '[gcloud config set compute/{0} NAME].\n\n'
                       .format(name, default_value['name']))
      return default_value

    if default_zone:
      default_zone = self._RunCmd(['compute', 'zones', 'describe'],
                                  [default_zone])
    zone = SetProperty('zone', default_zone, ['compute', 'zones', 'list'])
    if zone and not default_region:
      default_region = zone['region']
    if default_region:
      default_region = self._RunCmd(['compute', 'regions', 'describe'],
                                    [default_region])
    SetProperty('region', default_region, ['compute', 'regions', 'list'])

  def _Summarize(self, configuration_name):
    log.status.Print('Your Google Cloud SDK is configured and ready to use!\n')

    log.status.Print(
        '* Commands that require authentication will use {0} by default'
        .format(properties.VALUES.core.account.Get()))
    project = properties.VALUES.core.project.Get()
    if project:
      log.status.Print(
          '* Commands will reference project `{0}` by default'
          .format(project))
    region = properties.VALUES.compute.region.Get()
    if region:
      log.status.Print(
          '* Compute Engine commands will use region `{0}` by default'
          .format(region))
    zone = properties.VALUES.compute.zone.Get()
    if zone:
      log.status.Print(
          '* Compute Engine commands will use zone `{0}` by default\n'
          .format(zone))

    log.status.Print(
        'Run `gcloud help config` to learn how to change individual settings\n')

    log.status.Print(
        'This gcloud configuration is called [{config}]. You can create '
        'additional configurations if you work with multiple accounts and/or '
        'projects.'.format(config=configuration_name))
    log.status.Print('Run `gcloud topic configurations` to learn more.\n')

    log.status.Print('Some things to try next:\n')

    log.status.Print(
        '* Run `gcloud --help` to see the Cloud Platform services you can '
        'interact with. And run `gcloud help COMMAND` to get help on any '
        'gcloud command.')
    log.status.Print(
        '* Run `gcloud topic --help` to learn about advanced features of the '
        'SDK like arg files and output formatting')

    log.status.Print(
        '* Run `gcloud cheat-sheet` to see a roster of go-to `gcloud` '
        'commands.')

  def _CreateConfiguration(self):
    configuration_name = console_io.PromptResponse(
        'Enter configuration name. Names start with a lower case letter and '
        'contain only lower case letters a-z, digits 0-9, and hyphens \'-\':  ')
    configuration_name = configuration_name.strip()
    named_configs.ConfigurationStore.CreateConfig(configuration_name)
    named_configs.ConfigurationStore.ActivateConfig(configuration_name)
    named_configs.ActivePropertiesFile.Invalidate()
    return configuration_name

  def _CreateBotoConfig(self):
    gsutil_path = _FindGsutil()
    if not gsutil_path:
      log.debug('Unable to find [gsutil]. Not configuring default .boto '
                'file')
      return

    boto_path = files.ExpandHomeDir(os.path.join('~', '.boto'))
    if os.path.exists(boto_path):
      log.debug('Not configuring default .boto file. File already '
                'exists at [{boto_path}].'.format(boto_path=boto_path))
      return

    # 'gsutil config -n' creates a default .boto file that the user can read and
    # modify.
    command_args = ['config', '-n', '-o', boto_path]
    if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
      gsutil_args = execution_utils.ArgsForCMDTool(gsutil_path,
                                                   *command_args)
    else:
      gsutil_args = execution_utils.ArgsForExecutableTool(gsutil_path,
                                                          *command_args)

    return_code = execution_utils.Exec(gsutil_args, no_exit=True,
                                       out_func=log.file_only_logger.debug,
                                       err_func=log.file_only_logger.debug)
    if return_code == 0:
      log.status.write("""\
Created a default .boto configuration file at [{boto_path}]. See this file and
[https://cloud.google.com/storage/docs/gsutil/commands/config] for more
information about configuring Google Cloud Storage.
""".format(boto_path=boto_path))

    else:
      log.status.write('Error creating a default .boto configuration file. '
                       'Please run [gsutil config -n] if you would like to '
                       'create this file.\n')

  def _CleanCurrentConfiguration(self):
    properties.PersistProperty(properties.VALUES.core.account, None)
    properties.PersistProperty(properties.VALUES.core.project, None)
    properties.PersistProperty(properties.VALUES.compute.region, None)
    properties.PersistProperty(properties.VALUES.compute.zone, None)
    named_configs.ActivePropertiesFile.Invalidate()

  def _RunCmd(self, cmd, params=None, disable_user_output=True):
    if not self._cli_power_users_only.IsValidCommand(cmd):
      log.info('Command %s does not exist.', cmd)
      return None
    if params is None:
      params = []
    args = cmd + params
    log.info('Executing: [gcloud %s]', ' '.join(args))
    try:
      # Disable output from individual commands, so that we get
      # command run results, and don't clutter output of init.
      if disable_user_output:
        args.append('--no-user-output-enabled')

      if (properties.VALUES.core.verbosity.Get() is None and
          disable_user_output):
        # Unless user explicitly set verbosity, suppress from subcommands.
        args.append('--verbosity=none')

      if properties.VALUES.core.log_http.GetBool():
        args.append('--log-http')

      return resource_projector.MakeSerializable(
          self.ExecuteCommandDoNotUse(args))

    except SystemExit as exc:
      log.info('[%s] has failed\n', ' '.join(cmd + params))
      raise c_exc.FailedSubCommand(cmd + params, exc.code)
    except BaseException:
      log.info('Failed to run [%s]\n', ' '.join(cmd + params))
      raise


def _FindGsutil():
  """Finds the bundled gsutil wrapper.

  Returns:
    The path to gsutil.
  """
  sdk_bin_path = config.Paths().sdk_bin_path
  if not sdk_bin_path:
    return

  if platforms.OperatingSystem.Current() == platforms.OperatingSystem.WINDOWS:
    gsutil = 'gsutil.cmd'
  else:
    gsutil = 'gsutil'
  return os.path.join(sdk_bin_path, gsutil)
