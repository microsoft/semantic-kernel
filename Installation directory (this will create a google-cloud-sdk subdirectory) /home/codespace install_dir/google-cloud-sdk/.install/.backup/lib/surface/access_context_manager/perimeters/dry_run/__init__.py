# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""The command group for the Access Context Manager perimemters CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class DryRun(base.Group):
  """Manage the dry-run mode configuration for Service Perimeters."""


detailed_help = {
    'brief':
        'Enable management of dry-run mode configuration for Service Perimeters.',
    'DESCRIPTION':
        """A Service Perimeter describes a set of Google Cloud Platform
        resources which can freely import and export data amongst themselves,
        but not externally, by default.

        A dry-run mode configuration (also known as the Service Perimeter
        `spec`) makes it possible to understand the impact of any changes to a
        VPC Service Controls policy change before committing the change to the
        enforcement mode configuration.

        Note: For Service Perimeters without an explicit dry-run mode
        configuration, the enforcement mode configuration is used as the dry-run
        mode configuration, resulting in no audit logs being generated."""
}

DryRun.detailed_help = detailed_help
