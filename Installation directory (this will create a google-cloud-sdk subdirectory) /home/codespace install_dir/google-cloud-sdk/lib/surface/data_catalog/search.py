# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""List command for gcloud debug logpoints command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_catalog import search

@base.ReleaseTracks(base.ReleaseTrack.GA)


class Search(base.Command):
  """Search Data Catalog for resources that match a query."""

  detailed_help = {
      'DESCRIPTION': """\
          Search Data Catalog for resources that match a query.
      """,
      'EXAMPLES': """\
          To search project 'my-project' for Data Catalog resources that
          match the simple predicate 'foo':

            $ {command} 'foo' --include-project-ids=my-project

          To search organization '1234' for Data Catalog resources that
          match entities whose names match the predicate 'foo':

            $ {command} 'name:foo' --include-organization-ids=1234
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'query',
        help="""\
            Query string in search query syntax in Data Catalog. For more
            information, see:
            https://cloud.google.com/data-catalog/docs/how-to/search-reference
        """)

    parser.add_argument(
        '--limit',
        type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
            Maximum number of resources to list. The default is *unlimited*.
        """)

    parser.add_argument(
        '--page-size',
        type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
            Some services group resource list output into pages. This flag specifies
            the maximum number of resources per page.
        """)

    parser.add_argument(
        '--order-by',
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
            Specifies the ordering of results. Defaults to 'relevance'.

            Currently supported case-sensitive choices are:

                *  relevance
                *  last_access_timestamp [asc|desc]: defaults to descending.
                *  last_modified_timestamp [asc|desc]: defaults to descending.

            To order by last modified timestamp ascending, specify:
            `--order-by="last_modified_timestamp desc"`.
        """)

    scope_group = parser.add_argument_group(
        'Scope. Control the scope of the search.',
        required=True)
    scope_group.add_argument(
        '--include-gcp-public-datasets',
        action='store_true',
        help="""\
            If True, include Google Cloud Platform public datasets in the search
            results.
        """)
    scope_group.add_argument(
        '--include-project-ids',
        type=arg_parsers.ArgList(),
        metavar='PROJECT',
        help="""\
            List of Cloud Project IDs to include in the search.
        """)
    scope_group.add_argument(
        '--include-organization-ids',
        type=arg_parsers.ArgList(),
        metavar='ORGANIZATION',
        help="""\
            List of Cloud Organization IDs to include in the search.
        """)
    scope_group.add_argument(
        '--restricted-locations',
        type=arg_parsers.ArgList(),
        metavar='LOCATION',
        help="""\
            List of locations to search within.
        """)

  def Run(self, args):
    """Run the search command."""
    version_label = 'v1'
    return search.Search(args, version_label)

@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)


class SearchBeta(Search):
  __doc__ = Search.__doc__

  def Run(self, args):
    """Run the search command."""
    version_label = 'v1beta1'
    return search.Search(args, version_label)
