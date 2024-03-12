# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Flags for OS Login subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core.util import files


def AddKeyFlags(parser, action, additional_help=''):
  """Adds --key and --key-file flags to oslogin commands."""
  key_arg = parser.add_mutually_exclusive_group(required=True)

  key_arg.add_argument(
      '--key',
      help="""\
          The SSH public key to {0} the OS Login Profile.{1}
          """.format(action, additional_help))

  key_arg.add_argument(
      '--key-file',
      help="""\
          The path to a file containing an SSH public key to {0} the
          OS Login Profile.{1}
          """.format(action, additional_help))


def AddTtlFlag(parser, required=False):
  parser.add_argument(
      '--ttl',
      type=arg_parsers.Duration(),
      required=required,
      help="""\
          The amount of time before the SSH key expires. For example,
          specifying ``30m'' will set the expiration time on the SSH key for
          30 minutes from the current time. A value of 0 will result in no
          expiration time.
          See $ gcloud topic datetimes for information on duration formats.
          """)


def GetKeyFromArgs(args):
  if args.key_file:
    key = files.ReadFileContents(args.key_file)
  else:
    key = args.key

  return key
