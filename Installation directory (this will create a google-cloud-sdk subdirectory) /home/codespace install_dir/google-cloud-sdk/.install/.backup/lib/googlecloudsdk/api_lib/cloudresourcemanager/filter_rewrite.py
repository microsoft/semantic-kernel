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

"""Cloud resource manager resource filter expression rewriters.

Refer to the core.resource.resource_expr_rewrite docstring for expression
rewrite details.

To use in Run(args) methods:

  from googlecloudsdk.api_lib.cloudresourcemanager import filter_rewrite
    ...
  filter_expr = filter_rewrite.FooRewriter().Rewrite(args.filter)
    ...
  FooRequest(
    ...
    filter=filter_expr,
    ...
  )
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core.resource import resource_expr_rewrite


class ListRewriter(resource_expr_rewrite.Backend):
  """Project List request resource filter expression rewriter."""

  def Quote(self, value):
    """Returns value double quoted if it contains special characters."""
    return super(ListRewriter, self).Quote(
        value, always=re.search(r'[^-@.\w]', value))

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""

    del key_type  # unused in RewriteTerm
    if not key.startswith('labels.'):
      # Support OnePlatform aliases.
      key = key.lower()
      if key in ('createtime', 'create_time'):
        key = 'createTime'
      elif key in ('lifecyclestate', 'lifecycle_state'):
        key = 'lifecycleState'
      elif key in ('projectid', 'project_id'):
        key = 'id'
      elif key in ('projectname', 'project_name'):
        key = 'name'
      elif key in ('projectnumber', 'project_number'):
        key = 'projectNumber'
      elif key not in ('id', 'name', 'parent.id', 'parent.type'):
        return None

    if op not in (':', '=', '!='):
      return None

    # The query API does not support name:(value1 ... valueN), but it does
    # support OR, so we split multiple operands into separate name:value
    # expressions joined by OR.
    values = operand if isinstance(operand, list) else [operand]
    parts = []

    for value in values:
      if op == '!=':
        part = 'NOT ({key}{op}{operand})'.format(
            key=key, op='=', operand=self.Quote(value))

      else:
        part = '{key}{op}{operand}'.format(
            key=key, op=op, operand=self.Quote(value))
      parts.append(part)

    expr = ' OR '.join(parts)
    if len(parts) > 1:
      # This eliminates AND/OR precedence ambiguity.
      expr = '( ' + expr + ' )'
    return expr
