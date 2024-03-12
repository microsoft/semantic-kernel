# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Functions for du command to display resource size."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.command_lib.storage import list_util
from googlecloudsdk.command_lib.storage.resources import shim_format_util


class _ObjectFormatWrapper(list_util.BaseFormatWrapper):
  """For formatting how obejects are printed when listed by du."""

  def __str__(self):
    """Returns string of select properties from resource."""
    size = getattr(self.resource, 'size', 0)
    url_string, _ = self._check_and_handles_versions()

    # Example: 6194    gs://test/doc/README.md
    return ('{size:<13}{url}').format(
        size=list_util.check_and_convert_to_readable_sizes(
            size, self._readable_sizes, use_gsutil_style=self._use_gsutil_style
        ),
        url=url_string,
    )


class _ContainerSummaryFormatWrapper(list_util.BaseFormatWrapper):
  """For formatting how containers are printed when listed by du."""

  def __init__(
      self,
      resource,
      container_size=None,
      object_state=None,
      readable_sizes=False,
      use_gsutil_style=False,
  ):
    """See list_util.BaseFormatWrapper class for function doc strings."""
    super(_ContainerSummaryFormatWrapper, self).__init__(
        resource,
        display_detail=list_util.DisplayDetail.SHORT,
        object_state=object_state,
        readable_sizes=readable_sizes,
        use_gsutil_style=use_gsutil_style,
    )
    self._container_size = container_size

  def __str__(self):
    """Returns string of select properties from resource."""
    raw_url_string = self.resource.storage_url.versionless_url_string
    # Buckets and prefixes: only print container_size.
    if self.resource.storage_url.is_bucket():
      # For parity:
      # https://github.com/GoogleCloudPlatform/gsutil/blob/417c4a187ec4ae5c8b84a3dc4c099af9e1f5bbb1/gslib/commands/du.py#L290
      url_string = raw_url_string.rstrip('/')
    else:
      url_string = raw_url_string

    # Convert to human readable format.
    size = list_util.check_and_convert_to_readable_sizes(
        self._container_size, self._readable_sizes, self._use_gsutil_style
    )

    # Example: 6194    gs://test/doc/README.md
    return ('{size:<13}{url}').format(
        size=size,
        url=url_string,
    )


class _BucketSummaryFormatWrapper(_ContainerSummaryFormatWrapper):

  def __str__(self):
    if self.resource.storage_url.is_bucket():
      return super(_BucketSummaryFormatWrapper, self).__str__()
    else:
      return ''


class DuExecutor(list_util.BaseListExecutor):
  """Helper class for the Du command."""

  def __init__(
      self,
      cloud_urls,
      exclude_patterns=None,
      object_state=None,
      readable_sizes=False,
      summarize=False,
      total=False,
      use_gsutil_style=False,
      zero_terminator=False,
  ):
    """See list_util.BaseListExecutor class for function doc strings."""

    super(DuExecutor, self).__init__(
        cloud_urls=cloud_urls,
        exclude_patterns=exclude_patterns,
        object_state=object_state,
        readable_sizes=readable_sizes,
        recursion_flag=True,
        total=total,
        use_gsutil_style=use_gsutil_style,
        zero_terminator=zero_terminator,
    )
    self._summarize = summarize
    if self._summarize:
      self._container_summary_wrapper = _BucketSummaryFormatWrapper
    else:
      self._container_summary_wrapper = _ContainerSummaryFormatWrapper
      self._object_wrapper = _ObjectFormatWrapper

  def _should_only_display_buckets(self, raw_cloud_url):
    # Du should always list objects, even for providers.
    return False

  def _print_summary_for_top_level_url(
      self, resource_url, only_display_buckets, object_count, total_bytes
  ):
    if not self._summarize or resource_url.is_provider():
      return
    if self._readable_sizes:
      total_bytes = shim_format_util.get_human_readable_byte_value(
          total_bytes, use_gsutil_style=self._use_gsutil_style
      )

    if resource_url.is_bucket():
      # For parity:
      # https://github.com/GoogleCloudPlatform/gsutil/blob/417c4a187ec4ae5c8b84a3dc4c099af9e1f5bbb1/gslib/commands/du.py#L290
      url_string = resource_url.url_string.rstrip('/')
    else:
      url_string = resource_url.url_string

    print(
        '{size:<13}{url}'.format(
            size=total_bytes, url=url_string
        ),
        end='\0' if self._zero_terminator else '\n'
    )

  def _print_total(self, all_sources_total_bytes):
    print(
        '{size:<13}total'.format(
            size=list_util.check_and_convert_to_readable_sizes(
                all_sources_total_bytes,
                self._readable_sizes,
                self._use_gsutil_style,
            )
        ),
        end='\0' if self._zero_terminator else '\n'
    )
