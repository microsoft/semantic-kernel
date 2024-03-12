# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The super-group for the Filestore CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION':
        """\
        The gcloud filestore command group lets you create, configure and
        manipulate Filestore instances.

        With Filestore, you can take advantage of Google Cloud Platform's scale,
        performance, and value to create and run managed file systems on Google
        infrastructure.

        More information on Filestore can be found here:
        https://cloud.google.com/filestore/ and detailed documentation can be
        found here: https://cloud.google.com/filestore/docs/
        """,
}


class Filestore(base.Group):
  """Create and manipulate Filestore resources."""
  detailed_help = DETAILED_HELP
  category = base.STORAGE_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190533738):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
