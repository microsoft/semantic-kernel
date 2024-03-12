# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of Unix-like cat command for cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks.cat import cat_task_iterator


def _range_parser(string_value):
  """Creates Range object out of given string value.

  Args:
    string_value (str): The range the user entered.

  Returns:
    Range(int, int|None): The Range object from the given string value.
  """
  if string_value == '-':
    return arg_parsers.Range(start=0, end=None)
  range_start, _, range_end = string_value.partition('-')
  if not range_start:
    # Checking to see if the user entered -y for the range.
    return arg_parsers.Range(start=-1 * int(range_end), end=None)
  if not range_end:
    # Checking to see if the user entered x- for the range.
    return arg_parsers.Range(start=int(range_start), end=None)
  return arg_parsers.Range.Parse(string_value)


class Cat(base.Command):
  """Outputs the contents of one or more URLs to stdout."""

  detailed_help = {
      'DESCRIPTION':
          """
      The cat command outputs the contents of one or more URLs to stdout. While
      the cat command does not compute a checksum, it is otherwise equivalent to
      doing:

        $ {parent_command} cp url... -

      (The final '-' causes gcloud to stream the output to stdout.)
      """,
      'EXAMPLES':
          """

      The following command writes all text files in a bucket to stdout:

        $ {command} gs://bucket/*.txt

      The following command outputs a short header describing file.txt, along
      with its contents:

        $ {command} -d gs://my-bucket/file.txt

      The following command outputs bytes 256-939 of file.txt:

        $ {command} -r 256-939 gs://my-bucket/file.txt

      The following command outputs the last 5 bytes of file.txt:

        $ {command} -r -5 gs://my-bucket/file.txt

      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument('url', nargs='+', help='The url of objects to list.')
    parser.add_argument(
        '-d',
        '--display-url',
        action='store_true',
        help='Prints the header before each object.')
    parser.add_argument(
        '-r',
        '--range',
        type=_range_parser,
        help=textwrap.dedent("""\
            Causes gcloud storage to output just the specified byte range of
            the object. In a case where "start" = 'x', and "end" = 'y',
            ranges take the form:
            `x-y` (e.g., `-r 256-5939`), `x-` (e.g., `-r 256-`),
            `-y` (e.g., `-r -5`)

            When offsets start at 0, x-y means to return bytes x
            through y (inclusive), x- means to return bytes x through
            the end of the object, and -y changes the role of y.
            If -y is present, then it returns the last y bytes of the object.

            If the bytes are out of range of the object,
            then nothing is printed"""))

    flags.add_additional_headers_flag(parser)
    flags.add_encryption_flags(parser, command_only_reads_data=True)

  def Run(self, args):
    encryption_util.initialize_key_store(args)
    if args.url:
      storage_urls = []
      for url_string in args.url:
        url_object = storage_url.storage_url_from_string(url_string)
        if not isinstance(url_object, storage_url.CloudUrl):
          raise errors.InvalidUrlError('cat only works for valid cloud URLs.'
                                       ' {} is an invalid cloud URL.'.format(
                                           url_object.url_string))
        storage_urls.append(url_object)

    # Not using "FieldsScope.SHORT" because downloads always expect
    # serialization data for recovering from errors, which requires
    # the "GCS mediaLink" API field.
    source_expansion_iterator = name_expansion.NameExpansionIterator(
        args.url,
        fields_scope=cloud_api.FieldsScope.NO_ACL,
        recursion_requested=name_expansion.RecursionSetting.NO)

    task_iterator = cat_task_iterator.get_cat_task_iterator(
        source_expansion_iterator,
        args.display_url,
        start_byte=getattr(args.range, 'start', 0),
        end_byte=getattr(args.range, 'end', None))
    self.exit_code = task_executor.execute_tasks(task_iterator=task_iterator)
