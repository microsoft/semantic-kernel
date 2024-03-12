# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Genomics resource filter expression rewrite backend."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re
from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.util import times
import six


def _RewriteTimeTerm(key, op, operand):
  """Rewrites <createTime op operand>."""
  if op not in ['<', '<=', '=', ':', '>=', '>']:
    return None
  try:
    dt = times.ParseDateTime(operand)
  except ValueError as e:
    raise ValueError(
        '{operand}: date-time value expected for {key}: {error}'
        .format(operand=operand, key=key, error=six.text_type(e)))

  if op == ':':
    op = '='

  return '{key} {op} "{dt}"'.format(
      key=key, op=op, dt=times.FormatDateTime(dt, tzinfo=times.UTC))


class OperationsBackend(resource_expr_rewrite.Backend):
  """Limit filter expressions to those supported by the Genomics backend."""

  _FORMAT = '{key} {op} {operand}'
  _QUOTED_FORMAT = '{key} {op} "{operand}"'

  _TERMS = {
      r'^done$': _FORMAT,
      r'^error.code$': _FORMAT,
      r'^metadata.labels\.(.*)': _QUOTED_FORMAT,
      r'^metadata.events$': _QUOTED_FORMAT,
  }

  _CREATE_TIME_TERMS = [
      r'^metadata.create_time$',
      r'^metadata.createTime$',
  ]

  def RewriteTerm(self, key, op, operand, key_type):
    """Limit <key op operand> terms to expressions supported by the backend."""
    for regex in self._CREATE_TIME_TERMS:
      if re.match(regex, key):
        return _RewriteTimeTerm(key, op, operand)

    for regex, fmt in six.iteritems(self._TERMS):
      if re.match(regex, key):
        return fmt.format(key=key, op=op, operand=operand)
    return None
