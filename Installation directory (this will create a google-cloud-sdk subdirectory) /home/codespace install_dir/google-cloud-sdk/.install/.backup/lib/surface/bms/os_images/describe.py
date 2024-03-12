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
"""'Bare Metal Solution os images describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
import six

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Describe Bare Metal Solution OS image in a project.
        """,
    'EXAMPLES':
        """
          To describe given OS image within the project, run:

            $ {command} my-os-image --project=my-project
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(six.with_metaclass(abc.ABCMeta, base.CacheCommand)):
  """Describe Bare Metal Solution OS images in a project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddOsImageArgToParser(parser, positional=True)

  def Run(self, args):
    client = BmsClient()
    os_image_parent = args.CONCEPTS.os_image.Parse()
    return client.GetOSImage(os_image_parent)


Describe.detailed_help = DETAILED_HELP
