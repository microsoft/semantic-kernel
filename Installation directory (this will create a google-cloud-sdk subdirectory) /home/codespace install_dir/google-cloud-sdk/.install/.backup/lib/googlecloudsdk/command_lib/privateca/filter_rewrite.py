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
"""Helpers for list filter parameter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_expr_rewrite


# TODO(b/169417671) Support client side filtering along server side filtering.
class BackendFilterRewrite(resource_expr_rewrite.Backend):
  """Limit filter expressions to those supported by the PrivateCA API backend."""

  def RewriteOperand(self, operand):
    """Always quote the operand as the Cloud Filter Library won't be able to parse as values all arbitrary strings."""
    return self.QuoteOperand(operand, always=True)
