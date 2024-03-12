# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for creating instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.instances.bulk import flags as bulk_flags
from googlecloudsdk.command_lib.compute.instances.bulk import util as bulk_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'brief':
        """
          Create multiple Compute Engine virtual machines.
        """,
    'DESCRIPTION':
        """
        *{command}* facilitates the creation of multiple Compute Engine
        virtual machines with a single command. They offer a number of advantages
        compared to the single instance creation command. This includes the
        ability to automatically pick a zone in which to create instances based
        on resource availability, the ability to specify that the request be
        atomic or best-effort, and a faster rate of instance creation.
        """,
    'EXAMPLES':
        """
        To create instances called 'example-instance-1', 'example-instance-2',
        and 'example-instance-3' in the 'us-central1-a' zone, run:

          $ {command} --predefined-names=example-instance-1,example-instance-2,example-instance-3 --zone=us-central1-a
        """,
}


def _GetOperations(compute_client, project, operation_group_id):
  """Requests operations with group id matching the given one."""

  errors_to_collect = []

  _, operation_filter = filter_rewrite.Rewriter().Rewrite(
      expression='operationGroupId=' + operation_group_id)

  operations_response = compute_client.MakeRequests(
      [(compute_client.apitools_client.globalOperations, 'AggregatedList',
        compute_client.apitools_client.globalOperations.GetRequestType(
            'AggregatedList')(filter=operation_filter, project=project))],
      errors_to_collect=errors_to_collect,
      log_result=False,
      always_return_operation=True,
      no_followup=True)

  return operations_response, errors_to_collect


def _GetResult(compute_client, request, operation_group_id):
  """Requests operations with group id and parses them as an output."""

  operations_response, errors = _GetOperations(compute_client, request.project,
                                               operation_group_id)
  if errors:
    utils.RaiseToolException(errors, error_message='Could not fetch resource:')
  result = {'operationGroupId': operation_group_id, 'instances': []}

  successful = [
      op for op in operations_response if op.operationType == 'insert' and
      str(op.status) == 'DONE' and op.error is None
  ]
  num_successful = len(successful)
  num_unsuccessful = request.bulkInsertInstanceResource.count - num_successful

  def GetInstanceStatus(op):
    return {
        'id': op.targetId,
        'name': op.targetLink.split('/')[-1],
        'zone': op.zone,
        'selfLink': op.targetLink
    }

  instances_status = [GetInstanceStatus(op) for op in successful]

  result['createdInstanceCount'] = num_successful
  result['failedInstanceCount'] = num_unsuccessful
  result['instances'] = instances_status

  return result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create Compute Engine virtual machine instances."""

  _support_nvdimm = False
  _support_public_dns = False
  _support_erase_vss = True
  _support_min_node_cpu = True
  _support_source_snapshot_csek = False
  _support_image_csek = True
  _support_confidential_compute = True
  _support_post_key_revocation_action_type = True
  _support_rsa_encrypted = True
  _deprecate_maintenance_policy = True
  _support_create_disk_snapshots = True
  _support_boot_snapshot_uri = True
  _support_display_device = False
  _support_local_ssd_size = True
  _support_secure_tags = False
  _support_host_error_timeout_seconds = False
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_max_run_duration = False
  _support_enable_target_shape = True
  _support_confidential_compute_type = False
  _support_confidential_compute_type_tdx = False
  _support_no_address_in_networking = False
  _support_max_count_per_zone = True
  _support_local_ssd_recovery_timeout = True
  _support_network_queue_count = True
  _support_performance_monitoring_unit = False
  _support_custom_hostnames = False
  _support_storage_pool = False
  _support_specific_then_x_affinity = False

  _log_async = False

  @classmethod
  def Args(cls, parser):
    bulk_flags.AddCommonBulkInsertArgs(
        parser,
        base.ReleaseTrack.GA,
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
        support_confidential_compute_type=cls._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls._support_confidential_compute_type_tdx,
        support_no_address_in_networking=cls._support_no_address_in_networking,
        support_max_count_per_zone=cls._support_max_count_per_zone,
        support_network_queue_count=cls._support_network_queue_count,
        support_performance_monitoring_unit=cls._support_performance_monitoring_unit,
        support_custom_hostnames=cls._support_custom_hostnames,
        support_storage_pool=cls._support_storage_pool,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
    )
    cls.AddSourceInstanceTemplate(parser)

    # Flags specific to GA release track
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)

  # LINT.IfChange(instance_template)
  @classmethod
  def AddSourceInstanceTemplate(cls, parser):
    cls.SOURCE_INSTANCE_TEMPLATE = (
        bulk_flags.MakeBulkSourceInstanceTemplateArg())
    cls.SOURCE_INSTANCE_TEMPLATE.AddArgument(parser)

  # LINT.ThenChange(../../queued_resources/create.py:instance_template)

  def Collection(self):
    return 'compute.instances'

  def _CreateRequests(self, args, holder, compute_client, resource_parser,
                      project, location, scope):
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
        self._support_specific_then_x_affinity,
    )
    bulk_instance_resource = bulk_util.CreateBulkInsertInstanceResource(
        args,
        holder,
        compute_client,
        resource_parser,
        project,
        location,
        scope,
        self.SOURCE_INSTANCE_TEMPLATE,
        supported_features,
    )

    if scope == compute_scopes.ScopeEnum.ZONE:
      instance_service = compute_client.apitools_client.instances
      request_message = (
          compute_client.messages.ComputeInstancesBulkInsertRequest(
              bulkInsertInstanceResource=bulk_instance_resource,
              project=project,
              zone=location,
          )
      )
    elif scope == compute_scopes.ScopeEnum.REGION:
      instance_service = compute_client.apitools_client.regionInstances
      request_message = (
          compute_client.messages.ComputeRegionInstancesBulkInsertRequest(
              bulkInsertInstanceResource=bulk_instance_resource,
              project=project,
              region=location,
          )
      )

    return instance_service, request_message

  def Run(self, args):
    """Runs bulk create command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.

    Returns:
      A resource object dispatched by display.Displayer().
    """
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
    compute_client = holder.client
    resource_parser = holder.resources

    project = properties.VALUES.core.project.GetOrFail()
    location = None
    scope = None

    if args.IsSpecified('zone'):
      location = args.zone
      scope = compute_scopes.ScopeEnum.ZONE
    elif args.IsSpecified('region'):
      location = args.region
      scope = compute_scopes.ScopeEnum.REGION

    instances_service, request = self._CreateRequests(args, holder,
                                                      compute_client,
                                                      resource_parser, project,
                                                      location, scope)

    self._errors = []
    self._log_async = False
    self._status_message = None

    if args.async_:
      self._log_async = True
      try:
        response = instances_service.BulkInsert(request)
        self._operation_selflink = response.selfLink
        return {'operationGroupId': response.operationGroupId}
      except exceptions.HttpException as error:
        raise error

    errors_to_collect = []
    response = compute_client.MakeRequests(
        [(instances_service, 'BulkInsert', request)],
        errors_to_collect=errors_to_collect,
        log_result=False,
        always_return_operation=True,
        no_followup=True)

    self._errors = errors_to_collect
    if response:
      operation_group_id = response[0].operationGroupId
      result = _GetResult(compute_client, request, operation_group_id)
      if (result.get('createdInstanceCount') is not None and
          result.get('failedInstanceCount') is not None):
        self._status_message = 'VM instances created: {}, failed: {}.'.format(
            result['createdInstanceCount'], result['failedInstanceCount'])
      return result
    return

  def Epilog(self, resources_were_displayed):
    del resources_were_displayed
    if self._errors:
      log.error(self._errors[0][1])
    elif self._log_async:
      log.status.Print('Bulk instance creation in progress: {}'.format(
          self._operation_selflink))
    else:
      if self._errors:
        log.warning(self._errors[0][1])
      log.status.Print(
          'Bulk create request finished with status message: [{}]'.format(
              self._status_message))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create Compute Engine virtual machine instances."""

  _support_display_device = True
  _support_secure_tags = False
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = False
  _support_visible_core_count = True
  _support_max_run_duration = True
  _support_enable_target_shape = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_no_address_in_networking = False
  _support_max_count_per_zone = True
  _support_local_ssd_recovery_timeout = True
  _support_network_queue_count = True
  _support_local_ssd_size = True
  _support_performance_monitoring_unit = False
  _support_custom_hostnames = True
  _support_storage_pool = False
  _support_specific_then_x_affinity = True

  @classmethod
  def Args(cls, parser):
    bulk_flags.AddCommonBulkInsertArgs(
        parser,
        base.ReleaseTrack.BETA,
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
        support_confidential_compute_type=cls._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx,
        support_no_address_in_networking=cls._support_no_address_in_networking,
        support_max_count_per_zone=cls._support_max_count_per_zone,
        support_network_queue_count=cls._support_network_queue_count,
        support_performance_monitoring_unit=cls._support_performance_monitoring_unit,
        support_custom_hostnames=cls._support_custom_hostnames,
        support_storage_pool=cls._support_storage_pool,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
    )
    cls.AddSourceInstanceTemplate(parser)

    # Flags specific to Beta release track
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Compute Engine virtual machine instances."""

  # LINT.IfChange(alpha_spec)
  _support_display_device = True
  _support_local_ssd_size = True
  _support_secure_tags = True
  _support_host_error_timeout_seconds = True
  _support_numa_node_count = True
  _support_visible_core_count = True
  _support_max_run_duration = True
  _support_enable_target_shape = True
  _support_confidential_compute_type = True
  _support_confidential_compute_type_tdx = True
  _support_no_address_in_networking = True
  _support_max_count_per_zone = True
  _support_local_ssd_recovery_timeout = True
  _support_network_queue_count = True
  _support_performance_monitoring_unit = True
  _support_custom_hostnames = True
  _support_storage_pool = True
  _support_specific_then_x_affinity = True
  _support_ipv6_only = True

  @classmethod
  def Args(cls, parser):
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
        support_confidential_compute_type=cls._support_confidential_compute_type,
        support_confidential_compute_type_tdx=cls
        ._support_confidential_compute_type_tdx,
        support_no_address_in_networking=cls._support_no_address_in_networking,
        support_max_count_per_zone=cls._support_max_count_per_zone,
        support_network_queue_count=cls._support_network_queue_count,
        support_performance_monitoring_unit=cls._support_performance_monitoring_unit,
        support_custom_hostnames=cls._support_custom_hostnames,
        support_storage_pool=cls._support_storage_pool,
        support_specific_then_x_affinity=cls._support_specific_then_x_affinity,
        support_ipv6_only=cls._support_ipv6_only,
    )

    cls.AddSourceInstanceTemplate(parser)

    # Flags specific to Alpha release track
    instances_flags.AddSecureTagsArgs(parser)
    instances_flags.AddHostErrorTimeoutSecondsArgs(parser)
    instances_flags.AddMaintenanceInterval().AddToParser(parser)
    instances_flags.AddLocalSsdRecoveryTimeoutArgs(parser)
  # LINT.ThenChange(../../queued_resources/create.py:alpha_spec)


Create.detailed_help = DETAILED_HELP
