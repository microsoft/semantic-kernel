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
"""The deployments command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Deployments(base.Group):
  """Manage deployments of Apigee API proxies in runtime environments."""

  detailed_help = {
      "DESCRIPTION": """
          {description}

          `{command}` contains commands for enumerating and checking the status
          of deployments of proxies to runtime environments.
          """,
      "EXAMPLES": """
          To list all deployments for the active Cloud Platform project, run:

              $ {command} list

          To list all deployments in a particular environment of a particular
          Apigee organization, run:

              $ {command} list --environment=ENVIRONMENT --organization=ORG_NAME

          To get the status of a specific deployment as a JSON object, run:

              $ {command} describe --api=API_NAME --environment=ENVIRONMENT --format=json
      """,
  }

