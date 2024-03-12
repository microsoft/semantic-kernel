# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Implementation of rb command for deleting cloud storage buckets."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.cloud_api import NotEmptyException
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.storage_url import StorageUrlFromString
from gslib.utils.constants import NO_MAX
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap

_SYNOPSIS = """
  gsutil rb [-f] gs://<bucket_name>...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  Delete one or more buckets. Buckets must be empty before you can delete them.

  Be certain you want to delete a bucket before you do so, as once it is
  deleted the name becomes available and another user may create a bucket with
  that name. (But see also "DOMAIN NAMED BUCKETS" under "gsutil help naming"
  for help carving out parts of the bucket name space.)


<B>OPTIONS</B>
  -f          Continues silently (without printing error messages) despite
              errors when removing buckets. If some buckets couldn't be removed,
              gsutil's exit status will be non-zero even if this flag is set.
              If no buckets could be removed, the command raises a
              "no matches" error.
""")


class RbCommand(Command):
  """Implementation of gsutil rb command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'rb',
      command_name_aliases=[
          'deletebucket',
          'removebucket',
          'removebuckets',
          'rmdir',
      ],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=NO_MAX,
      supported_sub_args='f',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[
          ApiSelector.XML,
          ApiSelector.JSON,
      ],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='rb',
      help_name_aliases=[
          'deletebucket',
          'removebucket',
          'removebuckets',
          'rmdir',
      ],
      help_type='command_help',
      help_one_line_summary='Remove buckets',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'buckets', 'delete'],
      flag_map={
          '-f': GcloudStorageFlag('--continue-on-error'),
      },
  )

  def RunCommand(self):
    """Command entry point for the rb command."""
    self.continue_on_error = False
    if self.sub_opts:
      for o, unused_a in self.sub_opts:
        if o == '-f':
          self.continue_on_error = True

    did_some_work = False
    some_failed = False
    for url_str in self.args:
      wildcard_url = StorageUrlFromString(url_str)
      if wildcard_url.IsObject():
        raise CommandException('"rb" command requires a provider or '
                               'bucket URL')
      # Wrap WildcardIterator call in try/except so we can avoid printing errors
      # with -f option if a non-existent URL listed, permission denial happens
      # while listing, etc.
      try:
        # Materialize iterator results into a list to catch exceptions.
        # Since this is listing buckets this list shouldn't be too large to fit
        # in memory at once.
        # Also, avoid listing all fields to avoid performing unnecessary bucket
        # metadata GETs. These would also be problematic when billing is
        # disabled, as deletes are allowed but GetBucket is not.
        blrs = list(
            self.WildcardIterator(url_str).IterBuckets(bucket_fields=['id']))
      except:  # pylint: disable=bare-except
        some_failed = True
        if self.continue_on_error:
          continue
        else:
          raise
      for blr in blrs:
        url = blr.storage_url
        self.logger.info('Removing %s...', url)
        try:
          self.gsutil_api.DeleteBucket(url.bucket_name, provider=url.scheme)
        except NotEmptyException as e:
          some_failed = True
          if self.continue_on_error:
            continue
          elif 'VersionedBucketNotEmpty' in e.reason:
            raise CommandException('Bucket is not empty. Note: this is a '
                                   'versioned bucket, so to delete all '
                                   'objects\nyou need to use:'
                                   '\n\tgsutil rm -r %s' % url)
          else:
            raise
        except:  # pylint: disable=bare-except
          some_failed = True
          if not self.continue_on_error:
            raise
        did_some_work = True
    if not did_some_work:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(self.args))
    return 1 if some_failed else 0
