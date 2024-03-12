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
"""List regions available to Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import client


def Run(args, release_track):
  """Lists GCF gen2 regions available with the given args.

  Args:
    args: argparse.Namespace, All the arguments that were provided to this
      command invocation.
    release_track: base.ReleaseTrack, The release track (ga, beta, alpha)

  Returns:
    Iterable[cloudfunctions_v2alpha.Location], Generator of available GCF gen2
      regions.
  """
  del args  # unused by list command
  return client.FunctionsClient(release_track).ListRegions()
