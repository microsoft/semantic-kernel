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
"""Command to set properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs

import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Get(base.Command):
  """Print the value of a Google Cloud CLI property.

  {command} prints the property value from your active client side configuration
  only.

  ## AVAILABLE PROPERTIES

  {properties}

  ## EXAMPLES

  To print the project property in the core section, run:

    $ {command} project

  To print the zone property in the compute section, run:

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
        help='The property to be fetched. Note that `SECTION/` is optional'
        ' while referring to properties in the core section.')
    parser.display_info.AddFormat('value(.)')

  def Run(self, args):
    config_name = named_configs.ConfigurationStore.ActiveConfig().name
    if config_name != 'default':
      log.status.write('Your active configuration is: [{0}]\n'.format(
          config_name))

    section, prop = properties.ParsePropertyString(args.property)
    if not prop:
      if section:
        err_msg = ('You cannot call get on a SECTION/. '
                   'Did you mean `gcloud config list SECTION`?')
        raise c_exc.InvalidArgumentException('property', err_msg)
      raise c_exc.InvalidArgumentException(
          'property', 'Must be in the form: [SECTION/]PROPERTY')
    try:
      value = properties.VALUES.Section(section).Property(prop).Get(
          validate=True)
      if not value:
        # Writing message to stderr but returning any potentially empty
        # value to caller as is
        log.err.Print('(unset)')
        if section == properties.VALUES.api_endpoint_overrides.name:
          api_version = apis.ResolveVersion(prop)
          default_endpoint = apis.GetEffectiveApiEndpoint(prop, api_version)
          log.status.Print('Defaults to ', default_endpoint)
    except properties.InvalidValueError as e:
      # Writing warning to stderr but returning invalid value as is
      log.warning(six.text_type(e))
      value = properties.VALUES.Section(section).Property(prop).Get(
          validate=False)
    return value
