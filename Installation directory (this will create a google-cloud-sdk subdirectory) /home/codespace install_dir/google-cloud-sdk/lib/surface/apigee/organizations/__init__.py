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
"""The organizations command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Organizations(base.Group):
  """Manage Apigee organizations."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` contains commands for managing Apigee organizations, the
  highest-level grouping of Apigee objects. All API proxies, environments, and
  so forth each belong to one organization.

  Apigee organizations are distinct from Cloud Platform organizations, being
  more similar to Cloud Platform projects in scope and purpose.
          """,
      "EXAMPLES":
          """\
  To list all accessible organizations and their associated Cloud Platform projects, run:

      $ {command} list

  To get a JSON array of all organizations whose Cloud Platform project names
  contain the word ``sandbox'', run:

      $ {command} list --format=json --filter="project:(sandbox)"
  """}
