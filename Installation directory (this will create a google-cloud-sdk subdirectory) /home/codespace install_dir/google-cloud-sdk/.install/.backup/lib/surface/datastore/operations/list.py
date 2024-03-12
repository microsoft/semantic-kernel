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
"""The gcloud datastore operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastore import operations
from googlecloudsdk.api_lib.datastore import rewrite_backend
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projection_spec


class List(base.ListCommand):
  """List pending Cloud Datastore admin operations and their status.

  Filters are case-sensitive and have the following syntax:

    field = value [AND [field = value]] ...

  where `field` is one of `kind`, `namespace`, `type`, or `labels.[KEY]`, and
  `[KEY]` is a label key. `kind` and `namespace` may be `*` to query for
  operations on all kinds and/or all namespaces. `type` may be one of
  `export_entities` or `import_entities`.

  Only the logical `AND` operator is
  supported; space-separated items are treated as having an implicit `AND`
  operator.

  ## EXAMPLES

  To see the list of all operations, run:

    $ {command}

  To see the list of all export operations, run:

    $ {command} --filter='type:export_entities'

  To see the list of all export operations for kind 'MyKind', run:

    $ {command} --filter='type:export_entities AND kind:MyKind'

  To see the list of all operations with particular labels, run:

    $ {command} --filter='labels.run = daily'
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.PAGE_SIZE_FLAG.SetDefault(parser, operations.DEFAULT_PAGE_SIZE)
    base.LIMIT_FLAG.SetDefault(parser, operations.DEFAULT_PAGE_SIZE)

  def Run(self, args):
    frontend_filter, backend_filter = self._ConvertFilter(args.filter, args)
    # Override existing filter with frontend filter.
    args.filter = frontend_filter
    return operations.ListOperations(
        project=properties.VALUES.core.project.Get(required=True),
        limit=args.limit,
        operation_filter=backend_filter)

  def _ConvertFilter(self, expression, args):
    """Translates user-provided filter spec into one our backend understands.

    Args:
      expression: a filter spec to translate
      args: the args namespace object
    Returns:
      A tuple of string filter specs. The first is the frontend spec for post
      filtering, the second is a spec that the Datastore Admin API understands.
    """
    operation_rewrite_backend = rewrite_backend.OperationsRewriteBackend()
    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    return operation_rewrite_backend.Rewrite(expression, defaults=defaults)
