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
"""Describe cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from surface.container.clusters.upgrade import UpgradeHelpText
from surface.container.clusters.upgrade import VersionVerifier


class Describe(base.DescribeCommand):
  """Describe an existing cluster for running containers."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To describe an existing cluster, run:

            $ {command} sample-cluster
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('name', help='The name of this cluster.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    adapter = self.context['api_adapter']
    location_get = self.context['location_get']
    location = location_get(args)

    self._upgrade_hint = None
    vv = VersionVerifier()
    c = adapter.GetCluster(adapter.ParseCluster(args.name, location))
    ver_status = vv.Compare(c.currentMasterVersion, c.currentNodeVersion)

    if ver_status == VersionVerifier.UPGRADE_AVAILABLE:
      self._upgrade_hint = UpgradeHelpText.UPGRADE_AVAILABLE
    elif ver_status == VersionVerifier.SUPPORT_ENDING:
      self._upgrade_hint = UpgradeHelpText.SUPPORT_ENDING
    elif ver_status == VersionVerifier.UNSUPPORTED:
      self._upgrade_hint = UpgradeHelpText.UNSUPPORTED

    if ver_status != VersionVerifier.UP_TO_DATE:
      self._upgrade_hint += UpgradeHelpText.UPGRADE_COMMAND.format(name=c.name)

    return c

  def Epilog(self, results_were_displayed):
    if self._upgrade_hint:
      log.status.Print(self._upgrade_hint)
