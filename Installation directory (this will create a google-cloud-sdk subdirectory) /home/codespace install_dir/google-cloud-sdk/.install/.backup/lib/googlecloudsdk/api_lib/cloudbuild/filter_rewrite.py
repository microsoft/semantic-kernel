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

"""Cloud Build resource filter expression rewrite backend."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.resource import resource_expr_rewrite
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import times
import six


# If _STRING_FIELDS and _TIME_FIELDS are out of sync with the API then --filter
# expressions will still work, but parts may be done client side, degrading
# performance.

_STRING_FIELDS = {
    'build_id',
    'images',
    'options.requested_verify_option',
    'project_id',
    'results.images.digest',
    'results.images.name',
    'source_provenance.resolved_repo_source.commit_sha',
    'source.repo_source.branch_name',
    'source.repo_source.commit_sha',
    'source.repo_source.repo_name',
    'source.repo_source.tag_name',
    'source.storage_source.bucket',
    'source.storage_source.object',
    'status',
    'tags',
    'trigger_id',
}

_TIME_FIELDS = {
    'create_time',
    'finish_time',
    'start_time',
}


class Backend(resource_expr_rewrite.Backend):
  """Cloud Build resource filter expression rewrite backend."""

  def __init__(self, ongoing=False, **kwargs):
    super(Backend, self).__init__(**kwargs)
    self._ongoing = ongoing

  def _RewriteStrings(self, key, op, operand):
    """Rewrites <key op operand>."""
    terms = []
    for arg in operand if isinstance(operand, list) else [operand]:
      terms.append('{key}{op}{arg}'.format(key=key, op=op,
                                           arg=self.Quote(arg, always=True)))
    if len(terms) > 1:
      return '{terms}'.format(terms=' OR '.join(terms))
    return terms[0]

  def _RewriteTimes(self, key, op, operand):
    """Rewrites <*Time op operand>."""
    try:
      dt = times.ParseDateTime(operand)
    except ValueError as e:
      raise ValueError(
          '{operand}: date-time value expected for {key}: {error}'
          .format(operand=operand, key=key, error=six.text_type(e)))
    dt_string = times.FormatDateTime(dt, '%Y-%m-%dT%H:%M:%S.%3f%Ez', times.UTC)
    return '{key}{op}{dt_string}'.format(
        key=key, op=op, dt_string=self.Quote(dt_string, always=True))

  def Rewrite(self, expression, **kwargs):
    client_expression, server_expression = super(Backend, self).Rewrite(
        expression, **kwargs)
    if self._ongoing:
      ongoing = 'status="WORKING" OR status="QUEUED"'
      if server_expression:
        server_expression = self.RewriteAND(server_expression, ongoing)
      else:
        server_expression = ongoing
    return client_expression, server_expression

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""
    del key_type  # unused in RewriteTerm
    if op == ':':
      op = '='
    elif op not in ['<', '<=', '=', '!=', '>=', '>']:
      return None
    name = resource_property.ConvertToSnakeCase(key)
    if name in _STRING_FIELDS:
      return self._RewriteStrings(name, op, operand)
    elif name in _TIME_FIELDS:
      return self._RewriteTimes(name, op, operand)
    return None
