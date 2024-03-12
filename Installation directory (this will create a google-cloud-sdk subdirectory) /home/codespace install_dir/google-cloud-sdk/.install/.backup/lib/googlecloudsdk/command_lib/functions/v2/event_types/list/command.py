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
"""List event types available to Google Cloud Functions v2."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import providers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.eventarc.types import EventType
from googlecloudsdk.core import properties


def Run(args, release_track):
  """Lists GCF v2 available event_types.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    release_track: base.ReleaseTrack, The release track (ga, beta, alpha)

  Returns:
    event_types: List[EventType], The list of supported event types.
  """
  del release_track

  client = providers.ProvidersClient(base.ReleaseTrack.GA)
  project = args.project or properties.VALUES.core.project.GetOrFail()
  provider_list = client.List(
      'projects/{}/locations/-'.format(project), limit=None, page_size=None)

  event_types = {}
  for p in provider_list:
    for t in p.eventTypes:
      name = t.type
      description = '{}: {}'.format(p.displayName, t.description)
      attributes = ','.join(fa.attribute for fa in t.filteringAttributes)
      if name not in event_types:
        event_types[name] = EventType(name, description, attributes)

  return [v for k, v in event_types.items()]
