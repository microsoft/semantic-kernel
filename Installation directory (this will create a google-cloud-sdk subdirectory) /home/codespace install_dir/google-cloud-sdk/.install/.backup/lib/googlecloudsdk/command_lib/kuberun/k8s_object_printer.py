# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Kubernetes object-specific base printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.kuberun import kubernetesobject
from googlecloudsdk.command_lib.kuberun import kubernetes_consts
from googlecloudsdk.core.console import console_attr


def OrderByKey(map_):
  for k in sorted(map_):
    yield k, map_[k]


def FormatReadyMessage(record):
  if record.ready_condition and record.ready_condition.message:
    symbol, color = record.ReadySymbolAndColor()
    return console_attr.GetConsoleAttr().Colorize(
        textwrap.fill('{} {}'.format(symbol, record.ready_condition.message),
                      100), color)
  else:
    return ''


def FormatLastUpdated(record):
  modifier = record.last_modifier or '?'
  last_transition_time = '?'
  for condition in record.status.conditions:
    if condition.type == kubernetes_consts.VAL_READY and condition.lastTransitionTime:
      last_transition_time = condition.lastTransitionTime
  return 'Last updated on {} by {}'.format(last_transition_time, modifier)


def FormatLabels(labels):
  """Returns a human readable description of user provided labels if any."""
  if not labels:
    return ''
  return ' '.join(
      sorted([
          '{}:{}'.format(k, v)
          for k, v in labels.items()
          if not k.startswith(kubernetesobject.INTERNAL_GROUPS)
      ]))


def FormatHeader(record):
  con = console_attr.GetConsoleAttr()
  status = con.Colorize(*record.ReadySymbolAndColor())
  place = 'namespace ' + record.namespace
  return con.Emphasize('{} {} {} in {}'.format(status, record.Kind(),
                                               record.name, place))


def ReadyConditionFromDict(record):
  ready_cond = [
      x for x in record.get(kubernetes_consts.FIELD_STATUS, {}).get(
          kubernetes_consts.FIELD_CONDITIONS, [])
      if x[kubernetes_consts.FIELD_TYPE] == kubernetes_consts.VAL_READY
  ]
  if ready_cond:
    return ready_cond[0]
  else:
    return None
