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
"""Command for creating machine images."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import uuid

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.instances.bulk import flags as bulk_flags
from googlecloudsdk.command_lib.compute.instances.bulk import util as bulk_util
from googlecloudsdk.command_lib.compute.queued_resources import flags as queued_resource_flags
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Create a Compute Engine queued resource."""
  _ALLOW_RSA_ENCRYPTED_CSEK_KEYS = True

  detailed_help = {
      'brief':
          'Create a Compute Engine queued resource.',
      'EXAMPLES':
          """
     To create a queued resource, run:

       $ {command} queued-resource-1 --count=1 --name-pattern=instance-#
         --valid-until-duration=7d --zone=us-central1-a
   """,
  }
  # LINT.IfChange(alpha_spec)
  _support_nvdimm = False
  _support_public_dns = False
  _support_erase_vss = True
  _support_min_node_cpu = True
  _support_source_snapshot_csek = False
  _support_image_csek = True
  _deprecate_maintenance_policy = True
  _support_display_device = True
  _support_local_ssd_size = True
  _support_secure_tags = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = True
  _support_visible_core_count = True
  _support_max_run_duration = True
  _support_enable_target_shape = True
  _support_confidential_compute = True
  _support_post_key_revocation_action_type = True
  _support_rsa_encrypted = True
  _support_create_disk_snapshots = True
  _support_boot_snapshot_uri = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_no_address_in_networking = True
  _support_max_count_per_zone = False
  _support_local_ssd_recovery_timeout = True
  _support_network_queue_count = True
  _support_performance_monitoring_unit = True
  _support_custom_hostnames = True
  _support_storage_pool = False
  _support_specific_then_x = True
  _support_ipv6_only = True

  @classmethod
  def Args(cls, parser):
    # Bulk insert specific flags
    bulk_flags.AddCommonBulkInsertArgs(
        parser,
        base.ReleaseTrack.ALPHA,
        deprecate_maintenance_policy=cls._deprecate_maintenance_policy,
        support_min_node_cpu=cls._support_min_node_cpu,
        support_erase_vss=cls._support_erase_vss,
        snapshot_csek=cls._support_source_snapshot_csek,
        image_csek=cls._support_image_csek,
        support_display_device=cls._support_display_device,
        support_local_ssd_size=cls._support_local_ssd_size,
        support_numa_node_count=cls._support_numa_node_count,
        support_visible_core_count=cls._support_visible_core_count,
        support_max_run_duration=cls._support_max_run_duration,
        support_enable_target_shape=cls._support_enable_target_shape,
        add_zone_region_flags=False,
        support_confidential_compute_type=cls
        ._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx,
        support_no_address_in_networking=cls._support_no_address_in_networking,
        support_max_count_per_zone=cls._support_max_count_per_zone,
        support_network_queue_count=cls._support_network_queue_count,
        support_performance_monitoring_unit=cls._support_performance_monitoring_unit,
        support_custom_hostnames=cls._support_custom_hostnames,
        support_specific_then_x_affinity=cls._support_specific_then_x,
        support_ipv6_only=cls._support_ipv6_only,
    )
    cls.AddSourceInstanceTemplate(parser)
    instances_flags.AddSecureTagsArgs(parser)
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)
    instances_flags.AddMaintenanceInterval().AddToParser(parser)
    # LINT.ThenChange(../instances/bulk/create.py:alpha_spec)
    # Queued resource specific flags
    valid_until_group = parser.add_group(mutex=True, required=True)
    valid_until_group.add_argument(
        '--valid-until-duration',
        type=arg_parsers.Duration(),
        help="""Relative deadline for waiting for capacity.""")
    valid_until_group.add_argument(
        '--valid-until-time',
        type=arg_parsers.Datetime.Parse,
        help="""Absolute deadline for waiting for capacity in RFC3339 text format."""
    )
    Create.QueuedResourceArg = queued_resource_flags.MakeQueuedResourcesArg(
        plural=False)
    Create.QueuedResourceArg.AddArgument(parser, operation_type='create')
    queued_resource_flags.AddOutputFormat(parser)

  # LINT.IfChange(instance_template)
  @classmethod
  def AddSourceInstanceTemplate(cls, parser):
    cls.SOURCE_INSTANCE_TEMPLATE = (
        bulk_flags.MakeBulkSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)

  # LINT.ThenChange(../instances/bulk/create.py:instance_template)

  def Run(self, args):
    bulk_flags.ValidateBulkInsertArgs(
        args,
        support_enable_target_shape=self._support_enable_target_shape,
        support_max_run_duration=self._support_max_run_duration,
        support_image_csek=self._support_image_csek,
        support_source_snapshot_csek=self._support_source_snapshot_csek,
        support_max_count_per_zone=self._support_max_count_per_zone,
        support_custom_hostnames=self._support_custom_hostnames,
    )

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    queued_resource_ref = Create.QueuedResourceArg.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    zone = args.zone
    if not zone and queued_resource_ref.zone:
      zone = queued_resource_ref.zone

    supported_features = bulk_util.SupportedFeatures(
        self._support_nvdimm,
        self._support_public_dns,
        self._support_erase_vss,
        self._support_min_node_cpu,
        self._support_source_snapshot_csek,
        self._support_image_csek,
        self._support_confidential_compute,
        self._support_post_key_revocation_action_type,
        self._support_rsa_encrypted,
        self._deprecate_maintenance_policy,
        self._support_create_disk_snapshots,
        self._support_boot_snapshot_uri,
        self._support_display_device,
        self._support_local_ssd_size,
        self._support_secure_tags,
        self._support_host_error_timeout_seconds,
        self._support_numa_node_count,
        self._support_visible_core_count,
        self._support_max_run_duration,
        self._support_local_ssd_recovery_timeout,
        self._support_enable_target_shape,
        self._support_confidential_compute_type,
        self._support_confidential_compute_type_tdx,
        self._support_max_count_per_zone,
        self._support_performance_monitoring_unit,
        self._support_custom_hostnames,
        self._support_storage_pool,
        self._support_specific_then_x,
    )
    bulk_insert_instance_resource = bulk_util.CreateBulkInsertInstanceResource(
        args, holder, client, holder.resources, queued_resource_ref.project,
        zone, compute_scopes.ScopeEnum.ZONE, self.SOURCE_INSTANCE_TEMPLATE,
        supported_features)

    # minCount is not supported in QueuedResource
    bulk_insert_instance_resource.reset('minCount')

    queued_resource = client.messages.QueuedResource(
        name=queued_resource_ref.Name(),
        queuingPolicy=client.messages.QueuingPolicy(
            validUntilDuration=client.messages.Duration(
                seconds=args.valid_until_duration)),
        bulkInsertInstanceResource=bulk_insert_instance_resource)

    request = client.messages.ComputeZoneQueuedResourcesInsertRequest(
        queuedResource=queued_resource,
        project=queued_resource_ref.project,
        zone=queued_resource_ref.zone,
        requestId=uuid.uuid4().hex,
    )
    if args.async_:
      response = client.apitools_client.zoneQueuedResources.Insert(request)
      log.status.Print('Queued resource creation in progress: {}'.format(
          response.selfLink))
      # Disable argument formatting since we have not created a resource yet.
      args.format = 'disable'
      return response
    return client.MakeRequests([(client.apitools_client.zoneQueuedResources,
                                 'Insert', request)])
