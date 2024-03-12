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
"""Cloud Pub/Sub subscriptions list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.pubsub import subscriptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import properties


def _Run(args, legacy_output=False):
  client = subscriptions.SubscriptionsClient()
  for sub in client.List(util.ParseProject(), page_size=args.page_size):
    if legacy_output:
      sub = util.ListSubscriptionDisplayDict(sub)
    yield sub


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists Cloud Pub/Sub subscriptions."""

  detailed_help = {
      'DESCRIPTION': 'Lists all of the Cloud Pub/Sub subscriptions that exist '
                     'in a given project.'
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddUriFunc(util.SubscriptionUriFunc)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListBeta(List):
  """Lists Cloud Pub/Sub subscriptions."""

  def Run(self, args):
    legacy_output = properties.VALUES.pubsub.legacy_output.GetBool()
    return _Run(args, legacy_output=legacy_output)
