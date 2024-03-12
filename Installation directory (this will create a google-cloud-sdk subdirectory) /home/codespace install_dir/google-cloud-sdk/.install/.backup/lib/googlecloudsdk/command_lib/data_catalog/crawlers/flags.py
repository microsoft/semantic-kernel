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
"""Additional flags for data-catalog crawler commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base


def AddCrawlerScopeAndSchedulingFlagsForCreate():
  return AddCrawlerScopeAndSchedulingFlags()


def AddCrawlerScopeAndSchedulingFlagsForUpdate():
  return AddCrawlerScopeAndSchedulingFlags(for_update=True)


def AddCrawlerScopeAndSchedulingFlags(for_update=False):
  """Python hook to add the arguments for scope and scheduling options.

  Args:
    for_update: If flags are for update instead of create.

  Returns:
    List consisting of the scope and scheduling arg groups.
  """
  scope_group = base.ArgumentGroup(
      help='Arguments to configure the crawler scope:',
      required=not for_update)
  scope_group.AddArgument(GetCrawlScopeArg(for_update))
  scope_group.AddArgument(
      GetBucketArgForCreate() if not for_update else GetBucketArgsForUpdate())

  scheduling_group = base.ArgumentGroup(
      help='Arguments to configure the crawler run scheduling:',
      required=not for_update)
  scheduling_group.AddArgument(GetRunOptionArg(for_update))
  scheduling_group.AddArgument(GetRunScheduleArg(for_update))

  return [scope_group, scheduling_group]


def GetCrawlScopeArg(for_update):
  choices = {
      'bucket': 'Directs the crawler to crawl specific buckets within the '
                'project that owns the crawler.',
      'project': 'Directs the crawler to crawl all the buckets of the project '
                 'that owns the crawler.',
      'organization': 'Directs the crawler to crawl all the buckets of the '
                      'projects in the organization that owns the crawler.'}
  return base.ChoiceArgument(
      '--crawl-scope',
      choices=choices,
      required=not for_update,
      help_str='Scope of the crawler.')


def GetBucketArgForCreate():
  return base.Argument(
      '--buckets',
      type=arg_parsers.ArgList(),
      metavar='BUCKET',
      help='A list of buckets to crawl. This argument should be provided if '
           'and only if `--crawl-scope=BUCKET` was specified.')


def GetBucketArgsForUpdate():
  """Returns bucket-related args for crawler update."""
  bucket_group = base.ArgumentGroup(
      help='Update buckets to crawl. These arguments can be provided only if '
           'the crawler will be bucket-scoped after updating.')
  bucket_group.AddArgument(
      base.Argument(
          '--add-buckets',
          type=arg_parsers.ArgList(),
          metavar='BUCKET',
          help='List of buckets to add to the crawl scope.'))

  remove_bucket_group = base.ArgumentGroup(mutex=True)
  remove_bucket_group.AddArgument(
      base.Argument(
          '--remove-buckets',
          type=arg_parsers.ArgList(),
          metavar='BUCKET',
          help='List of buckets to remove from the crawl scope.'))
  remove_bucket_group.AddArgument(
      base.Argument(
          '--clear-buckets',
          action='store_true',
          help='If specified, clear the existing list of buckets in the crawl '
               'scope.'))

  bucket_group.AddArgument(remove_bucket_group)
  return bucket_group


def GetRunOptionArg(for_update):
  choices = {
      'manual': 'The crawler run will have to be triggered manually.',
      'scheduled': 'The crawler will run automatically on a schedule.'}
  return base.ChoiceArgument(
      '--run-option',
      choices=choices,
      required=not for_update,
      help_str='Run option of the crawler.')


def GetRunScheduleArg(for_update):
  help_str = 'Schedule for the crawler run.'
  if not for_update:
    help_str += (' This argument should be provided if and only if '
                 '`--run-option=SCHEDULED` was specified.')
  else:
    help_str += (' This argument can be provided only if the crawler run '
                 'option will be scheduled after updating.')
  return base.ChoiceArgument(
      '--run-schedule',
      choices=['daily', 'weekly'],
      help_str=help_str)
