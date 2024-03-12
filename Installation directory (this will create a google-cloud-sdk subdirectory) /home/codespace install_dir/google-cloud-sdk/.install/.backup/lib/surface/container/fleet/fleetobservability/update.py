# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""The command to update Fleet Observability Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container.fleet.features import base

_UPDATE_LOGGING_CONFIG_HELPF_TEXT = """\
  Path of the YAML(or JSON) file that contains the logging configurations.

  The JSON file is formatted as follows, with camelCase field naming:

  ```
  {
      "loggingConfig": {
          "defaultConfig": {
              "mode": "COPY"
          },
          "fleetScopeLogsConfig": {
              "mode": "MOVE"
          }
      }
  }
  ```

  The YAML file is formatted as follows, with camelCase field naming:

  ```
  ---
  loggingConfig:
    defaultConfig:
      mode: COPY
    fleetScopeLogsConfig:
      mode: MOVE
  ```
"""


class Update(base.UpdateCommand):
  """Updates the Fleet Observability Feature resource.

  This command updates the Fleet Observability Feature in a fleet.

  ## EXAMPLES

  To describe the Fleet Observability Feature, run:

    $ {command} --logging-config=LOGGING-CONFIG
  """

  feature_name = 'fleetobservability'

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--logging-config',
        type=arg_parsers.YAMLFileContents(),
        help=_UPDATE_LOGGING_CONFIG_HELPF_TEXT,
    )

  def Run(self, args):
    file_content = args.logging_config
    if 'loggingConfig' not in file_content:
      raise exceptions.InvalidArgumentException(
          '--logging-config',
          'Missing field [loggingConfig] in logging configuration file')
    logging_config_from_file = file_content.get('loggingConfig', None)

    try:
      logging_config = messages_util.DictToMessageWithErrorCheck(
          logging_config_from_file,
          self.messages.FleetObservabilityLoggingConfig)
    except (messages_util.DecodeError, AttributeError, KeyError) as err:
      raise exceptions.InvalidArgumentException(
          '--logging-config',
          "'{}'".format(err.args[0] if err.args else err))
    f = self.messages.Feature(
        spec=self.messages.CommonFeatureSpec(
            fleetobservability=self.messages.FleetObservabilityFeatureSpec(
                loggingConfig=logging_config,
            )))
    self.Update(['spec.fleetobservability.logging_config'], f)
