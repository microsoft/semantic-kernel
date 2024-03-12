# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""A command that describes a message from a given API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.meta.apis import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import registry


class Describe(base.DescribeCommand):
  """Describe the details of a proto message in an API."""

  @staticmethod
  def Args(parser):
    flags.API_REQUIRED_FLAG.AddToParser(parser)
    flags.API_VERSION_FLAG.AddToParser(parser)
    parser.add_argument(
        'message',
        help='The name of the message you want to describe.')

  def Run(self, args):
    api = registry.GetAPI(args.api, api_version=args.api_version)
    try:
      message = getattr(api.GetMessagesModule(), args.message)
      return arg_utils.GetRecursiveMessageSpec(message)
    except AttributeError:
      raise exceptions.InvalidArgumentException(
          'message', 'Message [{}] does not exist for API [{}]'.format(
              args.message, args.api))

