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

"""Command to set properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.command_lib.config import config_validators
from googlecloudsdk.command_lib.config import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import store as c_store


class Set(base.Command):
  """Set a Google Cloud CLI property.

  {command} sets the specified property in your active configuration only. A
  property governs the behavior of a specific aspect of Google Cloud CLI such as
  the service account to use or the verbosity level of logs. To
  set the property across all configurations, use the `--installation` flag. For
  more information regarding creating and using configurations, see
  `gcloud topic configurations`.

  To view a list of properties currently in use, run `gcloud config list`.

  To unset properties, use `gcloud config unset`.

  Google Cloud CLI comes with a `default` configuration. To create multiple
  configurations, use `gcloud config configurations create`, and
  `gcloud config configurations activate` to switch between them.

  Note: If you are using Cloud Shell, your gcloud command-line tool preferences
  are stored in a temporary `tmp` folder, set for your current tab only, and do
  not persist across sessions. For details on how to make these configurations
  persist, refer to the Cloud Shell
  guide on setting gcloud command-line tool preferences:
  https://cloud.google.com/shell/docs/configuring-cloud-shell#gcloud_command-line_tool_preferences.

  ## AVAILABLE PROPERTIES

  {properties}

  ## EXAMPLES

  To set the `project` property in the core section, run:

    $ {command} project PROJECT_ID

  To set the `zone` property in the `compute` section, run:

    $ {command} compute/zone ZONE_NAME

  To disable prompting for scripting, run:

    $ {command} disable_prompts true

  To set a proxy with the appropriate type, and specify the address and port on
  which to reach it, run:

    $ {command} proxy/type http
    $ {command} proxy/address 1.234.56.78
    $ {command} proxy/port 8080

  For a full list of accepted values, see
  https://cloud.google.com/sdk/gcloud/reference/topic/configurations#AVAILABLE-PROPERTIES.
  """

  detailed_help = {'properties': properties.VALUES.GetHelpString()}

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'property',
        metavar='SECTION/PROPERTY',
        completer=completers.PropertiesCompleter,
        help='Property to be set. Note that SECTION/ is optional while '
        'referring to properties in the core section, i.e., using either '
        '`core/project` or `project` is a valid way of setting a project. '
        'Using section names is required for setting other properties like '
        '`compute/region`. Consult the Available Properties section below '
        'for a comprehensive list of properties.')
    parser.add_argument(
        'value',
        completer=completers.PropertyValueCompleter,
        help='Value to be set.')

    flags.INSTALLATION_FLAG.AddToParser(parser)

  def Run(self, args):
    scope = (properties.Scope.INSTALLATION if args.installation
             else properties.Scope.USER)

    prop = properties.FromString(args.property)
    if not prop:
      raise c_exc.InvalidArgumentException(
          'property', 'Must be in the form: [SECTION/]PROPERTY')

    scope_msg = ''
    if args.installation:
      scope_msg = 'installation '

    if prop == properties.VALUES.context_aware.use_client_certificate:
      config_validators.WarnIfActivateUseClientCertificate(args.value)

    showed_warning = False
    if prop == properties.VALUES.core.project:
      # This warning is informational and should not ask for confirmation
      config_validators.WarnIfSettingProjectWhenAdcExists(args.value)
      showed_warning = config_validators.WarnIfSettingProjectWithNoAccess(
          scope, args.value)
    if prop == properties.VALUES.compute.zone:
      showed_warning = config_validators.WarnIfSettingNonExistentRegionZone(
          args.value, zonal=True)
    if prop == properties.VALUES.compute.region:
      showed_warning = config_validators.WarnIfSettingNonExistentRegionZone(
          args.value, zonal=False)
    if prop.section == properties.VALUES.api_endpoint_overrides.name:
      showed_warning = config_validators.WarnIfSettingApiEndpointOverrideOutsideOfConfigUniverse(
          args.value, prop
      )
    cred_account_universe_domain = None
    if prop == properties.VALUES.core.account:
      cred_account_universe_domain = (
          c_store.GetCredentialedAccountUniverseDomain(args.value)
      )
      showed_warning = (
          config_validators.WarnIfSettingAccountOutsideOfConfigUniverse(
              args.value, cred_account_universe_domain
          )
      )
    if prop == properties.VALUES.core.universe_domain:
      showed_warning = config_validators.WarnIfSettingUniverseDomainOutsideOfConfigAccountUniverse(
          args.value
      )

    if showed_warning and not args.quiet and console_io.CanPrompt():
      if not console_io.PromptContinue(
          'Are you sure you wish to set {0}property [{1}] to {2}?'.format(
              scope_msg, prop, args.value
          )
      ):
        return

    properties.PersistProperty(prop, args.value, scope=scope)
    log.status.Print('Updated {0}property [{1}].'.format(scope_msg, prop))
    if cred_account_universe_domain and showed_warning:
      properties.PersistProperty(
          properties.VALUES.core.universe_domain,
          cred_account_universe_domain,
          scope=scope,
      )
      log.status.Print('Updated [core/universe_domain] to match.')
