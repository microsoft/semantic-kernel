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

"""Command to create named configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.configurations import named_configs


class Create(base.SilentCommand):
  """Creates a new named configuration."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          Except for special cases (NONE), configuration names start with a
          lower case letter and contain only lower case letters a-z, digits 0-9,
          and hyphens '-'.

          See `gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To create a new named configuration, run:

            $ {command} my-config
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_name',
        help='Name of the configuration to create')
    parser.add_argument(
        '--activate',
        action='store_true',
        default=True,
        help='If true, activate this configuration upon create.')
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
    created_config = named_configs.ConfigurationStore.CreateConfig(
        args.configuration_name
    )
    log.CreatedResource(args.configuration_name)
    if args.activate:
      named_configs.ConfigurationStore.ActivateConfig(args.configuration_name)
      log.status.Print('Activated [{0}].'.format(args.configuration_name))
    else:
      log.status.Print('To use this configuration, activate it by running:\n'
                       '  $ gcloud config configurations activate {name}\n\n'.
                       format(name=args.configuration_name))
    if args.universe_domain:
      created_config.PersistProperty(
          'core', 'universe_domain', args.universe_domain
      )
      log.status.Print('Updated property [core/universe_domain].')

    return args.configuration_name
