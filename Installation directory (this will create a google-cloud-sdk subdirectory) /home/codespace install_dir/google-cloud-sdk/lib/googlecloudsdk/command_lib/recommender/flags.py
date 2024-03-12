# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""parsing flags for Recommender APIs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import base
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.util.args import common_args


def AddParentFlagsToParser(parser):
  """Adding argument mutex group project, billing-account, folder, organization to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
  """
  resource_group = parser.add_mutually_exclusive_group(
      required=True,
      help='Resource that is associated with cloud entity type. Currently four mutually exclusive flags are supported, --project, --billing-account, --folder, --organization.'
  )
  common_args.ProjectArgument(
      help_text_to_overwrite='The Google Cloud Platform project ID.'
  ).AddToParser(resource_group)
  resource_group.add_argument(
      '--billing-account',
      metavar='BILLING_ACCOUNT',
      help='The Google Cloud Platform billing account ID to use for this invocation.'
  )
  resource_group.add_argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      help='The Google Cloud Platform organization ID to use for this invocation.'
  )
  resource_group.add_argument(
      '--folder',
      metavar='FOLDER_ID',
      help='The Google Cloud Platform folder ID to use for this invocation.')


def AddEntityFlagsToParser(parser, entities):
  """Adds argument mutex group of specified entities to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      entities: The entities to add.
  """
  resource_group = parser.add_mutually_exclusive_group(
      required=True, help='Resource that is associated with cloud entity type.')
  if base.EntityType.ORGANIZATION in entities:
    resource_group.add_argument(
        '--organization',
        metavar='ORGANIZATION_ID',
        help='The Google Cloud organization ID to use for this invocation.')
  if base.EntityType.FOLDER in entities:
    resource_group.add_argument(
        '--folder',
        metavar='FOLDER_ID',
        help='The Google Cloud folder ID to use for this invocation.')
  if base.EntityType.BILLING_ACCOUNT in entities:
    resource_group.add_argument(
        '--billing-account',
        metavar='BILLING_ACCOUNT',
        help='The Google Cloud billing account ID to use for this invocation.')
  if base.EntityType.PROJECT in entities:
    common_args.ProjectArgument(
        help_text_to_overwrite='The Google Cloud project ID.').AddToParser(
            resource_group)


def AddInsightTypeFlagsToParser(parser, entities):
  """Adds argument mutex group of specified entities and insight type to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      entities: The entities to add.
  """
  AddEntityFlagsToParser(parser, entities)
  parser.add_argument(
      '--location',
      metavar='LOCATION',
      required=True,
      help='Location to use for this invocation.')
  parser.add_argument(
      'insight_type',
      metavar='INSIGHT_TYPE',
      help='Insight type to use for this invocation.')


def AddRecommenderFlagsToParser(parser, entities):
  """Adds argument mutex group of specified entities and recommender to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      entities: The entities to add.
  """
  AddEntityFlagsToParser(parser, entities)
  parser.add_argument(
      '--location',
      metavar='LOCATION',
      required=True,
      help='Location to use for this invocation.')
  parser.add_argument(
      'recommender',
      metavar='RECOMMENDER',
      help='Recommender to use for this invocation.')


def AddConfigFileToParser(parser, resource):
  """Adds config file to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      resource: The resource to add to.
  """
  parser.add_argument(
      '--config-file',
      help='Generation configuration file for the {}.'.format(resource))


def AddDisplayNameToParser(parser, resource):
  """Adds display-name to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      resource: The resource to add to.
  """
  parser.add_argument(
      '--display-name', help='Display name of the {}.'.format(resource))


def AddValidateOnlyToParser(parser):
  """Adds validate-only to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
  """
  parser.add_argument(
      '--validate-only',
      action='store_true',
      default=False,
      help='If true, validate the request and preview the change, but do not actually update it.'
  )


def AddEtagToParser(parser, resource):
  """Adds etag to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      resource: The resource to add to.
  """
  parser.add_argument(
      '--etag', required=True, help='Etag of the {}.'.format(resource))


def AddAnnotationsToParser(parser, resource):
  """Adds annotations to parser.

  Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
      resource: The resource to add to.
  """
  parser.add_argument(
      '--annotations',
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      help='Store small amounts of arbitrary data on the {}.'
      .format(resource),
      metavar='KEY=VALUE',
      action=arg_parsers.StoreOnceAction)


def GetResourceSegment(args):
  """Returns the resource from up to the cloud entity."""
  if hasattr(args, 'project') and args.project:
    return 'projects/%s' % args.project
  elif hasattr(args, 'folder') and args.folder:
    return 'folders/%s' % args.folder
  elif hasattr(args, 'billing_account') and args.billing_account:
    return 'billingAccounts/%s' % args.billing_account
  else:
    return 'organizations/%s' % args.organization


def GetLocationSegment(args):
  """Returns the resource name up to the location."""
  parent = GetResourceSegment(args)
  return '{}/locations/{}'.format(parent, args.location)


def GetInsightTypeName(args):
  """Returns the resource name up to the insight type."""
  parent = GetLocationSegment(args)
  return '{}/insightTypes/{}'.format(parent, args.insight_type)


def GetFullInsightTypeName(args, insight_type):
  """Returns the resource name up to the insight type."""
  parent = GetLocationSegment(args)
  return '{}/insightTypes/{}'.format(parent, insight_type)


def GetInsightTypeConfigName(args):
  """Returns the resource name for the insight type config."""
  return GetInsightTypeName(args) + '/config'


def GetInsightName(args):
  """Returns the resource name for the insight."""
  return GetInsightTypeName(args) + '/insights/{0}'.format(args.INSIGHT)


def GetRecommenderName(args):
  """Returns the resource name up to the recommender."""
  parent = GetLocationSegment(args)
  return '{}/recommenders/{}'.format(parent, args.recommender)


def GetFullRecommenderName(args, recommender):
  """Returns the resource name up to the recommender."""
  return '{}/recommenders/{}'.format(GetLocationSegment(args), recommender)


def GetRecommenderConfigName(args):
  """Returns the resource name for the recommender config."""
  return GetRecommenderName(args) + '/config'


def GetRecommendationName(args):
  """Returns the resource name for the insight."""
  return GetRecommenderName(args) + '/recommendations/{0}'.format(
      args.RECOMMENDATION)


def GetConfigsParentFromFlags(args, is_insight_api):
  """Parsing args for url string for recommender and insigh type configs apis.

  Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.
      is_insight_api: whether this is an insight api.

  Returns:
      The full url string based on flags given by user.
  """
  url = 'projects/{0}'.format(args.project)
  url = url + '/locations/{0}'.format(args.location)

  if is_insight_api:
    url = url + '/insightTypes/{0}'.format(args.insight_type)
  else:
    url = url + '/recommenders/{0}'.format(args.recommender)
  return url + '/config'
