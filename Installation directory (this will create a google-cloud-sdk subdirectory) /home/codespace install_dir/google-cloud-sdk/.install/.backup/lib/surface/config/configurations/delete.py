# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command to delete named configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resource import resource_printer


class Delete(base.SilentCommand):
  """Deletes a named configuration."""

  detailed_help = {
      'DESCRIPTION': """\
          {description} You cannot delete a configuration that is active, even
          when overridden with the --configuration flag.  To delete the current
          active configuration, first `gcloud config configurations activate`
          another one.

          See `gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To delete an existing configuration named `my-config`, run:

            $ {command} my-config

          To delete more than one configuration, run:

            $ {command} my-config1 my-config2

          To list existing configurations, run:

            $ gcloud config configurations list
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_names',
        nargs='+',
        completer=completers.NamedConfigCompleter,
        help=('Name of the configuration to delete. '
              'Cannot be currently active configuration.'))

  def Run(self, args):
    # Fail the delete operation when we're attempting to delete the
    # active config.
    active_config = named_configs.ConfigurationStore.ActiveConfig()
    if active_config.name in args.configuration_names:
      raise named_configs.NamedConfigError(
          'Deleting named configuration failed because configuration '
          '[{0}] is set as active.  Use `gcloud config configurations '
          'activate` to change the active configuration.'.format(
              active_config.name))

    fmt = 'list[title="The following configurations will be deleted:"]'
    resource_printer.Print(args.configuration_names, fmt, out=log.status)
    console_io.PromptContinue(default=True, cancel_on_no=True)

    for configuration_name in args.configuration_names:
      named_configs.ConfigurationStore.DeleteConfig(configuration_name)
      config_store_to_delete = config.GetConfigStore(configuration_name)
      config_store_to_delete.DeleteConfig()
      log.DeletedResource(configuration_name)
