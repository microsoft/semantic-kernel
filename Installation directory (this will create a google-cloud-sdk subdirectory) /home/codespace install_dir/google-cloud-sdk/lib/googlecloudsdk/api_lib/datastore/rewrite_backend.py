# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Backend rewrite tool for Cloud Datastore operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.datastore import constants
from googlecloudsdk.core.resource import resource_expr_rewrite
import six


class OperationsRewriteBackend(resource_expr_rewrite.Backend):
  """Rewrites for Cloud Datastore server side filter expressions."""

  _KEY_MAPPING = {
      r'^label\.(.*)': r'metadata.common.labels.\1',
      r'^labels\.(.*)': r'metadata.common.labels.\1',
      '^namespace$': 'metadata.entity_filter.namespace_id',
      '^namespaceId$': 'metadata.entity_filter.namespace_id',
      '^type$': 'metadata.common.operation_type',
      '^operationType$': 'metadata.common.operation_type',
      '^kind$': 'metadata.entity_filter.kind',
  }

  _OPERATOR_MAPPING = {
      # Datastore admin backends only supports EQ, not HAS
      ':': '='
  }

  _KEY_OPERAND_MAPPING = {
      'metadata.entity_filter.namespace_id': {
          constants.DEFAULT_NAMESPACE: '',
      },
  }

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites a <key op operand> term of a filter expression.

    Args:
      key: The key, a string.
      op: The op, a string.
      operand: The operand, a string or list of strings.
      key_type: The key type, unknown if None.

    Returns:
      the new term, as a string.
    """
    key = self._RewriteKey(key)
    op = self._RewriteOp(op)
    operand = self._RewriteOperand(key, operand)
    return super(OperationsRewriteBackend, self).RewriteTerm(
        key, op, operand, key_type)

  def Quote(self, value, always=False):
    """Returns value or value "..." quoted with C-style escapes if needed.

    Defers to BackendBase.Quote for everything but the empty string, which it
    force quotes.

    Args:
      value: The string value to quote if needed.
      always: Always quote non-numeric value if True.

    Returns:
      A string: value or value "..." quoted with C-style escapes if needed or
      requested.
    """
    # The Cloud Datastore backend does not handle missing values. Always
    # require quoting for the empty string.
    always = always or not value
    return super(OperationsRewriteBackend, self).Quote(value, always=always)

  def _RewriteOperand(self, key, operand):
    if isinstance(operand, list):
      return [
          self._RewriteOperand(key, operand_item) for operand_item in operand
      ]
    return self._KEY_OPERAND_MAPPING.get(key, {}).get(operand, operand)

  def _RewriteKey(self, key):
    for regex, replacement in six.iteritems(self._KEY_MAPPING):
      if re.match(regex, key):
        return re.sub(regex, replacement, key)
    return key

  def _RewriteOp(self, op):
    return self._OPERATOR_MAPPING.get(op, op)
