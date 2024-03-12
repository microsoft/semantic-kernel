# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Cloud resource filter expression scrubber backend.

A scrubbed expression has all operands replaced by X.

To scrub filter_expression_string:

  scrubber = resource_filter_scrub.Backend()
  _, scrubbed_expression_string = scrubber.Rewrite(filter_expression_string)
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_expr_rewrite


class Backend(resource_expr_rewrite.Backend):
  """Cloud resource filter expression scrubber backend."""

  def RewriteOperand(self, operand):
    """Rewrites any operand by scrubbing it down to X."""
    return 'X'

  def RewriteGlobal(self, call):
    """Rewrites any global restriction by scrubbing it down to X."""
    return 'X'
