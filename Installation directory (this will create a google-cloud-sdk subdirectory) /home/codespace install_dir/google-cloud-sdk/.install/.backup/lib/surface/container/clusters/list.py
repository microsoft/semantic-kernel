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
"""List clusters command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import transforms
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from surface.container.clusters.upgrade import UpgradeHelpText
from surface.container.clusters.upgrade import VersionVerifier


class List(base.ListCommand):
  """List existing clusters for running containers."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          This command queries cluster across all locations unless either
          '--location', '--region', or '--zone' are specified.
      """,
      'EXAMPLES': """\
          To list existing clusters in all locations, run:

            $ {command}
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(util.CLUSTERS_FORMAT)

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
    location = location_get(args, ignore_property=True, required=False)
    project = properties.VALUES.core.project.Get(required=True)

    def sort_key(cluster):
      return (cluster.zone, cluster.name)

    try:
      clusters = adapter.ListClusters(project, location)
      clusters.clusters = sorted(clusters.clusters, key=sort_key)

      if clusters.missingZones:
        log.warning(
            'The following zones did not respond: {0}. List results may be '
            'incomplete.'.format(', '.join(clusters.missingZones)))

      upgrade_available = False
      support_ending = False
      unsupported = False
      expiring = False
      self._upgrade_hint = ''
      self._expire_warning = ''
      self._degraded_warning = ''
      vv = VersionVerifier()
      for c in clusters.clusters:
        time_left = transforms.ParseExpireTime(c.expireTime)
        if time_left and time_left.days < constants.EXPIRE_WARNING_DAYS:
          expiring = True
        if adapter.IsDegraded(c):
          self._degraded_warning += constants.DEGRADED_WARNING.format(
              cluster_name=c.name,
              cluster_degraded_warning=adapter.GetDegradedWarning(c))
        if c.enableKubernetesAlpha:
          # Don't print upgrade hints for alpha clusters, they aren't
          # upgradeable.
          continue

        if c.nodePools:
          ver_status = vv.Compare(c.currentMasterVersion, c.currentNodeVersion)
          # If autopilot is enabled, then nodes cannot be manually upgraded,
          # so we don't show the upgrade_available message
          # (which prompts users to run a command to upgrade their nodes).
          if ver_status == VersionVerifier.UPGRADE_AVAILABLE and not (
              c.autopilot and c.autopilot.enabled
          ):
            c.currentNodeVersion += ' *'
            upgrade_available = True
          elif ver_status == VersionVerifier.SUPPORT_ENDING:
            c.currentNodeVersion += ' **'
            support_ending = True
          elif ver_status == VersionVerifier.UNSUPPORTED:
            c.currentNodeVersion += ' ***'
            unsupported = True
        else:
          # cnv is cluster api version for clusters w/ 0 nodes, so hide
          c.currentNodeVersion = ''

      if upgrade_available:
        self._upgrade_hint += UpgradeHelpText.UPGRADE_AVAILABLE
      if support_ending:
        self._upgrade_hint += UpgradeHelpText.SUPPORT_ENDING
      if unsupported:
        self._upgrade_hint += UpgradeHelpText.UNSUPPORTED
      if self._upgrade_hint:
        self._upgrade_hint += UpgradeHelpText.UPGRADE_COMMAND.format(
            name='NAME')
      if expiring:
        self._expire_warning = constants.EXPIRE_WARNING

      return clusters.clusters
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

  def Epilog(self, resources_were_displayed):
    if self._upgrade_hint:
      log.status.Print(self._upgrade_hint)
    if self._expire_warning:
      log.warning(self._expire_warning)
    if self._degraded_warning:
      log.warning(self._degraded_warning)
