# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""The command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Apigee(base.Group):
  """Manage Apigee resources.

  Commands for managing Google Cloud Apigee resources.
  """

  category = base.API_PLATFORM_AND_ECOSYSTEMS_CATEGORY

  detailed_help = {
      "DESCRIPTION": "Manage Apigee resources.",
      "EXAMPLES":
          """
          To list API proxies in the active Cloud Platform project, run:

            $ {command} apis list

          To deploy an API proxy named ``hello-world'' to the ``test''
          environment, run:

            $ {command} apis deploy --environment=test --api=hello-world

          To get the status of that deployment, run:

            $ {command} deployments describe --environment=test --api=hello-world

          To undeploy that API proxy, run:

            $ {command} apis undeploy --environment=test --api=hello-world
          """
  }

  def Filter(self, context, args):
    # TODO(b/190525329):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
