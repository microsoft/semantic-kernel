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
"""Command to list suggested environment upgrades."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import image_versions_util as image_versions_command_util
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ListUpgrades(base.ListCommand):
  """List the Cloud Composer image version upgrades for a specific environment.

  {command} prints a table listing the suggested image-version upgrades with the
  following columns:
  * Image Version ID
  * Composer 'default' flag
  * List of supported python versions
  """

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser, 'to list upgrades')
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table[box,title="SUGGESTED UPGRADES"]('
        'imageVersionId:label="IMAGE VERSION",'
        'isDefault:label="COMPOSER DEFAULT",'
        'supportedPythonVersions.list():label="SUPPORTED PYTHON VERSIONS")')

  def Run(self, args):
    env_ref = args.CONCEPTS.environment.Parse()
    log.status.Print('Fetching list of suggested upgrades...')
    return image_versions_command_util.ListImageVersionUpgrades(
        env_ref, release_track=self.ReleaseTrack())
