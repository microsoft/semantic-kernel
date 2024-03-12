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
"""Utils for Network Actions commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.network_actions import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers


messages = apis.GetMessagesModule('networkservices', 'v1alpha1')
LOG_LEVEL_VALUES = (
    messages.WasmPluginLogConfig.MinLogLevelValueValuesEnum.to_dict().keys()
)


def SetLocationAsGlobal():
  """Set default location to global."""
  return 'global'


class LogConfig(arg_parsers.ArgDict):

  def __init__(self):
    super(LogConfig, self).__init__(
        spec={
            'enable': arg_parsers.ArgBoolean(),
            'sample-rate': arg_parsers.BoundedFloat(0.0, 1.0),
            'min-log-level': _GetLogLevelValidator(),
        },
        required_keys=['enable'],
    )


def _GetLogLevelValidator():
  return arg_parsers.CustomFunctionValidator(
      lambda k: k in LOG_LEVEL_VALUES,
      'Only the following keys are valid for log level: [{}].'.format(
          ', '.join(LOG_LEVEL_VALUES)
      ),
      lambda x: x.upper(),
  )


def GetLogConfig(parsed_dict):
  log_config_dict = {
      _ConvertToCamelCase(key): parsed_dict[key]
      for key, value in parsed_dict.items()
  }
  return encoding.DictToMessage(log_config_dict, messages.WasmPluginLogConfig)


def _ConvertToCamelCase(name):
  """Converts kebab-case name to camelCase."""
  part = name.split('-')
  return part[0] + ''.join(x.title() for x in part[1:])


def GetApiVersion(track):
  if track in util.API_VERSION_FOR_TRACK:
    return util.API_VERSION_FOR_TRACK[track]
  else:
    raise ValueError('Unsupported Release Track: {}'.format(track))
