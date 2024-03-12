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

"""Command to unset properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.command_lib.config import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Unset(base.Command):
  """Unset a Google Cloud CLI property.

  By default, unsets the property in your active configuration only. Use the
  `--installation` flag to unset the property across all configurations. See
  `gcloud topic configurations` for more information.

  ## AVAILABLE PROPERTIES

  {properties}

  ## EXAMPLES

  To unset the project property in the core section, run:

    $ {command} project

  To unset the zone property in the compute section, run:

    $ {command} compute/zone
  """

  detailed_help = {'properties': properties.VALUES.GetHelpString()}

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'property',
        metavar='SECTION/PROPERTY',
        completer=completers.PropertiesCompleter,
        help='The property to be unset. Note that SECTION/ is optional while '
        'referring to properties in the core section.')

    flags.INSTALLATION_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs this command."""
    scope = (properties.Scope.INSTALLATION if args.installation
             else properties.Scope.USER)

    prop = properties.FromString(args.property)
    if not prop:
      raise c_exc.InvalidArgumentException(
          'property', 'Must be in the form: [SECTION/]PROPERTY')
    properties.PersistProperty(prop, None, scope=scope)

    scope_msg = ''
    if args.installation:
      scope_msg = 'installation '
    log.status.Print('Unset {0}property [{1}].'.format(scope_msg, prop))
