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

"""A command that describes a registered gcloud API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta.apis import flags
from googlecloudsdk.core import properties


ENFORCE_COLLECTION_FLAG = base.Argument(
    '--enforce-collection',
    action='store_true',
    default=True,
    help='Fail unless resource belongs to specified collection. '
         'This is applicable only if method being called is GET or DELETE '
         'and resource identifier is URL.')


class Call(base.Command):
  """Calls an API method with specific parameters."""

  @staticmethod
  def Args(parser):
    flags.API_VERSION_FLAG.AddToParser(parser)
    flags.COLLECTION_FLAG.AddToParser(parser)
    ENFORCE_COLLECTION_FLAG.AddToParser(parser)
    flags.RAW_FLAG.AddToParser(parser)
    parser.AddDynamicPositional(
        'method',
        action=flags.MethodDynamicPositionalAction,
        help='The name of the API method to invoke.')

  def Run(self, args):
    properties.VALUES.core.enable_gri.Set(True)
    response = args.method.Call()
    return response
