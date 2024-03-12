# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to lookup a Service Project."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import service_projects as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To lookup the service project `my-service-project`, run:

          $ {command} --project=my-service-project
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class LookupGA(base.DescribeCommand):
  """Lookup an Apphub service project."""

  detailed_help = _DETAILED_HELP

  def Run(self, args):
    """Run the lookup command."""
    client = apis.ServiceProjectsClient(release_track=base.ReleaseTrack.GA)
    service_project = properties.VALUES.core.project.Get()
    return client.Lookup(service_project=service_project)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class LookupAlpha(base.DescribeCommand):
  """Lookup an Apphub service project."""

  detailed_help = _DETAILED_HELP

  def Run(self, args):
    """Run the lookup command."""
    client = apis.ServiceProjectsClient(release_track=base.ReleaseTrack.ALPHA)
    service_project = properties.VALUES.core.project.Get()
    return client.Lookup(service_project=service_project)
