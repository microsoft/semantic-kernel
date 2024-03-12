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
"""List event types available to Google Cloud Functions v1."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import triggers


def Run(args):
  """Lists GCF v1 available event_types.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Yields:
    events: List[v1.TriggerEvent], The list of v1 supported event types.
  """
  del args

  for provider in triggers.TRIGGER_PROVIDER_REGISTRY.providers:
    for event in provider.events:
      yield event
