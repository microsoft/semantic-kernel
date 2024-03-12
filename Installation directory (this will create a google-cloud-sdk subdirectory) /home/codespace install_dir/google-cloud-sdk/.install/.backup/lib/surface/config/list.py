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
"""Command to list properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs


class BadConfigListInvocation(exceptions.Error):
  """Exception for incorrect invocations of `config list`."""


class List(base.ListCommand):
  """List Google Cloud CLI properties for the currently active configuration.

  {command} lists the properties of the specified section using the
  active configuration. These include the account used to authorize access to
  Google Cloud, the current Google Cloud project, and the default Compute Engine
  region and zone, if set. See `gcloud topic configurations` for more about
  configurations.

  ## AVAILABLE PROPERTIES

  {properties}

  ## EXAMPLES

  To list the set project property in the core section, run:

    $ {command} project

  To list the set zone property in the compute section, run:

    $ {command} compute/zone

  To list all the set properties in the compute section, run:

  $ {command} compute/

  To list all the properties in the compute section, run:

  $ {command} compute/ --all

  To list all the properties, run:

    $ {command} --all

  Note, you cannot specify both `--all` and a property name. Only a section name
  and the `--all` flag can be used together in the format `gcloud config list
  <SECTION>/ --all`.
  """

  detailed_help = {'properties': properties.VALUES.GetHelpString()}

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        '--all',
        action='store_true',
        help='List all set and unset properties that match the arguments.')
    parser.add_argument(
        'property',
        metavar='SECTION/PROPERTY',
        nargs='?',
        completer=completers.PropertiesCompleter,
        help='Property to be listed. Note that SECTION/ is optional while '
        'referring to properties in the core section.')
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat('config')
    parser.display_info.AddCacheUpdater(None)

  def _GetPropertiesToDisplay(self, args):
    """List available regular properties."""
    section, prop = properties.ParsePropertyString(args.property)

    if prop:
      return {
          section: {
              prop: properties.VALUES.Section(section).Property(prop).Get()
          }
      }
    if section:
      return {
          section:
              properties.VALUES.Section(section).AllValues(list_unset=args.all)
      }
    return properties.VALUES.AllValues(list_unset=args.all)

  def Run(self, args):
    _, prop = properties.ParsePropertyString(args.property)
    if args.all and prop:
      raise BadConfigListInvocation(
          'Commands with the `--all` flag must be in the format `gcloud '
          'config list <SECTION>/` without a property specified.')
    return self._GetPropertiesToDisplay(args)

  def Epilog(self, resources_were_displayed):
    config_name = named_configs.ConfigurationStore.ActiveConfig().name
    log.status.write(
        '\nYour active configuration is: [{0}]\n'.format(config_name))
