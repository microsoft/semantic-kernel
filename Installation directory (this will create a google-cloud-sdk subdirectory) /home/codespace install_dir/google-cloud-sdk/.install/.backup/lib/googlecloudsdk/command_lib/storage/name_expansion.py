# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Module for handling recursive expansion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import folder_util
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import wildcard_iterator
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import log
from googlecloudsdk.core.util import debug_output


class BucketSetting(enum.Enum):
  """An enum saying whether or not to include matched buckets."""

  YES = '_yes'
  NO = '_no'
  NO_WITH_ERROR = '_no_with_error'


class RecursionSetting(enum.Enum):
  """An enum saying whether or not recursion is requested."""
  NO = '_no'
  NO_WITH_WARNING = '_no_with_warning'
  YES = '_yes'


class NameExpansionIterator:
  """Expand all urls passed as arguments, and yield NameExpansionResult.

  For each url, expands wildcards, object-less bucket names,
  subdir bucket names, and directory names, and generates a flat listing of
  all the matching objects/files.
  The resulting objects/files are wrapped within a NameExpansionResult instance.
  See NameExpansionResult docstring for more info.
  """

  def __init__(
      self,
      urls_iterable,
      fields_scope=cloud_api.FieldsScope.NO_ACL,
      ignore_symlinks=False,
      include_buckets=BucketSetting.NO,
      managed_folder_setting=folder_util.ManagedFolderSetting.DO_NOT_LIST,
      object_state=cloud_api.ObjectState.LIVE,
      preserve_symlinks=False,
      raise_error_for_unmatched_urls=True,
      raise_managed_folder_precondition_errors=True,
      recursion_requested=RecursionSetting.NO_WITH_WARNING,
      url_found_match_tracker=None,
  ):
    """Instantiates NameExpansionIterator.

    Args:
      urls_iterable (Iterable[str]): The URLs to expand.
      fields_scope (cloud_api.FieldsScope): Determines amount of metadata
        returned by API.
      ignore_symlinks (bool): Skip over symlinks instead of following them.
      include_buckets (BucketSetting): Whether to fetch matched buckets and
        whether to raise an error.
      managed_folder_setting (folder_util.ManagedFolderSetting): Indicates how
        to deal with managed folders.
      object_state (cloud_api.ObjectState): Versions of objects to query.
      preserve_symlinks (bool): Preserve symlinks instead of following them.
      raise_error_for_unmatched_urls (bool): If True, raises an error if any url
        in `url_found_match_tracker` is unmatched after expansion.
      raise_managed_folder_precondition_errors (bool): If True, raises
        precondition errors from managed folder listing. Otherwise, suppresses
        these errors. This is helpful in commands that list managed folders by
        default.
      recursion_requested (RecursionSetting): Says whether or not recursion is
        requested.
      url_found_match_tracker (OrderedDict|None): Maps top-level URLs to a
        boolean indicating whether they matched resources. Mutated as resources
        are yielded. Reusing a tracker dict across NameExpansionIterators with
        different expansion criteria suppresses unmatched errors if any iterator
        expands a URL.
    """
    self.object_state = object_state
    self._urls_iterator = (
        plurality_checkable_iterator.PluralityCheckableIterator(urls_iterable)
    )
    self._fields_scope = fields_scope
    self._ignore_symlinks = ignore_symlinks
    self._include_buckets = include_buckets
    self._managed_folder_setting = managed_folder_setting
    self._preserve_symlinks = preserve_symlinks
    self._raise_error_for_unmatched_urls = raise_error_for_unmatched_urls
    self._raise_managed_folder_precondition_errors = (
        raise_managed_folder_precondition_errors
    )
    self._recursion_requested = recursion_requested

    if url_found_match_tracker is None:
      self._url_found_match_tracker = collections.OrderedDict()
    else:
      self._url_found_match_tracker = url_found_match_tracker

    self._top_level_iterator = (
        plurality_checkable_iterator.PluralityCheckableIterator(
            self._get_top_level_iterator()
        )
    )
    self._has_multiple_top_level_resources = None

  def _get_wildcard_iterator(
      self,
      url,
      managed_folder_setting=folder_util.ManagedFolderSetting.DO_NOT_LIST,
  ):
    """Returns get_wildcard_iterator with instance variables as args."""
    return wildcard_iterator.get_wildcard_iterator(
        url,
        fetch_encrypted_object_hashes=True,
        fields_scope=self._fields_scope,
        ignore_symlinks=self._ignore_symlinks,
        managed_folder_setting=managed_folder_setting,
        object_state=self.object_state,
        preserve_symlinks=self._preserve_symlinks,
        raise_managed_folder_precondition_errors=(
            self._raise_managed_folder_precondition_errors
        ),
    )

  @property
  def has_multiple_top_level_resources(self):
    """Returns if the iterator yields plural items without recursing.

    Also returns True if the iterator was created with multiple URLs.
    This may not be true if one URL doesn't return anything, but it's
    consistent with gsutil and the user's probable intentions.

    Returns:
      Boolean indicating if iterator contains multiple top-level sources.
    """
    if self._has_multiple_top_level_resources is None:
      self._has_multiple_top_level_resources = (
          self._urls_iterator.is_plural()
          or self._top_level_iterator.is_plural()
      )
    return self._has_multiple_top_level_resources

  def _get_top_level_iterator(self):
    """Iterates over user-entered URLs and does initial processing."""
    for url in self._urls_iterator:
      original_storage_url = storage_url.storage_url_from_string(url)
      if (
          isinstance(original_storage_url, storage_url.CloudUrl)
          and original_storage_url.is_bucket()
          and self._recursion_requested is not RecursionSetting.YES
          and self._include_buckets is BucketSetting.NO_WITH_ERROR
      ):
        raise errors.InvalidUrlError(
            'Expected object URL. Received: {}'.format(url)
        )
      # Set to True if associated Cloud resource found in __iter__.
      self._url_found_match_tracker[url] = self._url_found_match_tracker.get(
          url, False
      )

      if (
          self._managed_folder_setting
          in {
              folder_util.ManagedFolderSetting.LIST_WITH_OBJECTS,
              folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS,
          }
          and self._recursion_requested is RecursionSetting.YES
      ):
        # No need to perform additional managed folder API calls, since we will
        # recurse inside of containers anyway.
        wildcard_iterator_managed_folder_setting = (
            folder_util.ManagedFolderSetting.LIST_AS_PREFIXES
        )
      else:
        wildcard_iterator_managed_folder_setting = self._managed_folder_setting

      for resource in self._get_wildcard_iterator(
          url,
          managed_folder_setting=wildcard_iterator_managed_folder_setting,
      ):
        if (
            self._managed_folder_setting
            is folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS
            and isinstance(resource, resource_reference.ObjectResource)
        ):
          continue
        yield url, self._get_name_expansion_result(resource,
                                                   resource.storage_url,
                                                   original_storage_url)

  def _get_nested_objects_iterator(self, parent_name_expansion_result):
    new_storage_url = parent_name_expansion_result.resource.storage_url.join(
        '**')
    child_resources = self._get_wildcard_iterator(
        new_storage_url.url_string,
        managed_folder_setting=self._managed_folder_setting,
    )
    for child_resource in child_resources:
      yield self._get_name_expansion_result(
          child_resource, parent_name_expansion_result.resource.storage_url,
          parent_name_expansion_result.original_url)

  def _get_name_expansion_result(self, resource, expanded_url, original_url):
    """Returns a NameExpansionResult, removing generations when appropriate."""
    keep_generation_in_url = (
        self.object_state is cloud_api.ObjectState.LIVE_AND_NONCURRENT
        or original_url.generation  # User requested a specific generation.
    )
    if not keep_generation_in_url:
      new_storage_url = storage_url.storage_url_from_string(
          resource.storage_url.versionless_url_string)
      resource.storage_url = new_storage_url
    return NameExpansionResult(resource, expanded_url, original_url)

  def _raise_no_url_match_error_if_necessary(self):
    if not self._raise_error_for_unmatched_urls:
      return

    non_matching_urls = [
        url for url, found_match in self._url_found_match_tracker.items()
        if not found_match
    ]
    if non_matching_urls:
      raise errors.InvalidUrlError(
          'The following URLs matched no objects or files:\n-{}'.format(
              '\n-'.join(non_matching_urls)))

  def _raise_error_if_multiple_sources_include_stdin(self, expanded_url):
    if (self._has_multiple_top_level_resources and isinstance(
        expanded_url, storage_url.FileUrl) and expanded_url.is_stdio):
      raise errors.Error(
          'Multiple URL strings are not supported when transferring from'
          ' stdin.')

  def __iter__(self):
    """Iterates over each URL in self._urls_iterator and yield the expanded result.

    Yields:
      NameExpansionResult instance.

    Raises:
      InvalidUrlError: No matching objects found.
    """
    self._has_multiple_top_level_resources = self._top_level_iterator.is_plural(
    )
    for input_url, name_expansion_result in self._top_level_iterator:

      self._raise_error_if_multiple_sources_include_stdin(
          name_expansion_result.expanded_url)

      should_return_bucket = self._include_buckets is BucketSetting.YES and (
          name_expansion_result.resource.storage_url.is_bucket()
      )
      should_return_managed_folder = self._managed_folder_setting in {
          folder_util.ManagedFolderSetting.LIST_WITH_OBJECTS,
          folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS,
      } and isinstance(
          name_expansion_result.resource,
          resource_reference.ManagedFolderResource,
      )
      if (
          not resource_reference.is_container_or_has_container_url(
              name_expansion_result.resource
          )
          or should_return_bucket
          or should_return_managed_folder
      ):
        self._url_found_match_tracker[input_url] = True
        yield name_expansion_result

      if resource_reference.is_container_or_has_container_url(
          name_expansion_result.resource):
        if self._recursion_requested is RecursionSetting.YES:
          for nested_name_expansion_result in self._get_nested_objects_iterator(
              name_expansion_result):
            self._url_found_match_tracker[input_url] = True
            yield nested_name_expansion_result

        elif not (should_return_bucket or should_return_managed_folder):
          if self._recursion_requested is RecursionSetting.NO_WITH_WARNING:
            # Does not warn about buckets processed above because it's confusing
            # to warn about something that was successfully processed.
            log.warning('Omitting {} because it is a container, and recursion'
                        ' is not enabled.'.format(
                            name_expansion_result.resource))

    self._raise_no_url_match_error_if_necessary()


class NameExpansionResult:
  """Holds one fully expanded result from iterating over NameExpansionIterator.

  This class is required to pass the expanded_url information to the caller.
  This information is required for cp and rsync command, where the destination
  name is determined based on the expanded source url.
  For example, let's say we have the following objects:
  gs://bucket/dir1/a.txt
  gs://bucket/dir1/b/c.txt

  If we run the following command:
  cp -r gs://bucket/dir* foo

  We would need to know that gs://bucket/dir* was expanded to gs://bucket/dir1
  so that we can determine destination paths (foo/a.txt, foo/b/c.txt) assuming
  that foo does not exist.

  Attributes:
    resource (Resource): Yielded by the WildcardIterator.
    expanded_url (StorageUrl): The expanded wildcard url.
    original_url (StorageUrl): Pre-expanded URL.
  """

  def __init__(self, resource, expanded_url, original_url):
    """Initialize NameExpansionResult.

    Args:
      resource (resource_reference.Resource): Yielded by the WildcardIterator.
      expanded_url (StorageUrl): The expanded url string without any wildcard.
        This value should preserve generation even if not available in
        resource.storage_url. The versionless version of this should be same
        as resource.storage_url if recursion was not requested. This field is
        intended for only the cp and rsync commands.
      original_url (StorageUrl): Pre-expanded URL. Useful for knowing intention.
    """
    self.resource = resource
    self.expanded_url = expanded_url
    self.original_url = original_url

  def __repr__(self):
    return debug_output.generic_repr(self)

  def __str__(self):
    return self.resource.storage_url.url_string

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    # Leave out original_url because two different URLs can expand to the same
    # result. This is a "results" class.
    return (self.resource == other.resource
            and self.expanded_url == other.expanded_url)
