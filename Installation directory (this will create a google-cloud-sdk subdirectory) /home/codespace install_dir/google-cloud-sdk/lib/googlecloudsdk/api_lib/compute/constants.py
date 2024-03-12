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
"""Defines tool-wide constants."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import enum
import six


BYTES_IN_ONE_MB = 2 ** 20
BYTES_IN_ONE_GB = 2 ** 30

STANDARD_DISK_PERFORMANCE_WARNING_GB = 200
SSD_DISK_PERFORMANCE_WARNING_GB = 10

SSD_SMALL_PARTITION_GB = 375
SSD_LARGE_PARTITION_GB = 3000

# Disk types
DISK_TYPE_PD_STANDARD = 'pd-standard'
DISK_TYPE_PD_BALANCED = 'pd-balanced'
DISK_TYPE_PD_SSD = 'pd-ssd'
DISK_TYPE_PD_EXTREME = 'pd-extreme'
DISK_TYPE_HD_EXTREME = 'hyperdisk-extreme'
DISK_TYPE_HD_THROUGHPUT = 'hyperdisk-throughput'
DISK_TYPE_HD_BALANCED = 'hyperdisk-balanced'

# Provisioned IOPS for pd-extreme/cs-extreme disks
MIN_PROVISIONED_IOPS = 2500
MAX_PROVISIONED_IOPS = 300000
DEFAULT_PROVISIONED_IOPS = 100000

# Default size for each disk type
# TODO(b/233790191) Remove default disk sizes in gcloud.
DEFAULT_DISK_SIZE_GB_MAP = {
    DISK_TYPE_PD_STANDARD: 500,
    DISK_TYPE_PD_BALANCED: 100,
    DISK_TYPE_PD_SSD: 100,
    DISK_TYPE_PD_EXTREME: 1000,
    DISK_TYPE_HD_EXTREME: 1000,
    DISK_TYPE_HD_THROUGHPUT: 2048,
}

LEGACY_DISK_TYPE_LIST = [
    DISK_TYPE_PD_STANDARD,
    DISK_TYPE_PD_BALANCED,
    DISK_TYPE_PD_SSD,
    DISK_TYPE_PD_EXTREME,
]

# The maximum number of results that can be returned in a single list
# response.
MAX_RESULTS_PER_PAGE = 500

# Defaults for instance creation.
DEFAULT_ACCESS_CONFIG_NAME = 'external-nat'
DEFAULT_IPV6_ACCESS_CONFIG_NAME = 'external-v6-access-config'

CONFIDENTIAL_VM_TYPES = enum.Enum(
    'CONFIDENTIAL_VM_TYPES', ['SEV', 'SEV_SNP', 'TDX']
)

DEFAULT_MACHINE_TYPE = 'n1-standard-1'
DEFAULT_MACHINE_TYPE_FOR_CONFIDENTIAL_VMS = {
    CONFIDENTIAL_VM_TYPES.SEV: 'n2d-standard-2',
    CONFIDENTIAL_VM_TYPES.SEV_SNP: 'n2d-standard-2',
    CONFIDENTIAL_VM_TYPES.TDX: 'c3-standard-4',
}
DEFAULT_NETWORK = 'default'
DEFAULT_NETWORK_INTERFACE = 'nic0'
NETWORK_TIER_CHOICES_FOR_INSTANCE = (
    'PREMIUM', 'SELECT', 'STANDARD', 'FIXED_STANDARD')
NETWORK_INTERFACE_NIC_TYPE_CHOICES = ('VIRTIO_NET', 'GVNIC', 'RDMA')
NETWORK_INTERFACE_STACK_TYPE_CHOICES = ('IPV4_ONLY', 'IPV4_IPV6', 'IPV6_ONLY')
NETWORK_INTERFACE_IPV6_ONLY_STACK_TYPE = 'IPV6_ONLY'
NETWORK_INTERFACE_IGMP_QUERY_CHOICES = ('IGMP_QUERY_V2', 'IGMP_QUERY_DISABLED')
NETWORK_INTERFACE_IPV6_NETWORK_TIER_CHOICES = ('PREMIUM',)
ADV_NETWORK_TIER_CHOICES = ['DEFAULT', 'TIER_1']

DEFAULT_IMAGE_FAMILY = 'debian-11'
DEFAULT_IMAGE_FAMILY_FOR_CONFIDENTIAL_VMS = {
    CONFIDENTIAL_VM_TYPES.SEV: 'ubuntu-2204-lts',
    CONFIDENTIAL_VM_TYPES.SEV_SNP: 'ubuntu-2204-lts',
    CONFIDENTIAL_VM_TYPES.TDX: 'ubuntu-2304-amd64',
}

ImageAlias = collections.namedtuple(
    'ImageAlias', ['project', 'name_prefix', 'family'])

IMAGE_ALIASES = {
    'centos-6': ImageAlias(
        project='centos-cloud',
        name_prefix='centos-6',
        family='centos-6'),
    'centos-7': ImageAlias(
        project='centos-cloud',
        name_prefix='centos-7',
        family='centos-7'),
    'container-vm': ImageAlias(
        project='google-containers',
        name_prefix='container-vm',
        family='container-vm'),
    'cos': ImageAlias(
        project='cos-cloud',
        name_prefix='cos',
        family='cos'),
    'debian-8': ImageAlias(
        project='debian-cloud',
        name_prefix='debian-8-jessie',
        family='debian-8'),
    'fedora-coreos-stable': ImageAlias(
        project='fedora-coreos-cloud',
        name_prefix='fedora-coreos',
        family='fedora-coreos-stable'),
    'rhel-6': ImageAlias(
        project='rhel-cloud',
        name_prefix='rhel-6',
        family='rhel-6'),
    'rhel-7': ImageAlias(
        project='rhel-cloud',
        name_prefix='rhel-7',
        family='rhel-7'),
    'rhel-8': ImageAlias(
        project='rhel-cloud',
        name_prefix='rhel-8',
        family='rhel-8'),
    'sles-11': ImageAlias(
        project='suse-cloud',
        name_prefix='sles-11',
        family=None),
    'sles-12': ImageAlias(
        project='suse-cloud',
        name_prefix='sles-12',
        family=None),
    'ubuntu-12-04': ImageAlias(
        project='ubuntu-os-cloud',
        name_prefix='ubuntu-1204-precise',
        family='ubuntu-1204-lts'),
    'ubuntu-14-04': ImageAlias(
        project='ubuntu-os-cloud',
        name_prefix='ubuntu-1404-trusty',
        family='ubuntu-1404-lts'),
    'windows-2008-r2': ImageAlias(
        project='windows-cloud',
        name_prefix='windows-server-2008-r2',
        family='windows-2008-r2'),
    'windows-2012-r2': ImageAlias(
        project='windows-cloud',
        name_prefix='windows-server-2012-r2',
        family='windows-2012-r2'),
}

# These are like IMAGE_ALIASES, but don't show up in the alias list.
HIDDEN_IMAGE_ALIASES = {
    'gae-builder-vm': ImageAlias(
        project='goog-vmruntime-images',
        name_prefix='gae-builder-vm',
        family=None),
    'opensuse-13': ImageAlias(
        project='opensuse-cloud',
        name_prefix='opensuse-13',
        family=None),
}

WINDOWS_IMAGE_PROJECTS = [
    'windows-cloud',
    'windows-sql-cloud'
]
PUBLIC_IMAGE_PROJECTS = [
    'centos-cloud',
    'cos-cloud',
    'debian-cloud',
    'fedora-cloud',
    'fedora-coreos-cloud',
    'opensuse-cloud',
    'rhel-cloud',
    'rhel-sap-cloud',
    'rocky-linux-cloud',
    'suse-cloud',
    'suse-sap-cloud',
    'ubuntu-os-cloud',
    'ubuntu-os-pro-cloud',
] + WINDOWS_IMAGE_PROJECTS
PREVIEW_IMAGE_PROJECTS = []

# SSH-related constants.
SSH_KEYS_METADATA_KEY = 'ssh-keys'
SSH_KEYS_LEGACY_METADATA_KEY = 'sshKeys'
SSH_KEYS_BLOCK_METADATA_KEY = 'block-project-ssh-keys'
MAX_METADATA_VALUE_SIZE_IN_BYTES = 262144
SSH_KEY_TYPES = ('ssh-dss', 'ecdsa-sha2-nistp256', 'ssh-ed25519', 'ssh-rsa')

_STORAGE_RO = 'https://www.googleapis.com/auth/devstorage.read_only'
_LOGGING_WRITE = 'https://www.googleapis.com/auth/logging.write'
_MONITORING_WRITE = 'https://www.googleapis.com/auth/monitoring.write'
_MONITORING = 'https://www.googleapis.com/auth/monitoring'
_SERVICE_CONTROL_SCOPE = 'https://www.googleapis.com/auth/servicecontrol'
_SERVICE_MANAGEMENT_SCOPE = 'https://www.googleapis.com/auth/service.management.readonly'
_SOURCE_REPOS = 'https://www.googleapis.com/auth/source.full_control'
_SOURCE_REPOS_RO = 'https://www.googleapis.com/auth/source.read_only'
_PUBSUB = 'https://www.googleapis.com/auth/pubsub'
_STACKDRIVER_TRACE = 'https://www.googleapis.com/auth/trace.append'

DEFAULT_SCOPES = sorted([
    _STORAGE_RO, _LOGGING_WRITE, _MONITORING_WRITE, _SERVICE_CONTROL_SCOPE,
    _SERVICE_MANAGEMENT_SCOPE, _PUBSUB, _STACKDRIVER_TRACE,
])

GKE_DEFAULT_SCOPES = sorted([
    _STORAGE_RO,
    _LOGGING_WRITE,
    _MONITORING,
    _SERVICE_CONTROL_SCOPE,
    _SERVICE_MANAGEMENT_SCOPE,
    _STACKDRIVER_TRACE,
])

DEPRECATED_SQL_SCOPE_MSG = """\
DEPRECATION WARNING: https://www.googleapis.com/auth/sqlservice account scope
and `sql` alias do not provide SQL instance management capabilities and have
been deprecated. Please, use https://www.googleapis.com/auth/sqlservice.admin
or `sql-admin` to manage your Google SQL Service instances.
"""

DEPRECATED_SCOPES_MESSAGES = DEPRECATED_SQL_SCOPE_MSG

DEPRECATED_SCOPE_ALIASES = {'sql'}

SCOPES = {
    'bigquery': ['https://www.googleapis.com/auth/bigquery'],
    'cloud-platform': ['https://www.googleapis.com/auth/cloud-platform'],
    'cloud-source-repos': [_SOURCE_REPOS],
    'cloud-source-repos-ro': [_SOURCE_REPOS_RO],
    'compute-ro': ['https://www.googleapis.com/auth/compute.readonly'],
    'compute-rw': ['https://www.googleapis.com/auth/compute'],
    'default':
        DEFAULT_SCOPES,
    'gke-default':
        GKE_DEFAULT_SCOPES,
    'datastore': ['https://www.googleapis.com/auth/datastore'],
    'logging-write': [_LOGGING_WRITE],
    'monitoring': [_MONITORING],
    'monitoring-read': ['https://www.googleapis.com/auth/monitoring.read'],
    'monitoring-write': [_MONITORING_WRITE],
    'service-control': [_SERVICE_CONTROL_SCOPE],
    'service-management': [_SERVICE_MANAGEMENT_SCOPE],
    'sql': ['https://www.googleapis.com/auth/sqlservice'],
    'sql-admin': ['https://www.googleapis.com/auth/sqlservice.admin'],
    'trace': [_STACKDRIVER_TRACE],
    'storage-full': ['https://www.googleapis.com/auth/devstorage.full_control'],
    'storage-ro': [_STORAGE_RO],
    'storage-rw': ['https://www.googleapis.com/auth/devstorage.read_write'],
    'taskqueue': ['https://www.googleapis.com/auth/taskqueue'],
    'userinfo-email': ['https://www.googleapis.com/auth/userinfo.email'],
    'pubsub': ['https://www.googleapis.com/auth/pubsub'],
}


def ScopesHelp():
  """Returns the command help text markdown for scopes.

  Returns:
    The command help text markdown with scope intro text, aliases, and optional
    notes and/or warnings.
  """
  aliases = []
  for alias, value in sorted(six.iteritems(SCOPES)):
    if alias in DEPRECATED_SCOPE_ALIASES:
      alias = '{} (deprecated)'.format(alias)
    aliases.append('{0} | {1}'.format(alias, value[0]))
    for item in value[1:]:
      aliases.append('| ' + item)
  return """\
SCOPE can be either the full URI of the scope or an alias. *Default* scopes are
assigned to all instances. Available aliases are:

Alias | URI
--- | ---
{aliases}

{scope_deprecation_msg}
""".format(
    aliases='\n'.join(aliases),
    scope_deprecation_msg=DEPRECATED_SCOPES_MESSAGES)
