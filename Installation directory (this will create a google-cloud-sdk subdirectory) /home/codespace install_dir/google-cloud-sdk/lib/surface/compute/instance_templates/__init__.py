# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Commands for reading and manipulating instance templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class InstanceTemplates(base.Group):
  """Read and manipulate Compute Engine instances templates.

  Lists, creates, deletes, and modifies Compute Engine instance templates.

  More information on Compute Engine instance templates can be found here:
  [](https://cloud.google.com/compute/docs/instance-templates)

  """

InstanceTemplates.category = base.INSTANCES_CATEGORY

InstanceTemplates.detailed_help = {
    'DESCRIPTION': """
        Lists, creates, deletes, and modifies Compute Engine instance templates.

        For more information about instance templates, see the
        [instances templates documentation](https://cloud.google.com/compute/docs/instance-templates).

        See also: [Instance templates API](https://cloud.google.com/compute/docs/reference/rest/v1/instanceTemplates).
    """,
}
