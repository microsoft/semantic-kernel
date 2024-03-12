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

"""Command to list named configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file

import six


class List(base.ListCommand):
  """Lists existing named configurations."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          Run `$ gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To list all available configurations, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    configs = named_configs.ConfigurationStore.AllConfigs()
    table_format = """table(
        name,
        is_active,
        properties.core.account,
        properties.core.project,
        properties.compute.zone:label=COMPUTE_DEFAULT_ZONE,
        properties.compute.region:label=COMPUTE_DEFAULT_REGION)
    """
    for _, config in sorted(six.iteritems(configs)):
      props = properties.VALUES.AllValues(
          list_unset=True,
          include_hidden=True,
          properties_file=properties_file.PropertiesFile([config.file_path]),
      )
      config_universe = props['core'].get('universe_domain')
      if (
          config_universe
          and config_universe != properties.VALUES.core.universe_domain.default
      ):
        table_format = """table(
          name,
          is_active,
          properties.core.account,
          properties.core.project,
          properties.core.universe_domain,
          properties.compute.zone:label=COMPUTE_DEFAULT_ZONE,
          properties.compute.region:label=COMPUTE_DEFAULT_REGION)
      """
        break
    parser.display_info.AddFormat(table_format)

  def Run(self, args):
    configs = named_configs.ConfigurationStore.AllConfigs()
    for _, config in sorted(six.iteritems(configs)):
      props = properties.VALUES.AllValues(
          list_unset=True,
          properties_file=properties_file.PropertiesFile([config.file_path]),
          only_file_contents=True)
      yield {
          'name': config.name,
          'is_active': config.is_active,
          'properties': props,
      }
