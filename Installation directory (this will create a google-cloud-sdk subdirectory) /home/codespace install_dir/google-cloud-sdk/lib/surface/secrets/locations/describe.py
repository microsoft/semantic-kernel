# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Describe a location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args


class Describe(base.DescribeCommand):
  r"""Describe a location.

  Describe a location available for storing secrets.

  ## EXAMPLES

  Describe the location 'us-central1':

    $ {command} us-central1
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddLocation(
        parser, purpose='to describe', positional=True, required=True)

  def Run(self, args):
    location_ref = args.CONCEPTS.location.Parse()
    return secrets_api.Locations().Get(location_ref)
