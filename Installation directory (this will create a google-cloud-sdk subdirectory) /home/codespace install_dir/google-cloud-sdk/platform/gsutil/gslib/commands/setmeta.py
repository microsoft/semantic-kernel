# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implementation of setmeta command for setting cloud object metadata."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time

from apitools.base.py import encoding
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import Preconditions
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import MetadataMessage
from gslib.utils import constants
from gslib.utils import parallelism_framework_util
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.metadata_util import IsCustomMetadataHeader
from gslib.utils.retry_util import Retry
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.text_util import InsistAsciiHeader
from gslib.utils.text_util import InsistAsciiHeaderValue
from gslib.utils.translation_helper import CopyObjectMetadata
from gslib.utils.translation_helper import ObjectMetadataFromHeaders
from gslib.utils.translation_helper import PreconditionsFromHeaders

_PutToQueueWithTimeout = parallelism_framework_util.PutToQueueWithTimeout

_SYNOPSIS = """
  gsutil setmeta -h [header:value|header] ... url...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The gsutil setmeta command allows you to set or remove the metadata on one
  or more objects. It takes one or more header arguments followed by one or
  more URLs, where each header argument is in one of two forms:

  - If you specify ``header:value``, it sets the provided value for the
    given header on all applicable objects.

  - If you specify ``header`` (with no value), it removes the given header
    from all applicable objects.

  For example, the following command sets the ``Content-Type`` and
  ``Cache-Control`` headers while also removing the ``Content-Disposition``
  header on the specified objects:

    gsutil setmeta -h "Content-Type:text/html" \\
      -h "Cache-Control:public, max-age=3600" \\
      -h "Content-Disposition" gs://bucket/*.html

  If you have a large number of objects to update you might want to use the
  gsutil -m option, to perform a parallel (multi-threaded/multi-processing)
  update:

    gsutil -m setmeta -h "Content-Type:text/html" \\
      -h "Cache-Control:public, max-age=3600" \\
      -h "Content-Disposition" gs://bucket/*.html

  You can also use the setmeta command to set custom metadata on an object:

    gsutil setmeta -h "x-goog-meta-icecreamflavor:vanilla" gs://bucket/object

  Custom metadata is always prefixed in gsutil with ``x-goog-meta-``. This
  distinguishes it from standard request headers. Other tools that send and
  receive object metadata by using the request body do not use this prefix.

  While gsutil supports custom metadata with arbitrary Unicode values, note
  that when setting metadata using the XML API, which sends metadata as HTTP
  headers, Unicode characters are encoded using UTF-8, then url-encoded to
  ASCII. For example:
  
    gsutil setmeta -h "x-goog-meta-foo: ã" gs://bucket/object

  stores the custom metadata key-value pair of ``foo`` and ``%C3%A3``.
  Subsequently, running ``ls -L`` using the JSON API to list the object's
  metadata prints ``%C3%A3``, while ``ls -L`` using the XML API url-decodes
  this value automatically, printing the character ``ã``.

  The setmeta command reads each object's current generation and metageneration
  and uses those as preconditions unless they are otherwise specified by
  top-level arguments. For example, the following command sets the custom
  metadata ``icecreamflavor:vanilla`` if the current live object has a
  metageneration of 2:

    gsutil -h "x-goog-if-metageneration-match:2" setmeta
      -h "x-goog-meta-icecreamflavor:vanilla"

  See `Object metadata <https://cloud.google.com/storage/docs/metadata>`_ for
  more information about object metadata.

<B>OPTIONS</B>
  -h          Specifies a header:value to be added, or header to be removed,
              from each named object.
""")

# Setmeta assumes a header-like model which doesn't line up with the JSON way
# of doing things. This list comes from functionality that was supported by
# gsutil3 at the time gsutil4 was released.
SETTABLE_FIELDS = [
    'cache-control', 'content-disposition', 'content-encoding',
    'content-language', 'content-type', 'custom-time'
]

_GCLOUD_OBJECTS_UPDATE_COMMAND = ['storage', 'objects', 'update']


def _SetMetadataExceptionHandler(cls, e):
  """Exception handler that maintains state about post-completion status."""
  cls.logger.error(e)
  cls.everything_set_okay = False


def _SetMetadataFuncWrapper(cls, name_expansion_result, thread_state=None):
  cls.SetMetadataFunc(name_expansion_result, thread_state=thread_state)


class SetMetaCommand(Command):
  """Implementation of gsutil setmeta command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'setmeta',
      command_name_aliases=['setheader'],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=constants.NO_MAX,
      supported_sub_args='h:rR',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[
          ApiSelector.XML,
          ApiSelector.JSON,
      ],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudURLsArgument(),
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='setmeta',
      help_name_aliases=['setheader'],
      help_type='command_help',
      help_one_line_summary='Set metadata on already uploaded objects',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=_GCLOUD_OBJECTS_UPDATE_COMMAND,
      flag_map={},
  )

  def get_gcloud_storage_args(self):
    recursive_flag = []
    for o, _ in self.sub_opts:
      if o in ('-r', '-R'):
        recursive_flag = ['--recursive']
        break
    clear_set, set_dict = self._ParseMetadataHeaders(
        self._GetHeaderStringsFromSubOpts())
    # Handle translation through "gcloud_command" instead of "flag_map".
    self.sub_opts = []
    clear_flags = self._translate_headers(
        {clear_key: None for clear_key in clear_set}, unset=True)
    set_flags = self._translate_headers(set_dict, unset=False)
    command = (_GCLOUD_OBJECTS_UPDATE_COMMAND + recursive_flag + clear_flags +
               set_flags)

    gcloud_storage_map = GcloudStorageMap(
        gcloud_command=command,
        flag_map={},
    )

    return super().get_gcloud_storage_args(gcloud_storage_map)

  def RunCommand(self):
    """Command entry point for the setmeta command."""
    metadata_minus, metadata_plus = self._ParseMetadataHeaders(
        self._GetHeaderStringsFromSubOpts())

    self.metadata_change = metadata_plus
    for header in metadata_minus:
      self.metadata_change[header] = ''

    if not self.metadata_change:
      raise CommandException(
          'gsutil setmeta requires one or more headers to be provided with the'
          ' -h flag. See "gsutil help setmeta" for more information.')

    if len(self.args) == 1 and not self.recursion_requested:
      url = StorageUrlFromString(self.args[0])
      if not (url.IsCloudUrl() and url.IsObject()):
        raise CommandException('URL (%s) must name an object' % self.args[0])

    # Used to track if any objects' metadata failed to be set.
    self.everything_set_okay = True

    self.preconditions = PreconditionsFromHeaders(self.headers)

    name_expansion_iterator = NameExpansionIterator(
        self.command_name,
        self.debug,
        self.logger,
        self.gsutil_api,
        self.args,
        self.recursion_requested,
        all_versions=self.all_versions,
        continue_on_error=self.parallel_operations,
        bucket_listing_fields=['generation', 'metadata', 'metageneration'])

    seek_ahead_iterator = SeekAheadNameExpansionIterator(
        self.command_name,
        self.debug,
        self.GetSeekAheadGsutilApi(),
        self.args,
        self.recursion_requested,
        all_versions=self.all_versions,
        project_id=self.project_id)

    try:
      # Perform requests in parallel (-m) mode, if requested, using
      # configured number of parallel processes and threads. Otherwise,
      # perform requests with sequential function calls in current process.
      self.Apply(_SetMetadataFuncWrapper,
                 name_expansion_iterator,
                 _SetMetadataExceptionHandler,
                 fail_on_error=True,
                 seek_ahead_iterator=seek_ahead_iterator)
    except AccessDeniedException as e:
      if e.status == 403:
        self._WarnServiceAccounts()
      raise

    if not self.everything_set_okay:
      raise CommandException('Metadata for some objects could not be set.')

    return 0

  @Retry(PreconditionException, tries=3, timeout_secs=1)
  def SetMetadataFunc(self, name_expansion_result, thread_state=None):
    """Sets metadata on an object.

    Args:
      name_expansion_result: NameExpansionResult describing target object.
      thread_state: gsutil Cloud API instance to use for the operation.
    """
    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    exp_src_url = name_expansion_result.expanded_storage_url
    self.logger.info('Setting metadata on %s...', exp_src_url)

    cloud_obj_metadata = encoding.JsonToMessage(
        apitools_messages.Object, name_expansion_result.expanded_result)

    preconditions = Preconditions(
        gen_match=self.preconditions.gen_match,
        meta_gen_match=self.preconditions.meta_gen_match)
    if preconditions.gen_match is None:
      preconditions.gen_match = cloud_obj_metadata.generation
    if preconditions.meta_gen_match is None:
      preconditions.meta_gen_match = cloud_obj_metadata.metageneration

    # Patch handles the patch semantics for most metadata, but we need to
    # merge the custom metadata field manually.
    patch_obj_metadata = ObjectMetadataFromHeaders(self.metadata_change)

    api = gsutil_api.GetApiSelector(provider=exp_src_url.scheme)
    # For XML we only want to patch through custom metadata that has
    # changed.  For JSON we need to build the complete set.
    if api == ApiSelector.XML:
      pass
    elif api == ApiSelector.JSON:
      CopyObjectMetadata(patch_obj_metadata, cloud_obj_metadata, override=True)
      patch_obj_metadata = cloud_obj_metadata
      # Patch body does not need the object generation and metageneration.
      patch_obj_metadata.generation = None
      patch_obj_metadata.metageneration = None

    gsutil_api.PatchObjectMetadata(exp_src_url.bucket_name,
                                   exp_src_url.object_name,
                                   patch_obj_metadata,
                                   generation=exp_src_url.generation,
                                   preconditions=preconditions,
                                   provider=exp_src_url.scheme,
                                   fields=['id'])
    _PutToQueueWithTimeout(gsutil_api.status_queue,
                           MetadataMessage(message_time=time.time()))

  def _GetHeaderStringsFromSubOpts(self):
    """Gets header values from after the "setmeta" part of the command.

    Example: $ gsutil -h not:parsed setmeta is:parsed gs://bucket/object
               -> ["is:parsed"]

    Returns:
      List[str]: Headers without the "-h" but not yet split on colons.

    Raises:
      CommandException Found canned ACL.
    """
    if not self.sub_opts:
      return []
    headers = []
    for o, a in self.sub_opts:
      if o == '-h':
        if 'x-goog-acl' in a or 'x-amz-acl' in a:
          raise CommandException(
              'gsutil setmeta no longer allows canned ACLs. Use gsutil acl '
              'set ... to set canned ACLs.')
        headers.append(a)
    return headers

  def _ParseMetadataHeaders(self, headers):
    """Validates and parses metadata changes from the headers argument.

    Args:
      headers: Header dict to validate and parse.

    Returns:
      (metadata_plus, metadata_minus): Tuple of header sets to add and remove.
    """
    metadata_minus = set()
    cust_metadata_minus = set()
    metadata_plus = {}
    cust_metadata_plus = {}
    # Build a count of the keys encountered from each plus and minus arg so we
    # can check for dupe field specs.
    num_metadata_plus_elems = 0
    num_cust_metadata_plus_elems = 0
    num_metadata_minus_elems = 0
    num_cust_metadata_minus_elems = 0

    for md_arg in headers:
      # Use partition rather than split, as we should treat all characters past
      # the initial : as part of the header's value.
      parts = md_arg.partition(':')
      (header, _, value) = parts
      InsistAsciiHeader(header)

      # Translate headers to lowercase to match the casing assumed by our
      # sanity-checking operations.
      lowercase_header = header.lower()
      # This check is overly simple; it would be stronger to check, for each
      # URL argument, whether the header starts with the provider
      # metadata_prefix, but here we just parse the spec once, before
      # processing any of the URLs. This means we will not detect if the user
      # tries to set an x-goog-meta- field on an another provider's object,
      # for example.
      is_custom_meta = IsCustomMetadataHeader(lowercase_header)
      if not is_custom_meta and lowercase_header not in SETTABLE_FIELDS:
        raise CommandException(
            'Invalid or disallowed header (%s).\nOnly these fields (plus '
            'x-goog-meta-* fields) can be set or unset:\n%s' %
            (header, sorted(list(SETTABLE_FIELDS))))

      if value:
        if is_custom_meta:
          # Allow non-ASCII data for custom metadata fields.
          cust_metadata_plus[header] = value
          num_cust_metadata_plus_elems += 1
        else:
          # Don't unicode encode other fields because that would perturb their
          # content (e.g., adding %2F's into the middle of a Cache-Control
          # value).
          InsistAsciiHeaderValue(header, value)
          value = str(value)
          metadata_plus[lowercase_header] = value
          num_metadata_plus_elems += 1
      else:
        if is_custom_meta:
          cust_metadata_minus.add(header)
          num_cust_metadata_minus_elems += 1
        else:
          metadata_minus.add(lowercase_header)
          num_metadata_minus_elems += 1

    if (num_metadata_plus_elems != len(metadata_plus) or
        num_cust_metadata_plus_elems != len(cust_metadata_plus) or
        num_metadata_minus_elems != len(metadata_minus) or
        num_cust_metadata_minus_elems != len(cust_metadata_minus) or
        metadata_minus.intersection(set(metadata_plus.keys()))):
      raise CommandException('Each header must appear at most once.')

    metadata_plus.update(cust_metadata_plus)
    metadata_minus.update(cust_metadata_minus)
    return (metadata_minus, metadata_plus)
