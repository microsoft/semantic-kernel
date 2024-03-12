# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Implementation of label command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import codecs
import json
import os

import six

from gslib import metrics
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import Preconditions
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.help_provider import CreateHelpText
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import shim_util
from gslib.utils.constants import NO_MAX
from gslib.utils.constants import UTF8
from gslib.utils.retry_util import Retry
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.translation_helper import LabelTranslation

_SET_SYNOPSIS = """
  gsutil label set <label-json-file> gs://<bucket_name>...
"""

_GET_SYNOPSIS = """
  gsutil label get gs://<bucket_name>
"""

_CH_SYNOPSIS = """
  gsutil label ch <label_modifier>... gs://<bucket_name>...

  where each <label_modifier> is one of the following forms:

    -l <key>:<value>
    -d <key>
"""

_GET_DESCRIPTION = """
<B>GET</B>
  The "label get" command gets the `labels
  <https://cloud.google.com/storage/docs/tags-and-labels#bucket-labels>`_
  applied to a bucket, which you can save and edit for use with the "label set"
  command.
"""

_SET_DESCRIPTION = """
<B>SET</B>
  The "label set" command allows you to set the labels on one or more
  buckets. You can retrieve a bucket's labels using the "label get" command,
  save the output to a file, edit the file, and then use the "label set"
  command to apply those labels to the specified bucket(s). For
  example:

    gsutil label get gs://bucket > labels.json

  Make changes to labels.json, such as adding an additional label, then:

    gsutil label set labels.json gs://example-bucket

  Note that you can set these labels on multiple buckets at once:

    gsutil label set labels.json gs://bucket-foo gs://bucket-bar
"""

_CH_DESCRIPTION = """
<B>CH</B>
  The "label ch" command updates a bucket's label configuration, applying the
  label changes specified by the -l and -d flags. You can specify multiple
  label changes in a single command run; all changes will be made atomically to
  each bucket.

<B>CH EXAMPLES</B>
  Examples for "ch" sub-command:

  Add the label "key-foo:value-bar" to the bucket "example-bucket":

    gsutil label ch -l key-foo:value-bar gs://example-bucket

  Change the above label to have a new value:

    gsutil label ch -l key-foo:other-value gs://example-bucket

  Add a new label and delete the old one from above:

    gsutil label ch -l new-key:new-value -d key-foo gs://example-bucket

<B>CH OPTIONS</B>
  The "ch" sub-command has the following options

  -l          Add or update a label with the specified key and value.

  -d          Remove the label with the specified key.
"""

_SYNOPSIS = (_SET_SYNOPSIS + _GET_SYNOPSIS.lstrip('\n') +
             _CH_SYNOPSIS.lstrip('\n') + '\n\n')

_DESCRIPTION = """
  Gets, sets, or changes the label configuration (also called the tagging
  configuration by other storage providers) of one or more buckets. An example
  label JSON document looks like the following:

    {
      "your_label_key": "your_label_value",
      "your_other_label_key": "your_other_label_value"
    }

  The label command has three sub-commands:
""" + _GET_DESCRIPTION + _SET_DESCRIPTION + _CH_DESCRIPTION

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(_GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(_SET_SYNOPSIS, _SET_DESCRIPTION)
_ch_help_text = CreateHelpText(_CH_SYNOPSIS, _CH_DESCRIPTION)


class LabelCommand(Command):
  """Implementation of gsutil label command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'label',
      usage_synopsis=_SYNOPSIS,
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='l:d:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'set': [
              CommandArgument.MakeNFileURLsArgument(1),
              CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),
          ],
          'get': [CommandArgument.MakeNCloudURLsArgument(1),],
          'ch': [CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument(),],
      },
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='label',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary=(
          'Get, set, or change the label configuration of a bucket.'),
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text,
          'set': _set_help_text,
          'ch': _ch_help_text,
      },
  )

  gcloud_storage_map = GcloudStorageMap(gcloud_command={
      'get':
          GcloudStorageMap(
              gcloud_command=[
                  'storage', 'buckets', 'describe',
                  '--format="gsutiljson[key=labels,empty=\' has no label '
                  'configuration.\',empty_prefix_key=storage_url]"', '--raw'
              ],
              flag_map={},
          ),
      'set':
          GcloudStorageMap(
              gcloud_command=['storage', 'buckets', 'update', '--labels-file'],
              flag_map={},
          ),
      'ch':
          GcloudStorageMap(
              gcloud_command=['storage', 'buckets', 'update'],
              flag_map={
                  '-d':
                      GcloudStorageFlag(
                          '--remove-labels',
                          repeat_type=shim_util.RepeatFlagType.LIST),
                  '-l':
                      GcloudStorageFlag(
                          '--update-labels',
                          repeat_type=shim_util.RepeatFlagType.DICT),
              },
          ),
  },
                                        flag_map={})

  def _CalculateUrlsStartArg(self):
    if not self.args:
      self.RaiseWrongNumberOfArgumentsException()
    if self.args[0].lower() == 'set':
      return 2  # Filename comes before bucket arg(s).
    return 1

  def _SetLabel(self):
    """Parses options and sets labels on the specified buckets."""
    # At this point, "set" has been popped off the front of self.args.
    if len(self.args) < 2:
      self.RaiseWrongNumberOfArgumentsException()

    label_filename = self.args[0]
    if not os.path.isfile(label_filename):
      raise CommandException('Could not find the file "%s".' % label_filename)
    with codecs.open(label_filename, 'r', UTF8) as label_file:
      label_text = label_file.read()

    @Retry(PreconditionException, tries=3, timeout_secs=1)
    def _SetLabelForBucket(blr):
      url = blr.storage_url
      self.logger.info('Setting label configuration on %s...', blr)

      if url.scheme == 's3':  # Uses only XML.
        self.gsutil_api.XmlPassThroughSetTagging(label_text,
                                                 url,
                                                 provider=url.scheme)
      else:  # Must be a 'gs://' bucket.
        labels_message = None
        # When performing a read-modify-write cycle, include metageneration to
        # avoid race conditions (supported for GS buckets only).
        metageneration = None
        new_label_json = json.loads(label_text)
        if (self.gsutil_api.GetApiSelector(url.scheme) == ApiSelector.JSON):
          # Perform a read-modify-write so that we can specify which
          # existing labels need to be deleted.
          _, bucket_metadata = self.GetSingleBucketUrlFromArg(
              url.url_string, bucket_fields=['labels', 'metageneration'])
          metageneration = bucket_metadata.metageneration
          label_json = {}
          if bucket_metadata.labels:
            label_json = json.loads(
                LabelTranslation.JsonFromMessage(bucket_metadata.labels))
          # Set all old keys' values to None; this will delete each key that
          # is not included in the new set of labels.
          merged_labels = dict(
              (key, None) for key, _ in six.iteritems(label_json))
          merged_labels.update(new_label_json)
          labels_message = LabelTranslation.DictToMessage(merged_labels)
        else:  # ApiSelector.XML
          # No need to read-modify-write with the XML API.
          labels_message = LabelTranslation.DictToMessage(new_label_json)

        preconditions = Preconditions(meta_gen_match=metageneration)
        bucket_metadata = apitools_messages.Bucket(labels=labels_message)
        self.gsutil_api.PatchBucket(url.bucket_name,
                                    bucket_metadata,
                                    preconditions=preconditions,
                                    provider=url.scheme,
                                    fields=['id'])

    some_matched = False
    url_args = self.args[1:]
    for url_str in url_args:
      # Throws a CommandException if the argument is not a bucket.
      bucket_iter = self.GetBucketUrlIterFromArg(url_str, bucket_fields=['id'])
      for bucket_listing_ref in bucket_iter:
        some_matched = True
        _SetLabelForBucket(bucket_listing_ref)

    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def _ChLabel(self):
    """Parses options and changes labels on the specified buckets."""
    self.label_changes = {}
    self.num_deletions = 0

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-l':
          label_split = a.split(':')
          if len(label_split) != 2:
            raise CommandException(
                'Found incorrectly formatted option for "gsutil label ch": '
                '"%s". To add a label, please use the form <key>:<value>.' % a)
          self.label_changes[label_split[0]] = label_split[1]
        elif o == '-d':
          # Ensure only the key is supplied; stop if key:value was given.
          val_split = a.split(':')
          if len(val_split) != 1:
            raise CommandException(
                'Found incorrectly formatted option for "gsutil label ch": '
                '"%s". To delete a label, provide only its key.' % a)
          self.label_changes[a] = None
          self.num_deletions += 1
        else:
          self.RaiseInvalidArgumentException()
    if not self.label_changes:
      raise CommandException(
          'Please specify at least one label change with the -l or -d flags.')

    @Retry(PreconditionException, tries=3, timeout_secs=1)
    def _ChLabelForBucket(blr):
      url = blr.storage_url
      self.logger.info('Setting label configuration on %s...', blr)

      labels_message = None
      # When performing a read-modify-write cycle, include metageneration to
      # avoid race conditions (supported for GS buckets only).
      metageneration = None
      if (self.gsutil_api.GetApiSelector(url.scheme) == ApiSelector.JSON):
        # The JSON API's PATCH semantics allow us to skip read-modify-write,
        # with the exception of one edge case - attempting to delete a
        # nonexistent label returns an error iff no labels previously existed
        corrected_changes = self.label_changes
        if self.num_deletions:
          (_, bucket_metadata) = self.GetSingleBucketUrlFromArg(
              url.url_string, bucket_fields=['labels', 'metageneration'])
          if not bucket_metadata.labels:
            metageneration = bucket_metadata.metageneration
            # Remove each change that would try to delete a nonexistent key.
            corrected_changes = dict(
                (k, v) for k, v in six.iteritems(self.label_changes) if v)
        labels_message = LabelTranslation.DictToMessage(corrected_changes)
      else:  # ApiSelector.XML
        # Perform a read-modify-write cycle so that we can specify which
        # existing labels need to be deleted.
        (_, bucket_metadata) = self.GetSingleBucketUrlFromArg(
            url.url_string, bucket_fields=['labels', 'metageneration'])
        metageneration = bucket_metadata.metageneration

        label_json = {}
        if bucket_metadata.labels:
          label_json = json.loads(
              LabelTranslation.JsonFromMessage(bucket_metadata.labels))
        # Modify label_json such that all specified labels are added
        # (overwriting old labels if necessary) and all specified deletions
        # are removed from label_json if already present.
        for key, value in six.iteritems(self.label_changes):
          if not value and key in label_json:
            del label_json[key]
          else:
            label_json[key] = value
        labels_message = LabelTranslation.DictToMessage(label_json)

      preconditions = Preconditions(meta_gen_match=metageneration)
      bucket_metadata = apitools_messages.Bucket(labels=labels_message)
      self.gsutil_api.PatchBucket(url.bucket_name,
                                  bucket_metadata,
                                  preconditions=preconditions,
                                  provider=url.scheme,
                                  fields=['id'])

    some_matched = False
    url_args = self.args
    if not url_args:
      self.RaiseWrongNumberOfArgumentsException()
    for url_str in url_args:
      # Throws a CommandException if the argument is not a bucket.
      bucket_iter = self.GetBucketUrlIterFromArg(url_str)
      for bucket_listing_ref in bucket_iter:
        some_matched = True
        _ChLabelForBucket(bucket_listing_ref)

    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))

  def _GetAndPrintLabel(self, bucket_arg):
    """Gets and prints the labels for a cloud bucket."""
    bucket_url, bucket_metadata = self.GetSingleBucketUrlFromArg(
        bucket_arg, bucket_fields=['labels'])
    if bucket_url.scheme == 's3':
      print((self.gsutil_api.XmlPassThroughGetTagging(
          bucket_url, provider=bucket_url.scheme)))
    else:
      if bucket_metadata.labels:
        print((LabelTranslation.JsonFromMessage(bucket_metadata.labels,
                                                pretty_print=True)))
      else:
        print(('%s has no label configuration.' % bucket_url))

  def RunCommand(self):
    """Command entry point for the label command."""
    action_subcommand = self.args.pop(0)
    self.ParseSubOpts(check_args=True)

    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    metrics.LogCommandParams(sub_opts=self.sub_opts)
    if action_subcommand == 'get':
      metrics.LogCommandParams(subcommands=[action_subcommand])
      self._GetAndPrintLabel(self.args[0])
    elif action_subcommand == 'set':
      metrics.LogCommandParams(subcommands=[action_subcommand])
      self._SetLabel()
    elif action_subcommand == 'ch':
      metrics.LogCommandParams(subcommands=[action_subcommand])
      self._ChLabel()
    else:
      raise CommandException(
          'Invalid subcommand "%s" for the %s command.\nSee "gsutil help %s".' %
          (action_subcommand, self.command_name, self.command_name))
    return 0
