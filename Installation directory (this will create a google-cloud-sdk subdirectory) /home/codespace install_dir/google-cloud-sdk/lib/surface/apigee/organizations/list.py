# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command to list all Apigee organizations to which the user has access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List Apigee organizations and their paired Cloud Platform projects."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` lists all organizations to which the user's `gcloud auth`
  credentials have access, even if they don't match the active Cloud Platform
  project.

  Apigee organizations are distinct from Cloud Platform organizations, and
  usually have a one-to-one relationship with Cloud Platform projects.
  """,
      "EXAMPLES":
          """\
  To list all accessible organizations and their associated Cloud Platform projects, run:

      $ {command}

  To get a JSON array of all organizations whose Cloud Platform project names
  contain the word ``sandbox'', run:

      $ {command} --format=json --filter="project:(sandbox)"
  """}

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("table(name, project.flatten())")

  def Run(self, args):
    """Run the list command."""
    result = apigee.OrganizationsClient.List(vars(args))
    if "organizations" in result:
      for organization in result["organizations"]:
        yield {
            "name": organization["organization"],
            "project": organization["projectIds"]
        }
