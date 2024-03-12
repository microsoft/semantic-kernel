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
"""The developers command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Developers(base.Group):
  """Manage Apigee developers."""

  detailed_help = {
      "DESCRIPTION": """
          {description}

          `{command}` manages developers that want to use APIs exposed via
          Apigee in their applications.
          """,
      "EXAMPLES": """
          To list the email addresses of all the developers in the active Cloud
          Platform project, run:

              $ {command} list

          To get that list as a JSON array and only include developers with
          ``example.com'' addresses, run:

              $ {command} list --format=json --filter="email:(@example.com)"

          To get details about a specific developer in the active Cloud Platform
          project, run:

              $ {command} describe DEVELOPER_EMAIL
      """,
  }
