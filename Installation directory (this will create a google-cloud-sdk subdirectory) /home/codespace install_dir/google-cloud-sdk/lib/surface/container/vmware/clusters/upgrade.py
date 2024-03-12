# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to centrally upgrade an Anthos cluster on VMware."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.gkeonprem import operations
from googlecloudsdk.api_lib.container.gkeonprem import vmware_admin_clusters
from googlecloudsdk.api_lib.container.gkeonprem import vmware_clusters
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.gkeonprem import flags as common_flags
from googlecloudsdk.command_lib.container.vmware import constants
from googlecloudsdk.command_lib.container.vmware import errors
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import semver

_EXAMPLES = """
To upgrade a cluster named ``my-cluster'' managed in location ``us-west1'' to
version ``1.13.0-gke.1000'', run:

$ {command} my-cluster --location=us-west1 --version=1.13.0-gke.1000
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Upgrade(base.Command):
  """Centrally upgrade an Anthos cluster on VMware."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Gathers command line arguments for the upgrade command.

    Args:
      parser: The argparse parser to add the flag to.
    """
    parser.display_info.AddFormat(constants.VMWARE_CLUSTERS_FORMAT)
    flags.AddClusterResourceArg(parser, 'to upgrade')
    flags.AddVersion(parser, required=True)

  def Run(self, args):
    """Runs the upgrade command.

    Args:
      args: The arguments received from command line.

    Returns:
      The operation response.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    cluster_client = vmware_clusters.ClustersClient()
    cluster = cluster_client.Describe(cluster_ref)

    self._validate_version(cluster, cluster_ref)

    admin_cluster_name = cluster.adminClusterName
    if admin_cluster_name is None:
      operation_response = self._enroll_admin_cluster(
          args, cluster_ref, cluster.adminClusterMembership)
      res = encoding.MessageToPyValue(operation_response)
      admin_cluster_name = res.get('name')

    admin_cluster_ref = flags.GetAdminClusterResource(admin_cluster_name)
    self._update_platform(args, admin_cluster_ref)
    return self._upgrade(args, cluster_ref)

  def _validate_version(self, cluster, cluster_ref):
    if cluster.onPremVersion is None:
      raise errors.MissingClusterField(cluster_ref.RelativeName(),
                                       'onPremVersion')

    if semver.SemVer(cluster.onPremVersion) < semver.SemVer('1.13.0-gke.1'):
      raise errors.UnsupportedClusterVersion(
          'Central upgrade is only supported in cluster version 1.13.0 '
          'and newer. Cluster is at version {}.'.format(cluster.onPremVersion))

  def _enroll_admin_cluster(self, args, cluster_ref, admin_cluster_membership):
    admin_cluster_membership_ref = common_flags.GetAdminClusterMembershipResource(
        admin_cluster_membership)
    log.status.Print('Admin cluster is not enrolled. '
                     'Enrolling admin cluster with membership [{}]'.format(
                         admin_cluster_membership))
    admin_cluster_client = vmware_admin_clusters.AdminClustersClient()
    operation_client = operations.OperationsClient()
    operation = admin_cluster_client.Enroll(
        args,
        parent=cluster_ref.Parent().RelativeName(),
        membership=admin_cluster_membership,
        vmware_admin_cluster_id=admin_cluster_membership_ref.Name())
    operation_response = operation_client.Wait(operation)
    return operation_response

  def _update_platform(self, args, admin_cluster_ref):
    log.status.Print('Preparing version {} for upgrade'.format(args.version))
    admin_cluster_client = vmware_admin_clusters.AdminClustersClient()
    operation_client = operations.OperationsClient()
    operation = admin_cluster_client.Update(args, admin_cluster_ref)
    operation_response = operation_client.Wait(operation)
    log.UpdatedResource(admin_cluster_ref, 'Anthos on VMware admin cluster')
    return operation_response

  def _upgrade(self, args, cluster_ref):
    log.status.Print(
        'Upgrading Anthos on VMware user cluster [{}]'.format(cluster_ref))
    cluster_client = vmware_clusters.ClustersClient()
    operation_client = operations.OperationsClient()
    operation = cluster_client.Update(args)
    operation_response = operation_client.Wait(operation)
    log.UpdatedResource(cluster_ref, 'Anthos on VMware user cluster')
    return operation_response
