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
"""Task for retrieving a list of resources from the cloud.

Typically executed in a task iterator:
googlecloudsdk.command_lib.storage.tasks.task_executor.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.storage import list_util
from googlecloudsdk.command_lib.storage.resources import gcloud_full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import gsutil_full_resource_formatter
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_util
from googlecloudsdk.command_lib.storage.resources import shim_format_util


LONG_LIST_ROW_FORMAT = (
    '{size:>10}  {creation_time:>20}  {url}{metageneration}{etag}'
)


class _HeaderFormatWrapper(list_util.BaseFormatWrapper):
  """For formatting how headers print when listed."""

  def __init__(
      self,
      resource,
      display_detail=list_util.DisplayDetail.SHORT,
      include_etag=False,
      object_state=None,
      readable_sizes=False,
      full_formatter=None,
      use_gsutil_style=False,
  ):
    """See list_util.BaseFormatWrapper class for function doc strings."""

    super(_HeaderFormatWrapper, self).__init__(
        resource,
        display_detail=display_detail,
        full_formatter=full_formatter,
        include_etag=include_etag,
        object_state=object_state,
        readable_sizes=readable_sizes,
        use_gsutil_style=use_gsutil_style,
    )

  def __str__(self):
    if self._use_gsutil_style and isinstance(
        self.resource, resource_reference.BucketResource
    ):
      # Gsutil does not show header lines for buckets.
      return ''

    url = self.resource.storage_url.versionless_url_string
    if self._display_detail == list_util.DisplayDetail.JSON:
      return self.resource.get_json_dump()
    # This will print as "gs://bucket:" or "gs://bucket/prefix/:".
    return '\n{}:'.format(url)


class _ResourceFormatWrapper(list_util.BaseFormatWrapper):
  """For formatting how resources print when listed."""

  def __init__(
      self,
      resource,
      display_detail=list_util.DisplayDetail.SHORT,
      full_formatter=None,
      include_etag=False,
      object_state=None,
      readable_sizes=False,
      use_gsutil_style=False,
  ):
    """See list_util.BaseFormatWrapper class for function doc strings."""

    super(_ResourceFormatWrapper, self).__init__(
        resource,
        display_detail=display_detail,
        include_etag=include_etag,
        object_state=object_state,
        readable_sizes=readable_sizes,
        use_gsutil_style=use_gsutil_style,
    )

    self._full_formatter = full_formatter

  def _format_for_list_long(self):
    """Returns string of select properties from resource."""
    if isinstance(self.resource, resource_reference.PrefixResource):
      # Align PrefixResource URLs with ObjectResource URLs.
      return LONG_LIST_ROW_FORMAT.format(
          size='',
          creation_time='',
          url=self.resource.storage_url.url_string,
          metageneration='',
          etag='',
      )

    creation_time = resource_util.get_formatted_timestamp_in_utc(
        self.resource.creation_time
    )

    url_string, metageneration_string = self._check_and_handles_versions()

    if self._include_etag:
      etag_string = '  etag={}'.format(str(self.resource.etag))
    else:
      etag_string = ''

    # Full example (add 9 spaces of padding to the left):
    # 8  2020-07-27T20:58:25Z  gs://b/o  metageneration=4  etag=CJqt6aup7uoCEAQ=
    return LONG_LIST_ROW_FORMAT.format(
        size=list_util.check_and_convert_to_readable_sizes(
            self.resource.size, self._readable_sizes, self._use_gsutil_style
        ),
        creation_time=creation_time,
        url=url_string,
        metageneration=metageneration_string,
        etag=etag_string,
    )

  def __str__(self):
    if self._display_detail == list_util.DisplayDetail.LONG and (
        isinstance(self.resource, resource_reference.ObjectResource)
        or isinstance(self.resource, resource_reference.PrefixResource)
    ):
      return self._format_for_list_long()

    show_version_in_url = self._object_state in (
        cloud_api.ObjectState.LIVE_AND_NONCURRENT,
        cloud_api.ObjectState.SOFT_DELETED,
    )
    if self._display_detail == list_util.DisplayDetail.FULL and (
        isinstance(self.resource, resource_reference.BucketResource)
        or isinstance(self.resource, resource_reference.ObjectResource)
    ):
      return self._full_formatter.format(
          self.resource, show_version_in_url=show_version_in_url
      )
    if self._display_detail == list_util.DisplayDetail.JSON:
      return self.resource.get_json_dump()
    if show_version_in_url:
      # Include generation in URL.
      return self.resource.storage_url.url_string
    return self.resource.storage_url.versionless_url_string


class LsExecutor(list_util.BaseListExecutor):
  """Helper class for the ls command."""

  def __init__(
      self,
      cloud_urls,
      buckets_flag=False,
      display_detail=list_util.DisplayDetail.SHORT,
      fetch_encrypted_object_hashes=False,
      halt_on_empty_response=True,
      include_etag=False,
      include_managed_folders=False,
      next_page_token=None,
      object_state=None,
      readable_sizes=False,
      recursion_flag=False,
      use_gsutil_style=False,
  ):
    """See list_util.BaseListExecutor class for function doc strings."""
    super(LsExecutor, self).__init__(
        cloud_urls=cloud_urls,
        buckets_flag=buckets_flag,
        display_detail=display_detail,
        fetch_encrypted_object_hashes=fetch_encrypted_object_hashes,
        halt_on_empty_response=halt_on_empty_response,
        include_etag=include_etag,
        include_managed_folders=include_managed_folders,
        next_page_token=next_page_token,
        object_state=object_state,
        readable_sizes=readable_sizes,
        recursion_flag=recursion_flag,
        use_gsutil_style=use_gsutil_style,
    )

    if use_gsutil_style:
      self._full_formatter = (
          gsutil_full_resource_formatter.GsutilFullResourceFormatter()
      )
    else:
      self._full_formatter = (
          gcloud_full_resource_formatter.GcloudFullResourceFormatter()
      )
    self._header_wrapper = _HeaderFormatWrapper
    self._object_wrapper = _ResourceFormatWrapper

  def _print_summary_for_top_level_url(
      self, resource_url, only_display_buckets, object_count, total_bytes
  ):
    if (
        self._display_detail
        in (list_util.DisplayDetail.LONG, list_util.DisplayDetail.FULL)
        and not only_display_buckets
    ):
      # Long listing needs summary line.
      print(
          'TOTAL: {} objects, {} bytes ({})'.format(
              object_count,
              int(total_bytes),
              shim_format_util.get_human_readable_byte_value(
                  total_bytes, self._use_gsutil_style
              ),
          )
      )

  def _print_json_list(self, resource_wrappers):
    """Prints ResourceWrapper objects as JSON list."""
    is_empty_list = True
    for i, resource_wrapper in enumerate(resource_wrappers):
      is_empty_list = False
      if i == 0:
        # Start of JSON list for long long listing.
        print('[')
        print(resource_wrapper, end='')
      else:
        # Print resource without newline at end to allow list formatting for
        # unknown number of items in generator.
        print(',\n{}'.format(resource_wrapper), end='')

    # New line because we were removing it from previous prints to give us
    # the ability to do a trailing comma for JSON list printing.
    print()
    if not is_empty_list:
      # Close long long listing JSON list. Prints nothing if no items.
      print(']')
