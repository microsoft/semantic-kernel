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
"""Utilities for gkeonprem API clients for VMware admin cluster resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Generator

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkeonprem import client
from googlecloudsdk.api_lib.container.gkeonprem import update_mask
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.vmware import flags
from googlecloudsdk.core import properties
from googlecloudsdk.generated_clients.apis.gkeonprem.v1 import gkeonprem_v1_messages as messages


class AdminClustersClient(client.ClientBase):
  """Client for clusters in gkeonprem vmware API."""

  def __init__(self, **kwargs):
    super(AdminClustersClient, self).__init__(**kwargs)
    self._service = self._client.projects_locations_vmwareAdminClusters

  def Enroll(
      self, args, membership=None, vmware_admin_cluster_id=None, parent=None
  ) -> messages.Operation:
    """Enrolls an admin cluster to Anthos on VMware."""
    kwargs = {
        'membership': (
            membership
            if membership
            else self._admin_cluster_membership_name(args)
        ),
        'vmwareAdminClusterId': (
            vmware_admin_cluster_id
            if vmware_admin_cluster_id
            else self._admin_cluster_id(args)
        ),
    }
    req = messages.GkeonpremProjectsLocationsVmwareAdminClustersEnrollRequest(
        parent=parent if parent else self._admin_cluster_parent(args),
        enrollVmwareAdminClusterRequest=messages.EnrollVmwareAdminClusterRequest(
            **kwargs
        ),
    )
    return self._service.Enroll(req)

  def Unenroll(self, args: parser_extensions.Namespace) -> messages.Operation:
    """Unenrolls an Anthos on VMware admin cluster."""
    kwargs = {
        'name': self._admin_cluster_name(args),
        'validateOnly': self.GetFlag(args, 'validate_only'),
        'allowMissing': self.GetFlag(args, 'allow_missing'),
    }
    req = messages.GkeonpremProjectsLocationsVmwareAdminClustersUnenrollRequest(
        **kwargs
    )
    return self._service.Unenroll(req)

  def List(
      self, args: parser_extensions.Namespace
  ) -> Generator[messages.VmwareAdminCluster, None, None]:
    """Lists Admin Clusters in the GKE On-Prem VMware API."""
    # Workaround for P4SA: Call query version config first, ignore the result.
    # Context: b/296435390#comment2
    project = (
        args.project if args.project else properties.VALUES.core.project.Get()
    )
    # Hard code location to `us-west1`, because it cannot handle `--location=-`.
    parent = 'projects/{project}/locations/{location}'.format(
        project=project, location='us-west1'
    )
    dummy_request = messages.GkeonpremProjectsLocationsVmwareClustersQueryVersionConfigRequest(
        parent=parent,
    )
    _ = self._client.projects_locations_vmwareClusters.QueryVersionConfig(
        dummy_request
    )

    if (
        'location' not in args.GetSpecifiedArgsDict()
        and not properties.VALUES.container_vmware.location.Get()
    ):
      args.location = '-'

    list_req = (
        messages.GkeonpremProjectsLocationsVmwareAdminClustersListRequest(
            parent=self._location_name(args)
        )
    )

    return list_pager.YieldFromList(
        self._service,
        list_req,
        field='vmwareAdminClusters',
        batch_size=flags.Get(args, 'page_size'),
        limit=flags.Get(args, 'limit'),
        batch_size_attribute='pageSize',
    )

  def Update(
      self, args: parser_extensions.Namespace, cluster_ref=None
  ) -> messages.Operation:
    """Updates an admin cluster to Anthos on VMware."""
    kwargs = {
        'name': (
            cluster_ref.RelativeName()
            if cluster_ref
            else self._admin_cluster_name(args)
        ),
        'updateMask': update_mask.get_update_mask(
            args, update_mask.VMWARE_ADMIN_CLUSTER_ARGS_TO_UPDATE_MASKS
        ),
        'vmwareAdminCluster': self._vmware_admin_cluster(args),
    }
    req = messages.GkeonpremProjectsLocationsVmwareAdminClustersPatchRequest(
        **kwargs
    )
    return self._service.Patch(req)

  def _vmware_admin_cluster(self, args: parser_extensions.Namespace):
    """Constructs proto message VmwareAdminCluster."""
    kwargs = {
        'platformConfig': self._platform_config(args),
    }
    if any(kwargs.values()):
      return messages.VmwareAdminCluster(**kwargs)
    return None

  def _platform_config(self, args: parser_extensions.Namespace):
    """Constructs proto message field platform_config."""
    required_platform_version = flags.Get(args, 'required_platform_version')
    if required_platform_version is None:
      required_platform_version = flags.Get(args, 'version')

    kwargs = {
        'requiredPlatformVersion': required_platform_version,
    }
    if any(kwargs.values()):
      return messages.VmwarePlatformConfig(**kwargs)
    return None
