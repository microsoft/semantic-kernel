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

"""Factory for AutotuningConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.generated_clients.apis.dataproc.v1.dataproc_v1_messages import AutotuningConfig as ac


class AutotuningConfigFactory(object):
  """Factory for AutotuningConfig message.

  Add arguments related to AutotuningConfig to argument parser and create
  AutotuningConfig message from parsed arguments.
  """

  def __init__(self, dataproc):
    """Factory for AutotuningConfig message.

    Args:
      dataproc: An api_lib.dataproc.Dataproc instance.
    """
    self.dataproc = dataproc

  def GetMessage(self, args):
    """Builds an AutotuningConfig message instance.

    Args:
      args: Parsed arguments.

    Returns:
      AutotuningConfig: An AutotuningConfig message instance. Returns
      none if all fields are None.
    """
    kwargs = {}

    if args.autotuning_scenarios:
      kwargs['scenarios'] = [
          arg_utils.ChoiceToEnum(sc, ac.ScenariosValueListEntryValuesEnum)
          for sc in args.autotuning_scenarios
      ]

    if not kwargs:
      return None

    return self.dataproc.messages.AutotuningConfig(**kwargs)


def AddArguments(parser):
  """Adds related arguments to parser."""
  scenario_choices = [
      arg_utils.EnumNameToChoice(str(sc))
      for sc in ac.ScenariosValueListEntryValuesEnum
      if sc != ac.ScenariosValueListEntryValuesEnum.SCENARIO_UNSPECIFIED
  ]

  parser.add_argument(
      '--autotuning-scenarios',
      type=arg_parsers.ArgList(
          element_type=str,
          choices=scenario_choices,
      ),
      metavar='SCENARIO',
      default=[],
      help='Scenarios for which tunings are applied.',
      hidden=True,
  )
