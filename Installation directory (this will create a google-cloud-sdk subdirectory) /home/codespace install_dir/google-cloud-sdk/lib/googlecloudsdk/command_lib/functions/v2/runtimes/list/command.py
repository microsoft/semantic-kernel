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
"""List runtimes available to Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.functions.v2 import client
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def Run(args, release_track):
  """Lists GCF runtimes available with the given args from the v2 API.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    release_track: base.ReleaseTrack, The release track (ga, beta, alpha)

  Returns:
    List[Runtime], List of available GCF runtimes
  """
  del args
  if not properties.VALUES.functions.region.IsExplicitlySet():
    log.status.Print('Suggest using `--region us-west1`')
  region = properties.VALUES.functions.region.Get()

  gcf_client = client.FunctionsClient(release_track=release_track)

  # ListRuntimesResponse
  response = gcf_client.ListRuntimes(region)

  if response:
    runtime_mapping = collections.OrderedDict()
    for runtime in response.runtimes:
      runtime_mapping.setdefault(runtime.name, []).append(runtime)

    return [Runtime(value) for value in runtime_mapping.values()]
  else:
    return []


class Runtime:
  """Runtimes wrapper for ListRuntimesResponse#Runtimes.

  The runtimes response from GCFv2 duplicates runtimes for each environment. To
  make formatting easier, this includes all environments under a single object.

  Attributes:
    name: A string name of the runtime.
    stage: An enum of the release state of the runtime, e.g., GA, BETA, etc.
    environments: A list of supported runtimes, [GEN_1, GEN_2]
  """

  def __init__(self, runtimes):
    for runtime in runtimes:
      if runtime.name != runtimes[0].name:
        raise ValueError('Only runtimes with the same name should be included')

    self.name = runtimes[0].name if runtimes else ''
    self.stage = runtimes[0].stage if runtimes else ''
    self.environments = [runtime.environment for runtime in runtimes]

