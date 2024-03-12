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

"""The Cloud Resource Search lister."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_expr_rewrite


class Error(exceptions.Error):
  """Base exception for this module."""


class CollectionNotIndexed(Error):
  """The collection is not indexed."""


class QueryOperatorNotSupported(Error):
  """An operator in a query is not supported."""


PAGE_SIZE = 500

# TODO(b/38192518): Move this to the resource parser yaml config.
# The Cloud Resource Search type dict indexed by Cloud SDK collection.
# The cloudresourcesearch API does not allow dotted resource type names, so
# the flat namespace will get crowded and unwieldy as it grows. For example,
# how many APIs have an "instance" resource? Sorry, "Instance" already snapped
# up by compute.  Instead we map the well-defined hierarchical Cloud SDK
# collection names onto the supported resource types.
RESOURCE_TYPES = {
    'cloudresourcemanager.projects': 'Project',
    'compute.disks': 'Disk',
    'compute.healthChecks': 'HealthCheck',
    'compute.httpHealthChecks': 'HttpHealthCheck',
    'compute.httpsHealthChecks': 'HttpsHealthCheck',
    'compute.images': 'Image',
    'compute.instanceGroups': 'InstanceTemplate',
    'compute.instances': 'Instance',
    'compute.subnetworks': 'Subnetwork',
}

CLOUD_RESOURCE_SEARCH_COLLECTION = 'resources'


class QueryRewriter(resource_expr_rewrite.Backend):
  """Resource filter expression rewriter."""

  def RewriteGlobal(self, call):
    """Rewrites global restriction in call.

    Args:
      call: A list of resource_lex._TransformCall objects. In this case the list
        has one element that is a global restriction with a global_restriction
        property that is the restriction substring to match.

    Returns:
      The global restriction rewrite which is simply the global_restriction
      string.
    """
    return call.global_restriction

  def RewriteTerm(self, key, op, operand, key_type):
    """Rewrites <key op operand>."""

    del key_type  # unused in RewriteTerm
    if op in ('~',):
      raise QueryOperatorNotSupported(
          'The [{}] operator is not supported in cloud resource search '
          'queries.'.format(op))

    # The query API does not support name:(value1 ... valueN), but it does
    # support OR, so we split multiple operands into separate name:valueI
    # expressions joined by OR.
    values = operand if isinstance(operand, list) else [operand]

    if key == 'project':
      # The query API does not have a 'project' attribute, but It does have
      # 'selfLink'. The rewrite provides 'project' and massages the query to
      # operate on 'selfLink'. The resource parser would be perfection here,
      # but a bit heavweight. We'll stick with this shortcut until proven wrong.
      key = 'selfLink'
      values = ['/projects/{}/'.format(value) for value in values]
    elif key == '@type':
      # Cloud SDK maps @type:collection => @type:resource-type. This isolates
      # the user from yet another esoteric namespace.
      collections = values
      values = []
      for collection in collections:
        if collection.startswith(CLOUD_RESOURCE_SEARCH_COLLECTION + '.'):
          values.append(collection[len(CLOUD_RESOURCE_SEARCH_COLLECTION) + 1:])
        else:
          try:
            values.append(RESOURCE_TYPES[collection])
          except KeyError:
            raise CollectionNotIndexed(
                'Collection [{}] not indexed for search.'.format(collection))

    parts = ['{key}{op}{value}'.format(key=key, op=op, value=self.Quote(value))
             for value in values]
    expr = ' OR '.join(parts)
    if len(parts) > 1:
      # This eliminates AND/OR precedence ambiguity.
      expr = '( ' + expr + ' )'
    return expr


def List(limit=None, page_size=None, query=None, sort_by=None, uri=False):
  """Yields the list of Cloud Resources for collection.

  Not all collections are indexed for search.

  Args:
    limit: The max number of resources to return. None for unlimited.
    page_size: The max number of resources per response page. The defsult is
      PAGE_SIE.
    query: A resource filter expression. Use @type:collection to filter
      resources by collection. Use the resources._RESOURCE_TYPE_ collection to
      specify CloudResourceSearch resource types. By default all indexed
      resources are in play.
    sort_by: A list of field names to sort by. Prefix a name with ~ to reverse
      the sort for that name.
    uri: Return the resource URI if true.

  Raises:
    CollectionNotIndexed: If the collection is not indexed for search.
    QueryOperatorNotSupported: If the query contains an unsupported operator.
    HttpError: request/response errors.

  Yields:
    The list of Cloud Resources for collection.
  """
  _, remote_query = QueryRewriter().Rewrite(query)
  log.info('Resource search query="%s" remote_query="%s"', query, remote_query)
  if page_size is None:
    page_size = PAGE_SIZE
  if sort_by:
    order_by = ','.join([name[1:] + ' desc' if name.startswith('~') else name
                         for name in sort_by])
  else:
    order_by = None

  client = apis.GetClientInstance('cloudresourcesearch', 'v1')

  for result in list_pager.YieldFromList(
      service=client.ResourcesService(client),
      method='Search',
      request=client.MESSAGES_MODULE.CloudresourcesearchResourcesSearchRequest(
          orderBy=order_by,
          query=remote_query,
      ),
      field='results',
      limit=limit,
      batch_size=page_size,
      batch_size_attribute='pageSize'):
    yield result.resourceUrl if uri else result.resource
