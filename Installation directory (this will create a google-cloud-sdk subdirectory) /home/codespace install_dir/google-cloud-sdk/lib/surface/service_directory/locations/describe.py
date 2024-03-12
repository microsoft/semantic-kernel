# -*- coding: utf-8 -*- #
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
"""`gcloud service-directory locations describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import locations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import resource_args


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describes a location."""

  detailed_help = {
      'EXAMPLES':
          """\
          To describe a Service Directory location, run:

            $ {command} location us-east1
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to describe.')

  def Run(self, args):
    client = locations.LocationsClient(self.GetReleaseTrack())
    location_ref = args.CONCEPTS.location.Parse()

    return client.Describe(location_ref)

  def GetReleaseTrack(self):
    return base.ReleaseTrack.GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  """Describes a location."""

  def GetReleaseTrack(self):
    return base.ReleaseTrack.BETA
