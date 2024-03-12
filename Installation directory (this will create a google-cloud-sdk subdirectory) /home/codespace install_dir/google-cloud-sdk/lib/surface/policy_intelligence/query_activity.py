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
"""Command to query activities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.policy_intelligence import policy_analyzer
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

_DETAILED_HELP = {
    'brief':
        """Query activities on cloud resource.
        """,
    'DESCRIPTION':
        """\
     Query activities with certain types of specific container resource. For --activity-type, supported values are:
     - serviceAccountLastAuthentication
     - serviceAccountKeyLastAuthentication
        """,
    'EXAMPLES':
        """\
    To query serviceAccountKeyLastAuthentication activities of a project, run:

    $ {command} --activity-type=serviceAccountKeyLastAuthentication --project=project-id

    To query serviceAccountLastAuthentication activities of a project with no limit, run:

    $ {command} --activity-type=serviceAccountLastAuthentication --project=project-id --limit=unlimited

    To query serviceAccountLastAuthentication with filtering on certain service account, run:

    $ {command} --activity-type=serviceAccountLastAuthentication --project=project-id --query-filter='activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name@project-id.iam.gserviceaccount.com"'

    To query serviceAccountLastAuthentication with filtering on multiple service accounts, run:

    $ {command} --activity-type=serviceAccountLastAuthentication --project=project-id --query-filter='activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-1@project-id.iam.gserviceaccount.com" OR activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-2@project-id.iam.gserviceaccount.com" OR activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-3@project-id.iam.gserviceaccount.com"'
        """
}

_DETAILED_HELP_ALPHA = {
    'brief':
        """Query activities on cloud resource.
        """,
    'DESCRIPTION':
        """\
     Query activities with certain types of specific container resource. For --activity-type, supported values are:
     - serviceAccountLastAuthentication
     - serviceAccountKeyLastAuthentication
     - dailyAuthorization
        """,
    'EXAMPLES':
        """\
    To query serviceAccountKeyLastAuthentication activities of a project, run:

    $ {command} --activity-type=serviceAccountKeyLastAuthentication --project=project-id

    To query serviceAccountLastAuthentication activities of a project with no limit, run:

    $ {command} --activity-type=serviceAccountLastAuthentication --project=project-id --limit=unlimited

    To query serviceAccountLastAuthentication with filtering on certain service account, run:

    $ {command} --activity-type=serviceAccountLastAuthentication --project=project-id --query-filter='activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name@project-id.iam.gserviceaccount.com"'

    To query serviceAccountLastAuthentication with filtering on multiple service accounts, run:

    $ {command} --activity-type=serviceAccountLastAuthentication --project=project-id --query-filter='activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-1@project-id.iam.gserviceaccount.com" OR activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-2@project-id.iam.gserviceaccount.com" OR activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-3@project-id.iam.gserviceaccount.com"'

    To query dailyAuthorization activities of a project, run:

    $ {command} --activity-type=dailyAuthorization --project=project-id

    To query dailyAuthorization of a project with filtering on certain resource, permission, principal and date, run:

    $ {command} --activity-type=dailyAuthorization --project=project-id --query-filter='activities.activity.full_resource_name="<full_resource_name>" AND activities.activity.permission="<permission_name>" AND activities.activity.principal="<principal_email>" AND activities.activity.date="<YYYY-MM-DD>"'
    """
}


def _Args(parser):
  """Parses arguments for the commands."""
  parser.add_argument(
      '--activity-type',
      required=True,
      type=str,
      choices=[
          'serviceAccountLastAuthentication',
          'serviceAccountKeyLastAuthentication'
      ],
      help="""Type of the activities.
      """)
  parser.add_mutually_exclusive_group(required=True).add_argument(
      '--project',
      type=str,
      help="""The project ID or number to query the activities.
      """)
  parser.add_argument(
      '--query-filter',
      type=str,
      default='',
      help='Filter on activities, separated by "OR" if multiple filters are specified. At most 10 filter restrictions are supported in the query-filter. e.g. --query-filter=\'activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-1@project-id.iam.gserviceaccount.com" OR activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-2@project-id.iam.gserviceaccount.com"\''
  )
  parser.add_argument(
      '--limit',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      default=1000,
      help='Max number of query result. Default to be 1000 and max to be unlimited, i.e., --limit=unlimited.'
  )
  parser.add_argument(
      '--page-size',
      type=arg_parsers.BoundedInt(1, 1000),
      default=500,
      help='Max page size for each http response. Default to be 500 and max to be 1000.'
  )


def _ArgsAlpha(parser):
  """Parses arguments for the commands."""
  parser.add_argument(
      '--activity-type',
      required=True,
      type=str,
      choices=[
          'serviceAccountLastAuthentication',
          'serviceAccountKeyLastAuthentication', 'dailyAuthorization'
      ],
      help="""Type of the activities.
      """)
  parser.add_mutually_exclusive_group(required=True).add_argument(
      '--project',
      type=str,
      help="""The project ID or number to query the activities.
      """)
  parser.add_argument(
      '--query-filter',
      type=str,
      default='',
      help="""Filter on activities. \n
      For last authentication activities, this field is separated by "OR" if multiple filters are specified. At most 10 filter restrictions are supported in the query-filter. \n
        e.g. --query-filter=\'activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-1@project-id.iam.gserviceaccount.com" OR activities.full_resource_name="//iam.googleapis.com/projects/project-id/serviceAccounts/service-account-name-2@project-id.iam.gserviceaccount.com"\'\n
      For daily authorization activities, this field is separated by "OR" and "AND". At most 10 filter restrictions per layer and at most 2 layers are supported in the query-filter. \n
        e.g. --query-filter=\'activities.activity.date="2022-01-01" AND activities.activity.permission="spanner.databases.list" AND (activities.activity.principal="principal_1@your-organization.com" OR activities.activity.principal="principal_2@your-organization.com")'"""
  )
  parser.add_argument(
      '--limit',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      default=1000,
      help='Max number of query result. Default to be 1000 and max to be unlimited, i.e., --limit=unlimited.'
  )
  parser.add_argument(
      '--page-size',
      type=arg_parsers.BoundedInt(1, 1000),
      default=500,
      help='Max page size for each http response. Default to be 500 and max to be 1000.'
  )


def _Run(args):
  policy_analyzer_client, messages = policy_analyzer.GetClientAndMessages()
  query_activity_parent = 'projects/{0}/locations/global/activityTypes/{1}'.format(
      args.project, args.activity_type)
  query_activity_request = messages.PolicyanalyzerProjectsLocationsActivityTypesActivitiesQueryRequest(
      parent=query_activity_parent, filter=args.query_filter)
  policy_analyzer_service = policy_analyzer_client.ProjectsLocationsActivityTypesActivitiesService(
      policy_analyzer_client)
  return list_pager.YieldFromList(
      policy_analyzer_service,
      query_activity_request,
      method='Query',
      batch_size=args.page_size,
      field='activities',
      limit=args.limit,
      batch_size_attribute='pageSize')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Hidden
class QueryActivityAlpha(base.Command):
  """Query activities on cloud resource."""

  detailed_help = _DETAILED_HELP_ALPHA

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _ArgsAlpha(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
@base.Hidden
class QueryActivityBeta(base.Command):
  """Query activities on cloud resource."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _Args(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class QueryActivityGA(base.Command):
  """Query activities on cloud resource."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Parses arguments for the commands."""
    _Args(parser)

  def Run(self, args):
    return _Run(args)
