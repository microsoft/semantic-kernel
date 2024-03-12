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
"""`gcloud certificate-manager maps describe` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificate_maps
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an existing certificate map.

  This command fetches and prints information about an existing certificate map.

  ## EXAMPLES

  To describe a certificate map with name simple-map, run:

    $ {command} simple-map
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateMapResourceArg(parser, 'to describe')

  def Run(self, args):
    client = certificate_maps.CertificateMapClient()
    return client.Get(args.CONCEPTS.map.Parse())
