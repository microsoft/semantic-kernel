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
"""Annotates the resource types with extra information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.protorpclite import messages

from googlecloudsdk.api_lib.compute import instance_utils
from googlecloudsdk.api_lib.compute import path_simplifier
from googlecloudsdk.api_lib.compute import property_selector
import six
import six.moves.http_client


def _FirewallRulesToCell(firewall):
  """Returns a compact string describing the firewall rules."""
  rules = []
  for allowed in firewall.get('allowed', []):
    protocol = allowed.get('IPProtocol')
    if not protocol:
      continue

    port_ranges = allowed.get('ports')
    if port_ranges:
      for port_range in port_ranges:
        rules.append('{0}:{1}'.format(protocol, port_range))
    else:
      rules.append(protocol)

  return ','.join(rules)


def _TargetPoolHealthChecksToCell(target_pool):
  """Comma-joins the names of health checks of the given target pool."""
  return ','.join(path_simplifier.Name(check) for check in
                  target_pool.get('healthChecks', []))


def _FirewallSourceRangesToCell(firewall):
  """Comma-joins the source ranges of the given firewall rule."""
  return ','.join(firewall.get('sourceRanges', []))


def _FirewallSourceTagsToCell(firewall):
  """Comma-joins the source tags of the given firewall rule."""
  return ','.join(firewall.get('sourceTags', []))


def _FirewallTargetTagsToCell(firewall):
  """Comma-joins the target tags of the given firewall rule."""
  return ','.join(firewall.get('targetTags', []))


def _ForwardingRuleTarget(forwarding_rule):
  """Gets the API-level target or backend-service of the given rule."""
  backend_service = forwarding_rule.get('backendService', None)
  if backend_service is not None:
    return backend_service
  else:
    return forwarding_rule.get('target', None)


def _StatusToCell(zone_or_region):
  """Returns status of a machine with deprecation information if applicable."""
  deprecated = zone_or_region.get('deprecated', '')
  if deprecated:
    return '{0} ({1})'.format(zone_or_region.get('status'),
                              deprecated.get('state'))
  else:
    return zone_or_region.get('status')


def _DeprecatedDateTimeToCell(zone_or_region):
  """Returns the turndown timestamp of a deprecated machine or ''."""
  deprecated = zone_or_region.get('deprecated', '')
  if deprecated:
    return deprecated.get('deleted')
  else:
    return ''


def _QuotaToCell(metric, is_integer=True):
  """Returns a function that can format the given quota as usage/limit."""

  def QuotaToCell(region):
    """Formats the metric from the parent function."""
    for quota in region.get('quotas', []):
      if quota.get('metric') != metric:
        continue

      if is_integer:
        return '{0:6}/{1}'.format(
            int(quota.get('usage')),
            int(quota.get('limit')))
      else:
        return '{0:7.2f}/{1:.2f}'.format(
            quota.get('usage'),
            quota.get('limit'))

    return ''

  return QuotaToCell


def _LocationName(instance_group):
  """Returns a location name, could be region name or zone name."""
  if 'zone' in instance_group:
    return path_simplifier.Name(instance_group['zone'])
  elif 'region' in instance_group:
    return path_simplifier.Name(instance_group['region'])
  else:
    return None


def _LocationScopeType(instance_group):
  """Returns a location scope type, could be region or zone."""
  if 'zone' in instance_group:
    return 'zone'
  elif 'region' in instance_group:
    return 'region'
  else:
    return None


def _MachineTypeMemoryToCell(machine_type):
  """Returns the memory of the given machine type in GB."""
  memory = machine_type.get('memoryMb')
  if memory:
    return '{0:5.2f}'.format(float(memory) / 2**10)
  else:
    return ''


def _FormatCustomMachineTypeName(mt):
  """Checks for custom machine type and modifies output.

  Args:
    mt: machine type to be formatted

  Returns:
    If mt was a custom type, then it will be formatted into the desired custom
      machine type output. Otherwise, it is returned unchanged.

  Helper function for _MachineTypeNameToCell
  """
  custom_family, custom_cpu, custom_ram = \
    instance_utils.GetCpuRamVmFamilyFromCustomName(mt)
  if custom_cpu and custom_ram and custom_family:
    # Restricting output to 2 decimal places
    custom_ram_gb = '{0:.2f}'.format(custom_ram / (2**10))
    mt = 'custom ({0}, {1} vCPU, {2} GiB)'.format(custom_family, custom_cpu,
                                                  custom_ram_gb)
  return mt


def _MachineTypeNameToCell(machine_type):
  """Returns the formatted name of the given machine type.

  Most machine types will be untouched, with the exception of the custom machine
  type. This modifies the 'custom-N-M' custom machine types with
  'custom (N vCPU, M GiB)'.

  For example, given the following custom machine_type:

    custom-2-3500

  This function will return:

    custom (2 vCPU, 3.41 GiB)

  in the MACHINE_TYPE field when listing out the current instances.

  Args:
    machine_type: The machine type of the given instance

  Returns:
    A formatted version of the given custom machine type (as shown in example
    in docstring above).
  """
  mt = machine_type.get('properties', machine_type).get('machineType')
  if mt:
    return _FormatCustomMachineTypeName(mt)
  return mt


def FormatDescribeMachineTypeName(resources, com_path):
  """Formats a custom machine type when 'instances describe' is called.

  Args:
    resources: dict of resources available for the instance in question
    com_path: command path of the calling command

  Returns:
    If input is a custom type, returns the formatted custom machine type.
      Otherwise, returns None.
  """
  if ('instances' in com_path) and ('describe' in com_path):
    if not resources:
      return None
    if 'machineType' not in resources:
      return None
    mt_splitlist = resources['machineType'].split('/')
    mt = mt_splitlist[-1]
    if 'custom' not in mt:
      return None
    formatted_mt = _FormatCustomMachineTypeName(mt)
    mt_splitlist[-1] = formatted_mt
    return '/'.join(mt_splitlist)
  else:
    return None


def _OperationHttpStatusToCell(operation):
  """Returns the HTTP response code of the given operation."""
  if operation.get('status') == 'DONE':
    return operation.get('httpErrorStatusCode') or six.moves.http_client.OK
  else:
    return ''


def _ProjectToCell(resource):
  """Returns the project name of the given resource."""
  self_link = resource.get('selfLink')
  if self_link:
    return path_simplifier.ProjectSuffix(self_link).split('/')[0]
  else:
    return ''


def _MembersToCell(group):
  members = group.get('members')
  if members:
    return len(members)
  # Must be '0' instead of 0 to pass comparison 0 or ''.
  return '0'


def _BackendsToCell(backend_service):
  """Comma-joins the names of the backend services."""
  return ','.join(backend.get('group')
                  for backend in backend_service.get('backends', []))


def _RoutesNextHopToCell(route):
  """Returns the next hop value in a compact form."""
  if route.get('nextHopInstance'):
    return path_simplifier.ScopedSuffix(route.get('nextHopInstance'))
  elif route.get('nextHopGateway'):
    return path_simplifier.ScopedSuffix(route.get('nextHopGateway'))
  elif route.get('nextHopIp'):
    return route.get('nextHopIp')
  elif route.get('nextHopVpnTunnel'):
    return path_simplifier.ScopedSuffix(route.get('nextHopVpnTunnel'))
  elif route.get('nextHopPeering'):
    return route.get('nextHopPeering')
  else:
    return ''


def _TargetProxySslCertificatesToCell(target_proxy):
  """Joins the names of ssl certificates of the given HTTPS or SSL proxy."""
  return ','.join(path_simplifier.Name(cert) for cert in
                  target_proxy.get('sslCertificates', []))


def _ProtobufDefinitionToFields(message_class):
  """Flattens the fields in a protocol buffer definition.

  For example, given the following definition:

    message Point {
      required int32 x = 1;
      required int32 y = 2;
      optional string label = 3;
    }

    message Polyline {
      repeated Point point = 1;
      optional string label = 2;
    }

  a call to this function with the Polyline class would produce:

    ['label',
     'point[].label',
     'point[].x',
     'point[].y']

  Args:
    message_class: A class that inherits from protorpc.self.messages.Message
        and defines a protocol buffer.

  Yields:
    The flattened fields, in non-decreasing order.
  """
  for field in sorted(message_class.all_fields(), key=lambda field: field.name):
    if isinstance(field, messages.MessageField):
      for remainder in _ProtobufDefinitionToFields(field.type):
        if field.repeated:
          yield field.name + '[].' + remainder
        else:
          yield field.name + '.' + remainder
    else:
      if field.repeated:
        yield field.name + '[]'
      else:
        yield field.name


_InternalSpec = collections.namedtuple(
    'Spec',
    ['message_class_name', 'table_cols', 'transformations', 'editables'])

_SPECS_V1 = {
    'addresses': _InternalSpec(
        message_class_name='Address',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('ADDRESS', 'address'),
            ('STATUS', 'status'),
        ],
        transformations=[
            ('region', path_simplifier.Name),
            ('users[]', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'autoscalers': _InternalSpec(
        message_class_name='Autoscaler',
        table_cols=[
            ('NAME', 'name'),
            ('TARGET', 'target'),
            ('POLICY', 'autoscalingPolicy'),
        ],
        transformations=[
            ('zone', path_simplifier.Name),
            ('target', path_simplifier.Name),
        ],
        editables=None,
    ),

    'backendBuckets': _InternalSpec(
        message_class_name='BackendBucket',
        table_cols=[
            ('NAME', 'name'),
            ('GCS_BUCKET_NAME', 'bucketName'),
            ('ENABLE_CDN', 'enableCdn')
        ],
        transformations=[
            ('enableCdn', lambda x: str(x).lower()),
        ],
        editables=[
            'bucketName'
            'description',
            'enableCdn',
        ]),

    'backendServices': _InternalSpec(
        message_class_name='BackendService',
        table_cols=[
            ('NAME', 'name'),
            ('BACKENDS', _BackendsToCell),
            ('PROTOCOL', 'protocol'),
        ],
        transformations=[
            ('backends[].group', path_simplifier.ScopedSuffix),
        ],
        editables=[
            'backends',
            'description',
            'enableCDN',
            'healthChecks',
            'iap.enabled',
            'iap.oauth2ClientId',
            'iap.oauth2ClientSecret',
            'port',
            'portName',
            'protocol',
            'timeoutSec',
        ],
    ),

    'backendServiceGroupHealth': _InternalSpec(
        message_class_name='BackendServiceGroupHealth',
        table_cols=[
            ],
        transformations=[
            ('healthStatus[].instance', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'disks': _InternalSpec(
        message_class_name='Disk',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('SIZE_GB', 'sizeGb'),
            ('TYPE', 'type'),
            ('STATUS', 'status'),
        ],
        transformations=[
            ('sourceSnapshot', path_simplifier.Name),
            ('type', path_simplifier.Name),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'diskTypes': _InternalSpec(
        message_class_name='DiskType',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('VALID_DISK_SIZES', 'validDiskSize'),
        ],
        transformations=[
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'firewalls': _InternalSpec(
        message_class_name='Firewall',
        table_cols=[
            ('NAME', 'name'),
            ('NETWORK', 'network'),
            ('SRC_RANGES', _FirewallSourceRangesToCell),
            ('RULES', _FirewallRulesToCell),
            ('SRC_TAGS', _FirewallSourceTagsToCell),
            ('TARGET_TAGS', _FirewallTargetTagsToCell),
        ],
        transformations=[
            ('network', path_simplifier.Name),
        ],
        editables=None,
    ),

    'forwardingRules': _InternalSpec(
        message_class_name='ForwardingRule',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('IP_ADDRESS', 'IPAddress'),
            ('IP_PROTOCOL', 'IPProtocol'),
            ('TARGET', _ForwardingRuleTarget),
        ],
        transformations=[
            ('region', path_simplifier.Name),
            ('target', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'groups': _InternalSpec(
        message_class_name='Group',
        table_cols=[
            ('NAME', 'name'),
            ('NUM_MEMBERS', _MembersToCell),
            ('DESCRIPTION', 'description'),
        ],
        transformations=[],
        editables=[],
    ),

    'healthChecks': _InternalSpec(
        message_class_name='HealthCheck',
        table_cols=[
            ('NAME', 'name'),
            ('PROTOCOL', 'type'),
        ],
        transformations=[],
        editables=None,
    ),

    'httpHealthChecks': _InternalSpec(
        message_class_name='HttpHealthCheck',
        table_cols=[
            ('NAME', 'name'),
            ('HOST', 'host'),
            ('PORT', 'port'),
            ('REQUEST_PATH', 'requestPath'),
        ],
        transformations=[
            ],
        editables=None,
    ),

    'httpsHealthChecks': _InternalSpec(
        message_class_name='HttpsHealthCheck',
        table_cols=[
            ('NAME', 'name'),
            ('HOST', 'host'),
            ('PORT', 'port'),
            ('REQUEST_PATH', 'requestPath'),
        ],
        transformations=[
            ],
        editables=None,
    ),

    'iap': _InternalSpec(
        message_class_name='BackendServiceIAP',
        table_cols=[
            ('NAME', 'name'),
            ('ENABLED', 'enabled'),
            ('OAUTH2_CLIENT_ID', 'oauth2ClientId'),
            ('OAUTH2_CLIENT_SECRET', 'oauth2ClientSecret'),
            ('OAUTH2_CLIENT_SECRET_SHA256', 'oauth2ClientSecretSha256'),
        ],
        transformations=[],
        editables=None,
    ),

    'images': _InternalSpec(
        message_class_name='Image',
        table_cols=[
            ('NAME', 'name'),
            ('PROJECT', _ProjectToCell),
            ('FAMILY', 'family'),
            ('DEPRECATED', 'deprecated.state'),
            ('STATUS', 'status'),
        ],
        transformations=[],
        editables=None,
    ),

    'instanceGroups': _InternalSpec(
        message_class_name='InstanceGroup',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('NETWORK', 'network'),
            ('MANAGED', 'isManaged'),
            ('INSTANCES', 'size'),
        ],
        transformations=[
            ('zone', path_simplifier.Name),
            ('size', str),
        ],
        editables=None,
    ),

    'instanceGroupManagers': _InternalSpec(
        message_class_name='InstanceGroupManager',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('BASE_INSTANCE_NAME', 'baseInstanceName'),
            ('SIZE', 'size'),
            ('TARGET_SIZE', 'targetSize'),
            ('INSTANCE_TEMPLATE', 'instanceTemplate'),
            ('AUTOSCALED', 'autoscaled'),
        ],
        transformations=[
            ('zone', path_simplifier.Name),
            ('instanceGroup', path_simplifier.Name),
            ('instanceTemplate', path_simplifier.Name),
        ],
        editables=None,
    ),

    'instances': _InternalSpec(
        message_class_name='Instance',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('MACHINE_TYPE', _MachineTypeNameToCell),
            ('PREEMPTIBLE', 'scheduling.preemptible'),
            ('INTERNAL_IP', 'networkInterfaces[].networkIP.notnull().list()'),
            ('EXTERNAL_IP',
             'networkInterfaces[].accessConfigs[0].natIP.notnull().list()'),
            ('STATUS', 'status'),
        ],
        transformations=[
            ('disks[].source', path_simplifier.Name),
            ('machineType', path_simplifier.Name),
            ('networkInterfaces[].network', path_simplifier.Name),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'instanceTemplates': _InternalSpec(
        message_class_name='InstanceTemplate',
        table_cols=[
            ('NAME', 'name'),
            ('MACHINE_TYPE', _MachineTypeNameToCell),
            ('PREEMPTIBLE', 'properties.scheduling.preemptible'),
            ('CREATION_TIMESTAMP', 'creationTimestamp'),
        ],
        transformations=[],
        editables=None,
    ),

    'machineTypes': _InternalSpec(
        message_class_name='MachineType',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('CPUS', 'guestCpus'),
            ('MEMORY_GB', _MachineTypeMemoryToCell),
            ('DEPRECATED', 'deprecated.state'),
        ],
        transformations=[
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'networks': _InternalSpec(
        message_class_name='Network',
        table_cols=[
            ('NAME', 'name'),
            ('MODE', 'x_gcloud_mode'),
            ('IPV4_RANGE', 'IPv4Range'),
            ('GATEWAY_IPV4', 'gatewayIPv4'),
        ],
        transformations=[],
        editables=None,
    ),

    'projects': _InternalSpec(
        message_class_name='Project',
        table_cols=[],  # We do not support listing projects since
        # there is only one project (and there is no
        # API support).
        transformations=[
            ],
        editables=None,
    ),

    'operations': _InternalSpec(
        message_class_name='Operation',
        table_cols=[
            ('NAME', 'name'),
            ('TYPE', 'operationType'),
            ('TARGET', 'targetLink'),
            ('HTTP_STATUS', _OperationHttpStatusToCell),
            ('STATUS', 'status'),
            ('TIMESTAMP', 'insertTime'),
        ],
        transformations=[
            ('targetLink', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'invalidations': _InternalSpec(
        message_class_name='Operation',
        table_cols=[
            ('DESCRIPTION', 'description'),
            ('HTTP_STATUS', _OperationHttpStatusToCell),
            ('STATUS', 'status'),
            ('TIMESTAMP', 'insertTime'),
        ],
        transformations=[
            ('targetLink', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'regionBackendServices': _InternalSpec(
        message_class_name='BackendService',
        table_cols=[
            ('NAME', 'name'),
            ('BACKENDS', _BackendsToCell),
            ('PROTOCOL', 'protocol'),
        ],
        transformations=[
            ('backends[].group', path_simplifier.ScopedSuffix),
        ],
        editables=[
            'backends',
            'description',
            'enableCDN',
            'healthChecks',
            'port',
            'portName',
            'protocol',
            'timeoutSec',
        ],
    ),

    'regions': _InternalSpec(
        message_class_name='Region',
        table_cols=[
            ('NAME', 'name'),
            ('CPUS', _QuotaToCell('CPUS', is_integer=False)),
            ('DISKS_GB', _QuotaToCell('DISKS_TOTAL_GB', is_integer=True)),
            ('ADDRESSES', _QuotaToCell('IN_USE_ADDRESSES', is_integer=True)),
            ('RESERVED_ADDRESSES',
             _QuotaToCell('STATIC_ADDRESSES', is_integer=True)),
            ('STATUS', _StatusToCell),
            ('TURNDOWN_DATE', _DeprecatedDateTimeToCell),
        ],
        transformations=[
            ('zones[]', path_simplifier.Name),
        ],
        editables=None,
    ),

    'routes': _InternalSpec(
        message_class_name='Route',
        table_cols=[
            ('NAME', 'name'),
            ('NETWORK', 'network'),
            ('DEST_RANGE', 'destRange'),
            ('NEXT_HOP', _RoutesNextHopToCell),
            ('PRIORITY', 'priority'),
        ],
        transformations=[
            ('network', path_simplifier.Name),
        ],
        editables=None,
    ),

    'snapshots': _InternalSpec(
        message_class_name='Snapshot',
        table_cols=[
            ('NAME', 'name'),
            ('DISK_SIZE_GB', 'diskSizeGb'),
            ('SRC_DISK', 'sourceDisk'),
            ('STATUS', 'status'),
        ],
        transformations=[
            ('sourceDisk', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'sslCertificates': _InternalSpec(
        message_class_name='Network',
        table_cols=[
            ('NAME', 'name'),
            ('CREATION_TIMESTAMP', 'creationTimestamp'),
        ],
        transformations=[],
        editables=None,
    ),

    'subnetworks': _InternalSpec(
        message_class_name='Subnetwork',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('NETWORK', 'network'),
            ('RANGE', 'ipCidrRange')
        ],
        transformations=[
            ('network', path_simplifier.Name),
            ('region', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetHttpProxies': _InternalSpec(
        message_class_name='TargetHttpProxy',
        table_cols=[
            ('NAME', 'name'),
            ('URL_MAP', 'urlMap'),
        ],
        transformations=[
            ('urlMap', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetHttpsProxies': _InternalSpec(
        message_class_name='TargetHttpsProxy',
        table_cols=[
            ('NAME', 'name'),
            ('SSL_CERTIFICATES', _TargetProxySslCertificatesToCell),
            ('URL_MAP', 'urlMap'),
        ],
        transformations=[
            ('sslCertificates[]', path_simplifier.Name),
            ('urlMap', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetSslProxies': _InternalSpec(
        message_class_name='TargetSslProxy',
        table_cols=[
            ('NAME', 'name'),
            ('PROXY_HEADER', 'proxyHeader'),
            ('SERVICE', 'service'),
            ('SSL_CERTIFICATES', _TargetProxySslCertificatesToCell)
        ],
        transformations=[
            ('sslCertificates[]', path_simplifier.Name),
            ('service', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetInstances': _InternalSpec(
        message_class_name='TargetInstance',
        table_cols=[
            ('NAME', 'name'),
            ('ZONE', 'zone'),
            ('INSTANCE', 'instance'),
            ('NAT_POLICY', 'natPolicy'),
        ],
        transformations=[
            ('instance', path_simplifier.Name),
            ('zone', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetPoolInstanceHealth': _InternalSpec(
        message_class_name='TargetPoolInstanceHealth',
        table_cols=[
            ],
        transformations=[
            ('healthStatus[].instance', path_simplifier.ScopedSuffix),
        ],
        editables=None,
    ),

    'targetPools': _InternalSpec(
        message_class_name='TargetPool',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('SESSION_AFFINITY', 'sessionAffinity'),
            ('BACKUP', 'backupPool'),
            ('HEALTH_CHECKS', _TargetPoolHealthChecksToCell),
        ],
        transformations=[
            ('backupPool', path_simplifier.Name),
            ('healthChecks[]', path_simplifier.Name),
            ('instances[]', path_simplifier.ScopedSuffix),
            ('region', path_simplifier.Name),
        ],
        editables=None,
    ),

    'targetVpnGateways': _InternalSpec(
        message_class_name='TargetVpnGateway',
        table_cols=[
            ('NAME', 'name'),
            ('NETWORK', 'network'),
            ('REGION', 'region')
        ],
        transformations=[
            ('network', path_simplifier.Name),
            ('region', path_simplifier.Name)],
        editables=None
    ),

    'users': _InternalSpec(
        message_class_name='User',
        table_cols=[
            ('NAME', 'name'),
            ('OWNER', 'owner'),
            ('DESCRIPTION', 'description'),
        ],
        transformations=[],
        editables=[],
    ),

    'zones': _InternalSpec(
        message_class_name='Zone',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('STATUS', _StatusToCell),
            ('TURNDOWN_DATE', _DeprecatedDateTimeToCell),
        ],
        transformations=[
            ('region', path_simplifier.Name),
        ],
        editables=None,
    ),

    'vpnTunnels': _InternalSpec(
        message_class_name='VpnTunnel',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('GATEWAY', 'targetVpnGateway'),
            ('PEER_ADDRESS', 'peerIp')
        ],
        transformations=[
            ('region', path_simplifier.Name),
            ('targetVpnGateway', path_simplifier.Name)],
        editables=None
    ),

    'routers': _InternalSpec(
        message_class_name='Router',
        table_cols=[
            ('NAME', 'name'),
            ('REGION', 'region'),
            ('NETWORK', 'network'),
        ],
        transformations=[
            ('network', path_simplifier.Name),
            ('region', path_simplifier.Name),
        ],
        editables=None,
    ),
}


_SPECS_BETA = _SPECS_V1.copy()
_SPECS_BETA['backendServices'] = _InternalSpec(
    message_class_name='BackendService',
    table_cols=[
        ('NAME', 'name'),
        ('BACKENDS', _BackendsToCell),
        ('PROTOCOL', 'protocol'),
    ],
    transformations=[
        ('backends[].group', path_simplifier.ScopedSuffix),
    ],
    editables=[
        'backends',
        'description',
        'enableCDN',
        'sessionAffinity',
        'affinityCookieTTL',
        'healthChecks',
        'iap.enabled',
        'iap.oauth2ClientId',
        'iap.oauth2ClientSecret',
        'port',
        'portName',
        'protocol',
        'timeoutSec',
    ],)
_SPECS_BETA['commitments'] = _InternalSpec(
    message_class_name='Commitment',
    table_cols=[
        ('NAME', 'name'),
        ('ENDS', 'endTimestamp'),
        ('REGION', 'region'),
        ('STATUS', 'status'),
    ],
    transformations=[],
    editables=[])


_SPECS_ALPHA = _SPECS_BETA.copy()

_SPECS_ALPHA['instanceGroups'] = _InternalSpec(
    message_class_name='InstanceGroup',
    table_cols=[
        ('NAME', 'name'),
        ('LOCATION', _LocationName),
        ('SCOPE', _LocationScopeType),
        ('NETWORK', 'network'),
        ('MANAGED', 'isManaged'),
        ('INSTANCES', 'size'),
    ],
    transformations=[
        ('size', str),
    ],
    editables=None,
)
_SPECS_ALPHA['instanceGroupManagers'] = _InternalSpec(
    message_class_name='InstanceGroupManager',
    table_cols=[
        ('NAME', 'name'),
        ('LOCATION', _LocationName),
        ('SCOPE', _LocationScopeType),
        ('BASE_INSTANCE_NAME', 'baseInstanceName'),
        ('SIZE', 'size'),
        ('TARGET_SIZE', 'targetSize'),
        ('INSTANCE_TEMPLATE', 'instanceTemplate'),
        ('AUTOSCALED', 'autoscaled'),
    ],
    transformations=[
        ('instanceGroup', path_simplifier.Name),
        ('instanceTemplate', path_simplifier.Name),
    ],
    editables=None,
    )


def _GetSpecsForVersion(api_version):
  """Get Specs for the given API version.

  This currently always returns _SPECS_V1, but is left here for the future,
  as a pattern for providing different specs for different versions.

  Args:
    api_version: A string identifying the API version, e.g. 'v1'.

  Returns:
    A map associating each message class name with an _InternalSpec object.
  """
  if api_version == 'v1' or api_version == 'v2beta1':
    return _SPECS_V1
  if 'alpha' in api_version:
    return _SPECS_ALPHA
  return _SPECS_BETA


Spec = collections.namedtuple(
    'Spec',
    ['message_class', 'fields', 'table_cols', 'transformations', 'editables'])


def GetSpec(resource_type, message_classes, api_version):
  """Returns a Spec for the given resource type."""
  spec = _GetSpecsForVersion(api_version)

  if resource_type not in spec:
    raise KeyError('"%s" not found in Specs for version "%s"' %
                   (resource_type, api_version))

  spec = spec[resource_type]

  table_cols = []
  for name, action in spec.table_cols:
    if isinstance(action, six.string_types):
      table_cols.append((name, property_selector.PropertyGetter(action)))
    elif callable(action):
      table_cols.append((name, action))
    else:
      raise ValueError('expected function or property in table_cols list: {0}'
                       .format(spec))

  message_class = getattr(message_classes, spec.message_class_name)
  fields = list(_ProtobufDefinitionToFields(message_class))
  return Spec(message_class=message_class,
              fields=fields,
              table_cols=table_cols,
              transformations=spec.transformations,
              editables=spec.editables)
