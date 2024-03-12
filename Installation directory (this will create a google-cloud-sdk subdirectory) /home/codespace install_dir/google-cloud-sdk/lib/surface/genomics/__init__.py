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
"""The main command group for genomics.

Everything under here will be the commands in your group.  Each file results in
a command with that name.

This module contains a single class that extends base.Group.  Calliope will
dynamically search for the implementing class and use that as the command group
for this command tree.  You can implement methods in this class to override some
of the default behavior.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Genomics(base.Group):
  """Manage Genomics resources."""
  category = base.SOLUTIONS_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190534871):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
