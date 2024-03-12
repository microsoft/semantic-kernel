# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""List the keys within a keyring."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kmsinventory import inventory
from googlecloudsdk.calliope import base

from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION': """
         *{command}* lists the keys in the specified project.
       """,
    'EXAMPLES': """
        To view the keys in the default project, run:

           $ {command}

        To view the keys in project `jellyfish`, run:

           $ {command} --project=jellyfish
       """,
}


class ListKeys(base.ListCommand):
  """Lists the keys in a project."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    pass

  def Run(self, args):
    # NOMUTANTS--no good way to test
    project = properties.VALUES.core.project.Get(required=True)
    return inventory.ListKeys(project, args)
