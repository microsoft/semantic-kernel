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
"""Convenience functions and classes for dealing with instances groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum
from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
import six
from six.moves import range  # pylint: disable=redefined-builtin

INSTANCE_GROUP_GET_NAMED_PORT_DETAILED_HELP = {
    'brief': 'Lists the named ports for an instance group resource',
    'DESCRIPTION': """
Named ports are key:value pairs metadata representing
the service name and the port that it's running on. Named ports
can be assigned to an instance group, which indicates that the service
is available on all instances in the group. This information is used
by Application Load Balancers and proxy Network Load Balancers.

*{command}* lists the named ports (name and port tuples)
for an instance group.
""",
    'EXAMPLES': """
For example, to list named ports for an instance group:

  $ {command} example-instance-group --zone=us-central1-a

The above example lists named ports assigned to an instance
group named 'example-instance-group' in the ``us-central1-a'' zone.
""",
}

# max_langth limit of instances field in InstanceGroupManagers*InstancesRequest
INSTANCES_MAX_LENGTH = 1000


def IsZonalGroup(group_ref):
  """Checks if group reference is zonal."""
  return group_ref.Collection() == 'compute.instanceGroups'


def ValidateInstanceInZone(instances, zone):
  """Validate if provided list in zone given as parameter.

  Args:
    instances: list of instances resources to be validated
    zone: a zone all instances must be in order to pass validation

  Raises:
    InvalidArgumentException: If any instance is in different zone
                              than given as parameter.
  """
  invalid_instances = [inst.SelfLink()
                       for inst in instances if inst.zone != zone]
  if any(invalid_instances):
    raise calliope_exceptions.InvalidArgumentException(
        'instances', 'The zone of instance must match the instance group zone. '
        'Following instances has invalid zone: %s'
        % ', '.join(invalid_instances))


def UnwrapResponse(responses, attr_name):
  """Extracts items stored in given attribute of instance group response."""
  for response in responses:
    for item in getattr(response, attr_name):
      yield item


def UriFuncForListInstanceRelatedObjects(resource):
  """UriFunc for listing instance-group related subresources.

  Function returns field with URI for objects being subresources of
  instance-groups, with instance fields. Works for list-instances and
  instance-configs list commands.

  Args:
    resource: instance-group subresource with instance field

  Returns:
    URI of instance
  """
  return resource.instance


def OutputNamedPortsForGroup(group_ref, compute_client):
  """Gets the request to fetch instance group."""
  compute = compute_client.apitools_client
  if group_ref.Collection() == 'compute.instanceGroups':
    service = compute.instanceGroups
    request = service.GetRequestType('Get')(
        instanceGroup=group_ref.Name(),
        zone=group_ref.zone,
        project=group_ref.project)
  else:
    service = compute.regionInstanceGroups
    request = service.GetRequestType('Get')(
        instanceGroup=group_ref.Name(),
        region=group_ref.region,
        project=group_ref.project)
  results = compute_client.MakeRequests(requests=[(service, 'Get', request)])
  return list(UnwrapResponse(results, 'namedPorts'))


class FingerprintFetchException(exceptions.Error):
  """Exception thrown when there is a problem with getting fingerprint."""


def _GetGroupFingerprint(compute_client, group_ref):
  """Gets fingerprint of given instance group."""
  compute = compute_client.apitools_client
  if IsZonalGroup(group_ref):
    service = compute.instanceGroups
    request = compute.MESSAGES_MODULE.ComputeInstanceGroupsGetRequest(
        project=group_ref.project,
        zone=group_ref.zone,
        instanceGroup=group_ref.instanceGroup)
  else:
    service = compute.regionInstanceGroups
    request = compute.MESSAGES_MODULE.ComputeRegionInstanceGroupsGetRequest(
        project=group_ref.project,
        region=group_ref.region,
        instanceGroup=group_ref.instanceGroup)

  errors = []
  resources = compute_client.MakeRequests(
      requests=[(service, 'Get', request)],
      errors_to_collect=errors)

  if errors:
    utils.RaiseException(
        errors,
        FingerprintFetchException,
        error_message='Could not set named ports for resource:')
  return resources[0].fingerprint


def GetSetNamedPortsRequestForGroup(compute_client, group_ref, ports):
  """Returns a request to get named ports and service to send request.

  Args:
    compute_client: GCE API client,
    group_ref: reference to instance group (zonal or regional),
    ports: list of named ports to set

  Returns:
    request, message to send in order to set named ports on instance group,
    service, service where request should be sent
      - regionInstanceGroups for regional groups
      - instanceGroups for zonal groups
  """
  compute = compute_client.apitools_client
  messages = compute_client.messages
  # Instance group fingerprint will be used for optimistic locking. Each
  # modification of instance group changes the fingerprint. This request will
  # fail if instance group fingerprint does not match fingerprint sent in
  # request.
  fingerprint = _GetGroupFingerprint(compute_client, group_ref)
  if IsZonalGroup(group_ref):
    request_body = messages.InstanceGroupsSetNamedPortsRequest(
        fingerprint=fingerprint,
        namedPorts=ports)
    return messages.ComputeInstanceGroupsSetNamedPortsRequest(
        instanceGroup=group_ref.Name(),
        instanceGroupsSetNamedPortsRequest=request_body,
        zone=group_ref.zone,
        project=group_ref.project), compute.instanceGroups
  else:
    request_body = messages.RegionInstanceGroupsSetNamedPortsRequest(
        fingerprint=fingerprint,
        namedPorts=ports)
    return messages.ComputeRegionInstanceGroupsSetNamedPortsRequest(
        instanceGroup=group_ref.Name(),
        regionInstanceGroupsSetNamedPortsRequest=request_body,
        region=group_ref.region,
        project=group_ref.project), compute.regionInstanceGroups


def ValidateAndParseNamedPortsArgs(messages, named_ports):
  """Validates named ports flags."""
  ports = []
  for named_port in named_ports:
    if named_port.count(':') != 1:
      raise calliope_exceptions.InvalidArgumentException(
          named_port, 'Named ports should follow NAME:PORT format.')
    host, port = named_port.split(':')
    if not port.isdigit():
      raise calliope_exceptions.InvalidArgumentException(
          named_port, 'Named ports should follow NAME:PORT format.')
    ports.append(messages.NamedPort(name=host, port=int(port)))
  return ports


SET_NAMED_PORTS_HELP = {
    'brief': 'Sets the list of named ports for an instance group',
    'DESCRIPTION': """
Named ports are key:value pairs metadata representing
the service name and the port that it's running on. Named ports
can be assigned to an instance group, which
indicates that the service is available on all instances in the
group. This information is used by Application Load Balancers
and proxy Network Load Balancers.

*{command}* sets the list of named ports for all instances
in an instance group.

Note: Running this command will clear all existing named ports.
""",
    'EXAMPLES': """
For example, to apply the named ports to an entire instance group:

  $ {command} example-instance-group --named-ports=example-service:1111 --zone=us-central1-a

The above example will assign a name 'example-service' for port 1111
to the instance group called 'example-instance-group' in the
``us-central1-a'' zone. The command removes any named ports that are
already set for this instance group.

To clear named ports from instance group provide empty named ports
list as parameter:

  $ {command} example-instance-group --named-ports="" --zone=us-central1-a
""",
}


def CreateInstanceReferences(resources, compute_client, igm_ref,
                             instance_names_or_urls):
  """Creates reference to instances in instance group (zonal or regional).

  Args:
    resources: Resources parser for the client.
    compute_client: Client for the current release track.
    igm_ref: URL to the target IGM.
    instance_names_or_urls: names or full URLs of target instances.

  Returns:
    A dict where instance names are keys, and corresponding references are
    values. Unresolved names are present in dict with value None.
  """
  _InstanceNameWithReference = collections.namedtuple(
      'InstanceNameWithReference', ['instance_name', 'instance_reference'])
  instance_references = []
  # Make sure we don't have URLs here.
  names_to_resolve = [
      path_simplifier.Name(name_or_url)
      for name_or_url in instance_names_or_urls
  ]
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    for instance_name in names_to_resolve:
      instance_ref = resources.Parse(
          instance_name,
          params={
              'project': igm_ref.project,
              'zone': igm_ref.zone,
          },
          collection='compute.instances')
      instance_references.append(
          _InstanceNameWithReference(
              instance_name=instance_name,
              instance_reference=instance_ref.SelfLink()))
    return instance_references
  elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    service = compute_client.apitools_client.regionInstanceGroupManagers
    request = service.GetRequestType('ListManagedInstances')(
        instanceGroupManager=igm_ref.Name(),
        region=igm_ref.region,
        project=igm_ref.project)
    resolved_references = {}
    for instance_ref in compute_client.MakeRequests(
        requests=[(service, 'ListManagedInstances', request)]):
      resolved_references[path_simplifier.Name(
          instance_ref.instance)] = instance_ref.instance
    for instance_name in names_to_resolve:
      if instance_name in resolved_references:
        instance_references.append(
            _InstanceNameWithReference(
                instance_name=instance_name,
                instance_reference=resolved_references[instance_name]))
      else:
        instance_references.append(
            _InstanceNameWithReference(
                instance_name=instance_name, instance_reference=None))
    return instance_references
  else:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))


def SplitInstancesInRequest(request,
                            request_field,
                            max_length=INSTANCES_MAX_LENGTH):
  """Split request into parts according to max_length limit.

  Example:
    requests = SplitInstancesInRequest(
          self.messages.
          ComputeInstanceGroupManagersAbandonInstancesRequest(
              instanceGroupManager=igm_ref.Name(),
              instanceGroupManagersAbandonInstancesRequest=(
                  self.messages.InstanceGroupManagersAbandonInstancesRequest(
                      instances=instances,
                  )
              ),
              project=igm_ref.project,
              zone=igm_ref.zone,
          ), 'instanceGroupManagersAbandonInstancesRequest')

  Then:
    return client.MakeRequests(LiftRequestsList(service, method, requests))

  Args:
    request: _messages.Message, request to split
    request_field: str, name of property inside request holding instances field
    max_length: int, max_length of instances property

  Returns:
    List of requests with instances field length limited by max_length.
  """
  result = []
  all_instances = getattr(request, request_field).instances or []
  n = len(all_instances)
  for i in range(0, n, max_length):
    request_part = encoding.CopyProtoMessage(request)
    field = getattr(request_part, request_field)
    field.instances = all_instances[i:i+max_length]
    result.append(request_part)
  return result


def GenerateRequestTuples(service, method, requests):
  """(a, b, [c]) -> [(a, b, c)]."""
  for request in requests:
    yield (service, method, request)


# TODO(b/36799480) Parallelize instance_groups_utils.MakeRequests
def MakeRequestsAndGetStatusPerInstance(client, requests,
                                        instances_holder_field,
                                        errors_to_collect):
  """Make *-instances requests with feedback per instance.

  Args:
    client: Compute client.
    requests: [(service, method, request)].
    instances_holder_field: name of field inside request holding list of
      instances.
    errors_to_collect: A list for capturing errors. If any response contains an
      error, it is added to this list.

  Returns:
    A list of request statuses per instance. Requests status is a dictionary
    object, see SendInstancesRequestsAndPostProcessOutputs for details.
  """

  # Make requests and collect errors for each.
  request_results = []
  for service, method, request in requests:
    errors = []
    client.MakeRequests([(service, method, request)], errors)
    request_results.append((request, errors))
    errors_to_collect.extend(errors)

  # Determine status of instances.
  status_per_instance = []
  for request, errors in request_results:
    # Currently, any validation failure means that whole request is rejected.
    if errors:
      instance_status = 'FAIL'
    else:
      instance_status = 'SUCCESS'
    for instance in getattr(request, instances_holder_field).instances:
      status_per_instance.append({
          'selfLink': instance,
          'instanceName': path_simplifier.Name(instance),
          'status': instance_status
      })

  return status_per_instance


def ExtractSkippedInstancesAndCollectOtherWarnings(operation,
                                                   warnings_to_collect):
  """Extract from operation instances skipped due to graceful validation.

  Args:
    operation: Operation containing warnings.
    warnings_to_collect: A list to collect warnings unrelated to graceful
      validation.

  Returns:
    Dict from resource path of a skipped instance to validation error.
  """
  skipped_instances = dict()
  for warning in operation.warnings or []:
    # Check code. If not related to graceful validation, collect warning to
    # print later.
    if warning.code != warning.CodeValueValuesEnum.NOT_CRITICAL_ERROR:
      warnings_to_collect.append(warning.message)
      continue
    skipped_instance_path = None
    is_graceful_validation_warning = False
    # Use metadata to determine if warning is related to validation error and to
    # collect skipped instance's path.
    for warning_metadata in warning.data or []:
      if warning_metadata.key == 'instance':
        skipped_instance_path = warning_metadata.value
      if ((warning_metadata.key == 'validation_error') or
          (warning_metadata.key == 'validation_outcome')):
        is_graceful_validation_warning = True
    if is_graceful_validation_warning and skipped_instance_path:
      skipped_instances[skipped_instance_path] = warning.message
    else:
      # Not a graceful validation warning. Collect to print later.
      warnings_to_collect.append(warning.message)
  return skipped_instances


def MakeRequestsAndGetStatusPerInstanceFromOperation(client, requests,
                                                     instances_holder_field,
                                                     warnings_to_collect,
                                                     errors_to_collect):
  """Make *-instances requests with feedback per instance.

  Specialized version of MakeRequestsAndGetStatusPerInstance. Checks operations
  for warnings presence to evaluate statuses per instance. Gracefully validated
  requests may produce warnings on operations, indicating instances skipped.
  It would be merged with MakeRequestsAndGetStatusPerInstance after we see
  there's no issues with this implementation.

  Args:
    client: Compute client.
    requests: [(service, method, request)].
    instances_holder_field: name of field inside request holding list of
      instances.
    warnings_to_collect: A list for capturing warnings. If any completed
      operation will contain skipped instances, function will append warning
      suggesting how to find additional details on the operation, warnings
      unrelated to graceful validation will be collected as is.
    errors_to_collect: A list for capturing errors. If any response contains an
      error, it is added to this list.

  Returns:
    See MakeRequestsAndGetStatusPerInstance.
  """

  # Make requests and collect errors for each.
  request_results = []

  for service, method, request in requests:
    errors = []
    operations = client.MakeRequests([(service, method, request)],
                                     errors,
                                     log_warnings=False,
                                     no_followup=True,
                                     always_return_operation=True)
    # There should be only one operation in the list.
    [operation] = operations or [None]
    request_results.append((request, operation, errors))
    errors_to_collect.extend(errors)

  # Determine status of instances.
  status_per_instance = []
  for request, operation, errors in request_results:
    # If there's any errors, we assume that operation failed for all instances.
    if errors:
      for instance in getattr(request, instances_holder_field).instances:
        status_per_instance.append({
            'selfLink': instance,
            'instanceName': path_simplifier.Name(instance),
            'status': 'FAIL'
        })
    else:
      # Mimicking default logging in request_helper.
      if operation.targetLink:
        log.status.write('Updated [{0}].\n'.format(operation.targetLink))

      skipped_instances = ExtractSkippedInstancesAndCollectOtherWarnings(
          operation, warnings_to_collect)

      for instance in getattr(request, instances_holder_field).instances:
        # Extract public path of an instance from URI. Public path is a part of
        # instance URI, which starts with 'projects/'
        instance_path = instance[instance.find('/projects/') + 1:]
        validation_error = None
        if instance_path in skipped_instances:
          instance_status = 'SKIPPED'
          validation_error = skipped_instances[instance_path]
        else:
          instance_status = 'SUCCESS'
        status_per_instance.append({
            'selfLink': instance,
            'instanceName': path_simplifier.Name(instance),
            'status': instance_status,
            'validationError': validation_error
        })
  return status_per_instance


def SendAllInstancesRequest(api_holder, method_name, request_template,
                            all_instances_holder_field, igm_ref):
  """Prepare *-instances request with --all-instances flag and format output.

  Args:
    api_holder: Compute API holder.
    method_name: Name of the (region) instance groups managers service method to
      call.
    request_template: Partially filled *-instances request (no instances).
    all_instances_holder_field: Name of the field inside request holding
      allInstances field.
    igm_ref: URL to the target IGM.

  Returns:
    Empty list (for consistency with a command version using list of instances).
  """
  client = api_holder.client
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    service = client.apitools_client.instanceGroupManagers
  elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    service = client.apitools_client.regionInstanceGroupManagers
  else:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))

  getattr(request_template, all_instances_holder_field).allInstances = True

  errors = []
  client.MakeRequests([(service, method_name, request_template)], errors)

  if errors:
    raise utils.RaiseToolException(errors)

  # We return empty list for consistency with the format of result when
  # instances are specified and requests are sent in chunks.
  return []


def SendInstancesRequestsAndPostProcessOutputs(
    api_holder,
    method_name,
    request_template,
    instances_holder_field,
    igm_ref,
    instances,
    per_instance_status_enabled=False):
  """Make *-instances requests and format output.

  Method resolves instance references, splits them to make batch of requests,
  adds to results statuses for unresolved instances, and yields all statuses
  raising errors, if any, in the end.

  Args:
    api_holder: Compute API holder.
    method_name: Name of the (region) instance groups managers service method to
      call.
    request_template: Partially filled *-instances request (no instances).
    instances_holder_field: Name of the field inside request holding instances
      field.
    igm_ref: URL to the target IGM.
    instances: A list of names of the instances to apply method to.
    per_instance_status_enabled: Enable functionality parsing resulting
      operation for graceful validation related warnings to allow per-instance
      status output. The plan is to gradually enable this for all per-instance
      commands in GA (even where graceful validation is not available / not
      used).

  Yields:
    A list of request statuses per instance. Requests status is a dictionary
    object with link to an instance keyed with 'selfLink', instance name keyed
    with 'instanceName', and status indicating if operation succeeded for
    instance keyed with 'status'. Status might be 'FAIL', 'SUCCESS', 'SKIPPED'
    in case of graceful validation, or 'MEMBER_NOT_FOUND' (in case of regional
    MIGs, when instance name cannot be resolved).
  """
  client = api_holder.client
  if igm_ref.Collection() == 'compute.instanceGroupManagers':
    service = client.apitools_client.instanceGroupManagers
  elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
    service = client.apitools_client.regionInstanceGroupManagers
  else:
    raise ValueError('Unknown reference type {0}'.format(igm_ref.Collection()))

  instances_with_references = CreateInstanceReferences(api_holder.resources,
                                                       client, igm_ref,
                                                       instances)
  resolved_references = [
      instance.instance_reference
      for instance in instances_with_references
      if instance.instance_reference
  ]
  getattr(request_template,
          instances_holder_field).instances = resolved_references
  requests = SplitInstancesInRequest(request_template, instances_holder_field)
  request_tuples = GenerateRequestTuples(service, method_name, requests)

  errors_to_collect = []
  warnings_to_collect = []

  request_status_per_instance = []
  if per_instance_status_enabled:
    request_status_per_instance.extend(
        MakeRequestsAndGetStatusPerInstanceFromOperation(
            client, request_tuples, instances_holder_field, warnings_to_collect,
            errors_to_collect))
  else:
    request_status_per_instance.extend(
        MakeRequestsAndGetStatusPerInstance(client, request_tuples,
                                            instances_holder_field,
                                            errors_to_collect))

  unresolved_instance_names = [
      instance.instance_name
      for instance in instances_with_references
      if not instance.instance_reference
  ]
  request_status_per_instance.extend([
      dict(instanceName=name, status='MEMBER_NOT_FOUND')
      for name in unresolved_instance_names
  ])

  for status in request_status_per_instance:
    yield status

  if warnings_to_collect:
    log.warning(
        utils.ConstructList('Some requests generated warnings:',
                            warnings_to_collect))
  if errors_to_collect:
    raise utils.RaiseToolException(errors_to_collect)


class InstanceGroupFilteringMode(enum.Enum):
  """Filtering mode for Instance Groups based on dynamic properties."""
  ALL_GROUPS = 1
  ONLY_MANAGED_GROUPS = 2
  ONLY_UNMANAGED_GROUPS = 3


def ComputeInstanceGroupManagerMembership(
    compute_holder, items, filter_mode=InstanceGroupFilteringMode.ALL_GROUPS):
  """Add information if instance group is managed.

  Args:
    compute_holder: ComputeApiHolder, The compute API holder
    items: list of instance group messages,
    filter_mode: InstanceGroupFilteringMode, managed/unmanaged filtering options
  Returns:
    list of instance groups with computed dynamic properties
  """
  client = compute_holder.client
  resources = compute_holder.resources

  errors = []
  items = list(items)
  zone_links = set([ig['zone'] for ig in items if 'zone' in ig])

  project_to_zones = {}
  for zone in zone_links:
    zone_ref = resources.Parse(
        zone,
        params={
            'project': properties.VALUES.core.project.GetOrFail,
        },
        collection='compute.zones')
    if zone_ref.project not in project_to_zones:
      project_to_zones[zone_ref.project] = set()
    project_to_zones[zone_ref.project].add(zone_ref.zone)

  zonal_instance_group_managers = []
  for project, zones in six.iteritems(project_to_zones):
    zonal_instance_group_managers.extend(lister.GetZonalResources(
        service=client.apitools_client.instanceGroupManagers,
        project=project,
        requested_zones=zones,
        filter_expr=None,
        http=client.apitools_client.http,
        batch_url=client.batch_url,
        errors=errors))

  regional_instance_group_managers = []
  if hasattr(client.apitools_client, 'regionInstanceGroups'):
    # regional instance groups are just in 'alpha' API
    region_links = set([ig['region'] for ig in items if 'region' in ig])
    project_to_regions = {}
    for region in region_links:
      region_ref = resources.Parse(region, collection='compute.regions')
      if region_ref.project not in project_to_regions:
        project_to_regions[region_ref.project] = set()
      project_to_regions[region_ref.project].add(region_ref.region)
    for project, regions in six.iteritems(project_to_regions):
      regional_instance_group_managers.extend(lister.GetRegionalResources(
          service=client.apitools_client.regionInstanceGroupManagers,
          project=project,
          requested_regions=regions,
          filter_expr=None,
          http=client.apitools_client.http,
          batch_url=client.batch_url,
          errors=errors))

  instance_group_managers = (
      list(zonal_instance_group_managers)
      + list(regional_instance_group_managers))
  instance_group_managers_refs = set([
      path_simplifier.ScopedSuffix(igm.selfLink)
      for igm in instance_group_managers])

  if errors:
    utils.RaiseToolException(errors)

  results = []
  for item in items:
    self_link = item['selfLink']
    igm_self_link = self_link.replace(
        '/instanceGroups/', '/instanceGroupManagers/')
    scoped_suffix = path_simplifier.ScopedSuffix(igm_self_link)
    is_managed = scoped_suffix in instance_group_managers_refs

    if (is_managed and
        filter_mode == InstanceGroupFilteringMode.ONLY_UNMANAGED_GROUPS):
      continue
    elif (not is_managed and
          filter_mode == InstanceGroupFilteringMode.ONLY_MANAGED_GROUPS):
      continue

    item['isManaged'] = ('Yes' if is_managed else 'No')
    if is_managed:
      item['instanceGroupManagerUri'] = igm_self_link
    results.append(item)

  return results
