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
"""The apis command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Apis(base.Group):
  """Manage Apigee API proxies."""
  detailed_help = {
      "EXAMPLES": """
          To list all the API proxies in the active Cloud Platform project, run:

              $ {command} list

          To get details about a specific API proxy in a specific Apigee
          organization, run:

              $ {command} describe PROXY_NAME --organization=ORG_NAME

          To get a JSON object containing revision-level details about an API
          proxy, run:

              $ {command} describe PROXY_NAME --verbose --format=json

          To deploy the most recent revision of an API proxy into the ``eval''
          deployment environment, run:

              $ {command} deploy --api=PROXY_NAME --environment=eval

          To deploy the first revision of that API proxy into the ``release''
          deployment environment, run:

              $ {command} deploy 1 --api=PROXY_NAME --environment=release

          To undeploy whatever revision of PROXY_NAME is currently deployed in
          ENVIRONMENT, run:

              $ {command} undeploy --api=PROXY_NAME --environment=ENVIRONMENT
      """,
  }
