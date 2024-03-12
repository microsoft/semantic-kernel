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

"""The super-group for the oslogin CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'DESCRIPTION': """
        The gcloud oslogin command group lets you manage your OS Login profile.

        OS Login profiles can be used to store information such as Posix account
        information and SSH keys used for cloud products such as
        Compute Engine.

        For more information about OS Login, see the
        [OS Login documentation](https://cloud.google.com/compute/docs/oslogin).

        See also: [OS Login API](https://cloud.google.com/compute/docs/oslogin/rest/).
        """,
}


class Oslogin(base.Group):
  """Create and manipulate Compute Engine OS Login resources."""
  category = base.TOOLS_CATEGORY
  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    del context, args
    base.EnableUserProjectQuotaWithFallback()
