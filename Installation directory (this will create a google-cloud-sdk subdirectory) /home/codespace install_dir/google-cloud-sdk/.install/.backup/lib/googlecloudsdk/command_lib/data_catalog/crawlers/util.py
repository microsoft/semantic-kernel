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
"""Utilities for Data Catalog crawler commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import crawlers
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import exceptions

DATACATALOG_CRAWLER_API_VERSION = 'v1alpha3'


class InvalidCrawlScopeError(exceptions.Error):
  """Error if a crawl scope is invalid."""


class InvalidRunOptionError(exceptions.Error):
  """Error if a run option is invalid."""


class NoFieldsSpecifiedError(exceptions.Error):
  """Error if no fields are specified for a patch request."""


def ValidateAndParseFlagsForUpdate(ref, args, request):
  """Python hook that validates and parses crawler config flags.

  Normally all the functions called here would be provided directly as
  modify_request_hooks in the update command YAML file. However, this would
  require setting read_modify_update: True to obtain the existing crawler
  beforehand, incurring an extra GET API call that may be unnecessary depending
  on what fields need to be updated.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The update crawler request.
  Returns:
    Request with scope and scheduling flags set appropriately.
  Raises:
    InvalidCrawlScopeError: If the crawl scope configuration is not valid.
    InvalidRunOptionError: If the scheduling configuration is not valid.
  """
  client = crawlers.CrawlersClient()
  # Call client.Get(ref) lazily and cache the result, so we only make one API
  # call to get the existing crawler (and only if necessary).
  crawler = repeated.CachedResult.FromFunc(client.Get, ref)

  request = ValidateScopeFlagsForUpdate(ref, args, request, crawler)
  request = ValidateSchedulingFlagsForUpdate(ref, args, request, crawler)
  request = ParseScopeFlagsForUpdate(ref, args, request, crawler)
  request = ParseSchedulingFlagsForUpdate(ref, args, request)
  request = ParseBundleSpecsFlagsForUpdate(ref, args, request, crawler)
  return request


def ParseBundleSpecsFlagsForUpdate(ref, args, request, crawler):
  """Python hook that parses the bundle spec args into the update request.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The update crawler request.
    crawler: CachedResult, The cached crawler result.
  Returns:
    Request with bundling specs set appropriately.
  """
  del ref
  if not _IsChangeBundleSpecsSpecified(args):
    return request

  bundle_specs = crawler.Get().config.bundleSpecs or []
  if args.IsSpecified('clear_bundle_specs'):
    bundle_specs = []
  if args.IsSpecified('remove_bundle_specs'):
    to_remove = set(args.remove_bundle_specs)
    bundle_specs = [b for b in bundle_specs if b not in to_remove]
  if args.IsSpecified('add_bundle_specs'):
    bundle_specs += args.add_bundle_specs

  arg_utils.SetFieldInMessage(
      request,
      'googleCloudDatacatalogV1alpha3Crawler.config.bundleSpecs',
      bundle_specs)
  return request


def ValidateScopeFlagsForCreate(ref, args, request):
  """Validates scope flags for create.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The create request.
  Returns:
    The request, if the crawl scope configuration is valid.
  Raises:
    InvalidCrawlScopeError: If the crawl scope configuration is not valid.
  """
  del ref
  if args.IsSpecified('buckets') and args.crawl_scope != 'bucket':
    raise InvalidCrawlScopeError(
        'Argument `--buckets` is only valid for bucket-scoped crawlers. '
        'Use `--crawl-scope=bucket` to specify a bucket-scoped crawler.')
  if not args.IsSpecified('buckets') and args.crawl_scope == 'bucket':
    raise InvalidCrawlScopeError(
        'Argument `--buckets` must be provided when creating a bucket-scoped '
        'crawler.')
  return request


def ValidateScopeFlagsForUpdate(ref, args, request, crawler):
  """Validates scope flags for update.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The update request.
    crawler: CachedResult, The cached crawler result.
  Returns:
    The request, if the crawl scope configuration is valid.
  Raises:
    InvalidCrawlScopeError: If the crawl scope configuration is not valid.
  """
  del ref
  change_buckets = _IsChangeBucketsSpecified(args)

  if (change_buckets and args.crawl_scope != 'bucket' and
      (args.IsSpecified('crawl_scope') or
       crawler.Get().config.bucketScope is None)):
    raise InvalidCrawlScopeError(
        'Arguments `--add-buckets`, `--remove-buckets`, and `--clear-buckets` '
        'are only valid for bucket-scoped crawlers. Use `--crawl-scope=bucket` '
        'to specify a bucket-scoped crawler.')
  if not change_buckets and args.crawl_scope == 'bucket':
    raise InvalidCrawlScopeError(
        'Must provide buckets to add or remove when updating the crawl scope '
        'of a bucket-scoped crawler.')
  return request


def SetUpdateMask(ref, args, request):
  """Python hook that computes the update mask for a patch request.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The update crawler request.
  Returns:
    Request with update mask set appropriately.
  Raises:
    NoFieldsSpecifiedError: If no fields were provided for updating.
  """
  del ref
  update_mask = []

  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')

  if _IsChangeBundleSpecsSpecified(args):
    update_mask.append('config.bundleSpecs')

  if args.crawl_scope == 'project':
    update_mask.append('config.projectScope')
  elif args.crawl_scope == 'organization':
    update_mask.append('config.organizationScope')
  elif _IsChangeBucketsSpecified(args):
    update_mask.append('config.bucketScope')

  if args.run_option == 'manual':
    update_mask.append('config.adHocRun')
  elif args.run_option == 'scheduled' or args.IsSpecified('run_schedule'):
    update_mask.append('config.scheduledRun')

  if not update_mask:
    raise NoFieldsSpecifiedError(
        'Must specify at least one parameter to update.')

  request.updateMask = ','.join(update_mask)
  return request


def ParseScopeFlagsForCreate(ref, args, request):
  """Python hook that parses the crawl scope args into the create request.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The create crawler request.
  Returns:
    Request with crawl scope set appropriately.
  """
  del ref
  client = crawlers.CrawlersClient()
  messages = client.messages
  if args.IsSpecified('buckets'):
    buckets = [messages.GoogleCloudDatacatalogV1alpha3BucketSpec(bucket=b)
               for b in args.buckets]
  else:
    buckets = None
  return _SetScopeInRequest(args.crawl_scope, buckets, request, messages)


def ParseScopeFlagsForUpdate(ref, args, request, crawler):
  """Python hook that parses the crawl scope args into the update request.

  Args:
    ref: The crawler resource reference.
    args: The parsed args namespace.
    request: The update crawler request.
    crawler: CachedResult, The cached crawler result.
  Returns:
    Request with crawl scope set appropriately.
  """
  del ref
  client = crawlers.CrawlersClient()
  messages = client.messages

  if _IsChangeBucketsSpecified(args):
    buckets = _GetBucketsPatch(args, crawler, messages)
    # Infer the crawl scope so that the user can update buckets of an existing
    # bucket-scoped crawler without needing to explicitly specify
    # `--crawl-scope=bucket` again.
    crawl_scope = 'bucket'
  else:
    buckets = None
    crawl_scope = args.crawl_scope

  return _SetScopeInRequest(crawl_scope, buckets, request, messages)


def _IsChangeBucketsSpecified(args):
  return (args.IsSpecified('add_buckets') or
          args.IsSpecified('remove_buckets') or
          args.IsSpecified('clear_buckets'))


def _IsChangeBundleSpecsSpecified(args):
  return (args.IsSpecified('add_bundle_specs') or
          args.IsSpecified('remove_bundle_specs') or
          args.IsSpecified('clear_bundle_specs'))


def _SetScopeInRequest(crawl_scope, buckets, request, messages):
  """Returns request with the crawl scope set."""
  if crawl_scope == 'bucket':
    if not buckets:
      raise InvalidCrawlScopeError(
          'At least one bucket must be included in the crawl scope of a '
          'bucket-scoped crawler.')
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1alpha3Crawler.config.bucketScope.buckets',
        buckets)
  elif crawl_scope == 'project':
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1alpha3Crawler.config.projectScope',
        messages.GoogleCloudDatacatalogV1alpha3ParentProjectScope())
  elif crawl_scope == 'organization':
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1alpha3Crawler.config.organizationScope',
        messages.GoogleCloudDatacatalogV1alpha3ParentOrganizationScope())

  return request


def _GetBucketsPatch(args, crawler, messages):
  """Returns list of buckets for a patch request based on the args provided.

  Args:
    args: The parsed args namespace.
    crawler: CachedResult, The cached crawler result.
    messages: The messages module.
  Returns:
    Desired list of buckets.
  """
  bucket_scope = crawler.Get().config.bucketScope
  buckets = bucket_scope.buckets if bucket_scope else []

  if args.IsSpecified('clear_buckets'):
    buckets = []
  if args.IsSpecified('remove_buckets'):
    to_remove = set(args.remove_buckets)
    buckets = [b for b in buckets if b.bucket not in to_remove]
  if args.IsSpecified('add_buckets'):
    buckets += [messages.GoogleCloudDatacatalogV1alpha3BucketSpec(bucket=b)
                for b in args.add_buckets]
  return buckets


def ValidateSchedulingFlagsForCreate(ref, args, request):
  del ref
  return _ValidateSchedulingFlags(args, request)


def ValidateSchedulingFlagsForUpdate(ref, args, request, crawler):
  del ref
  return _ValidateSchedulingFlags(args, request, crawler, for_update=True)


def _ValidateSchedulingFlags(args, request, crawler=None, for_update=False):
  """Validates scheduling flags.

  Args:
    args: The parsed args namespace.
    request: The create or update request.
    crawler: CachedResult, The cached crawler result.
    for_update: If the request is for update instead of create.
  Returns:
    The request, if the scheduling configuration is valid.
  Raises:
    InvalidRunOptionError: If the scheduling configuration is not valid.
  """
  if args.run_option == 'scheduled' and not args.IsSpecified('run_schedule'):
    raise InvalidRunOptionError(
        'Argument `--run-schedule` must be provided if `--run-option=scheduled`'
        ' was specified.')

  if args.run_option != 'scheduled' and args.IsSpecified('run_schedule'):
    # This is always an error for create, but for update we allow the user to
    # modify the run schedule of an existing scheduled crawler without needing
    # to explicitly specify `--run-option=scheduled` again.
    if (not for_update or
        args.IsSpecified('run_option') or
        crawler.Get().config.scheduledRun is None):
      raise InvalidRunOptionError(
          'Argument `--run-schedule` can only be provided for scheduled '
          'crawlers. Use `--run-option=scheduled` to specify a scheduled '
          'crawler.')

  return request


def ParseSchedulingFlagsForCreate(ref, args, request):
  del ref
  client = crawlers.CrawlersClient()
  messages = client.messages
  return _SetRunOptionInRequest(
      args.run_option, args.run_schedule, request, messages)


def ParseSchedulingFlagsForUpdate(ref, args, request):
  del ref
  client = crawlers.CrawlersClient()
  messages = client.messages
  # Infer the run schedule so that the user can update the schedule of an
  # existing scheduled crawler without needing to explicitly specify
  # `--run-option=scheduled` again.
  run_option = ('scheduled' if args.IsSpecified('run_schedule')
                else args.run_option)
  return _SetRunOptionInRequest(
      run_option, args.run_schedule, request, messages)


def _SetRunOptionInRequest(run_option, run_schedule, request, messages):
  """Returns request with the run option set."""
  if run_option == 'manual':
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1alpha3Crawler.config.adHocRun',
        messages.GoogleCloudDatacatalogV1alpha3AdhocRun())
  elif run_option == 'scheduled':
    scheduled_run_option = arg_utils.ChoiceToEnum(
        run_schedule,
        (messages.GoogleCloudDatacatalogV1alpha3ScheduledRun
         .ScheduledRunOptionValueValuesEnum))
    arg_utils.SetFieldInMessage(
        request,
        'googleCloudDatacatalogV1alpha3Crawler.config.scheduledRun.scheduledRunOption',
        scheduled_run_option)
  return request
