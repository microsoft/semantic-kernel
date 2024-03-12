# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Upgrade cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import container_command_util
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util.semver import SemVer


class UpgradeHelpText(object):
  """Upgrade available help text messages."""
  UPGRADE_AVAILABLE = """
* - There is an upgrade available for your cluster(s).
"""

  SUPPORT_ENDING = """
** - The current version of your cluster(s) will soon be out of support, please upgrade.
"""

  UNSUPPORTED = """
*** - The current version of your cluster(s) is unsupported, please upgrade.
"""

  UPGRADE_COMMAND = """
To upgrade nodes to the latest available version, run
  $ gcloud container clusters upgrade {name}"""


class VersionVerifier(object):
  """Compares the cluster and master versions for upgrade availablity."""
  UP_TO_DATE = 0
  UPGRADE_AVAILABLE = 1
  SUPPORT_ENDING = 2
  UNSUPPORTED = 3

  def Compare(self, current_master_version, current_cluster_version):
    """Compares the cluster and master versions and returns an enum."""
    if current_master_version == current_cluster_version:
      return self.UP_TO_DATE
    master_version = SemVer(current_master_version)
    cluster_version = SemVer(current_cluster_version)
    major, minor, _ = master_version.Distance(cluster_version)
    if major != 0 or minor > 2:
      return self.UNSUPPORTED
    elif minor > 1:
      return self.SUPPORT_ENDING
    else:
      return self.UPGRADE_AVAILABLE


def ParseUpgradeOptionsBase(args):
  """Parses the flags provided with the cluster upgrade command."""
  return api_adapter.UpdateClusterOptions(
      version=args.cluster_version,
      update_master=args.master,
      update_nodes=(not args.master),
      node_pool=args.node_pool,
      image_type=args.image_type,
      image=args.image,
      image_project=args.image_project)


def _Args(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.
  """
  parser.add_argument(
      'name', metavar='NAME', help='The name of the cluster to upgrade.')
  flags.AddClusterVersionFlag(
      parser,
      help="""\
The GKE release version to which to upgrade the cluster's node pools or master.

If desired cluster version is omitted, *node pool* upgrades default to the current
*master* version and *master* upgrades default to the default cluster version,
which can be found in the server config.

You can find the list of allowed versions for upgrades by running:

  $ gcloud container get-server-config
""")
  parser.add_argument('--node-pool', help='The node pool to upgrade.')
  parser.add_argument(
      '--master',
      help=(
          "Upgrade the cluster's master. Node pools cannot be upgraded at the "
          ' same time as the master.'
      ),
      action='store_true',
  )
  # Timeout in seconds for the operation, default 3600 seconds (60 minutes)
  parser.add_argument(
      '--timeout',
      type=int,
      default=3600,
      hidden=True,
      help='Timeout (seconds) for waiting on the operation to complete.')
  flags.AddAsyncFlag(parser)
  flags.AddImageTypeFlag(parser, 'cluster/node pool')
  flags.AddImageFlag(parser, hidden=True)
  flags.AddImageProjectFlag(parser, hidden=True)


def MaybeLog122UpgradeWarning(cluster):
  """Logs deprecation warning for GKE v1.22 upgrades."""
  if cluster is not None:
    cmv = SemVer(cluster.currentMasterVersion)
    if cmv >= SemVer('1.22.0-gke.0'):
      return

  log.status.Print(
      'Upcoming breaking change: Starting with v1.22, Kubernetes has removed '
      'several v1beta1 APIs for more stable v1 APIs. Read more about this '
      'change - '
      'https://cloud.google.com/kubernetes-engine/docs/deprecations/apis-1-22. '
      'Please ensure that your cluster is not using any deprecated v1beta1 '
      'APIs prior to upgrading to GKE 1.22.')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Upgrade(base.Command):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def ParseUpgradeOptions(self, args):
    return ParseUpgradeOptionsBase(args)

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
    cluster_ref = adapter.ParseCluster(args.name, location)
    project_id = properties.VALUES.core.project.Get(required=True)

    try:
      cluster = adapter.GetCluster(cluster_ref)
    except (exceptions.HttpException, apitools_exceptions.HttpForbiddenError,
            util.Error) as error:
      log.warning(('Problem loading details of cluster to upgrade:\n\n{}\n\n'
                   'You can still attempt to upgrade the cluster.\n').format(
                       console_attr.SafeText(error)))
      cluster = None

    try:
      server_conf = adapter.GetServerConfig(project_id, location)
    except (exceptions.HttpException, apitools_exceptions.HttpForbiddenError,
            util.Error) as error:
      log.warning(('Problem loading server config:\n\n{}\n\n'
                   'You can still attempt to upgrade the cluster.\n').format(
                       console_attr.SafeText(error)))
      server_conf = None

    upgrade_message = container_command_util.ClusterUpgradeMessage(
        name=args.name,
        server_conf=server_conf,
        cluster=cluster,
        master=args.master,
        node_pool_name=args.node_pool,
        new_version=args.cluster_version,
        new_image_type=args.image_type)

    if args.master:
      MaybeLog122UpgradeWarning(cluster)

    console_io.PromptContinue(
        message=upgrade_message, throw_if_unattended=True, cancel_on_no=True)

    options = self.ParseUpgradeOptions(args)

    try:
      op_ref = adapter.UpdateCluster(cluster_ref, options)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error, util.HTTP_ERROR_FORMAT)

    if not args.async_:
      adapter.WaitForOperation(
          op_ref,
          'Upgrading {0}'.format(cluster_ref.clusterId),
          timeout_s=args.timeout)

      log.UpdatedResource(cluster_ref)


Upgrade.detailed_help = {
    'DESCRIPTION':
        """\
      Upgrades the Kubernetes version of an existing container cluster.

      This command upgrades the Kubernetes version of the *node pools* or *master* of
      a cluster. Note that the Kubernetes version of the cluster's *master* is
      also periodically upgraded automatically as new releases are available.

      If desired cluster version is omitted, *node pool* upgrades default to the
      current *master* version and *master* upgrades default to the default
      cluster version, which can be found in the server config.

      *During node pool upgrades, nodes will be deleted and recreated.* While
      persistent Kubernetes resources, such as
      Pods backed by replication controllers, will be rescheduled onto new
      nodes, a small cluster may experience a few minutes where there are
      insufficient nodes available to run all of the scheduled Kubernetes
      resources.

      *Please ensure that any data you wish to keep is stored on a persistent*
      *disk before upgrading the cluster.* Ephemeral Kubernetes resources--in
      particular, Pods without replication controllers--will be lost, while
      persistent Kubernetes resources will get rescheduled.
    """,
    'EXAMPLES':
        """\
      Upgrade the node pool `pool-1` of `sample-cluster` to the Kubernetes
      version of the cluster's master.

        $ {command} sample-cluster --node-pool=pool-1

      Upgrade the node pool `pool-1` of `sample-cluster` to Kubernetes version
      1.14.7-gke.14:

        $ {command} sample-cluster --node-pool=pool-1 --cluster-version="1.14.7-gke.14"

      Upgrade the master of `sample-cluster` to the default cluster version:

        $ {command} sample-cluster --master
""",
}


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpgradeBeta(Upgrade):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpgradeAlpha(Upgrade):
  """Upgrade the Kubernetes version of an existing container cluster."""

  @staticmethod
  def Args(parser):
    _Args(parser)
    flags.AddSecurityProfileForUpgradeFlags(parser)

  def ParseUpgradeOptions(self, args):
    ops = ParseUpgradeOptionsBase(args)
    ops.security_profile = args.security_profile
    ops.security_profile_runtime_rules = args.security_profile_runtime_rules
    return ops
