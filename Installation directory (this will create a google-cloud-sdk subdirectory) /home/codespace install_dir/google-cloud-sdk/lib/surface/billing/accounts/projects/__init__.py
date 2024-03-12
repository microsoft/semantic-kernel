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
"""Manage the billing account configuration of your projects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


_BASE_MESSAGE = """\
The `gcloud alpha billing accounts projects` group has been moved to `gcloud
billing projects`. Please use the new, shorter commands instead."""


# Don't promote this group beyond alpha, since the new alias is preferred.
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
@base.Deprecate(is_removed=False, warning=_BASE_MESSAGE, error=_BASE_MESSAGE)
class Projects(base.Group):
  """Manage the billing account configuration of your projects."""
