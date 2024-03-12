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
"""Commands for interacting with the Cloud NetApp Files Active Directory API resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.netapp import constants
from googlecloudsdk.api_lib.netapp import util as netapp_api_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class ActiveDirectoriesClient(object):
  """Wrapper for working with Active Directories in the Cloud NetApp Files API Client."""

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    if release_track == base.ReleaseTrack.ALPHA:
      self._adapter = AlphaActiveDirectoriesAdapter()
    elif release_track == base.ReleaseTrack.BETA:
      self._adapter = BetaActiveDirectoriesAdapter()
    elif release_track == base.ReleaseTrack.GA:
      self._adapter = ActiveDirectoriesAdapter()
    else:
      raise ValueError('[{}] is not a valid API version.'.format(
          netapp_api_util.VERSION_MAP[release_track]))

  @property
  def client(self):
    return self._adapter.client

  @property
  def messages(self):
    return self._adapter.messages

  def WaitForOperation(self, operation_ref):
    """Waits on the long-running operation until the done field is True.

    Args:
      operation_ref: the operation reference.

    Raises:
      waiter.OperationError: if the operation contains an error.

    Returns:
      the 'response' field of the Operation.
    """
    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(
            self.client.projects_locations_operations), operation_ref,
        'Waiting for [{0}] to finish'.format(operation_ref.Name()))

  def ParseActiveDirectoryConfig(self,
                                 name=None,
                                 domain=None,
                                 site=None,
                                 dns=None,
                                 net_bios_prefix=None,
                                 organizational_unit=None,
                                 aes_encryption=None,
                                 username=None,
                                 password=None,
                                 backup_operators=None,
                                 security_operators=None,
                                 kdc_hostname=None,
                                 kdc_ip=None,
                                 nfs_users_with_ldap=None,
                                 ldap_signing=None,
                                 encrypt_dc_connections=None,
                                 description=None,
                                 labels=None):
    """Parses the command line arguments for Create Active Directory into a config.

    Args:
      name: the name of the Active Directory
      domain: the domain name of the Active Directory
      site: the site of the Active Directory
      dns: the DNS server IP addresses for the Active Directory domain
      net_bios_prefix: the NetBIOS prefix name of the server
      organizational_unit: The organizational unit within the AD the user
        belongs to
      aes_encryption: Bool, if enabled, AES encryption will be enabled for
        SMB communication
      username: Username of the AD domain admin
      password: Password of the AD domain admin
      backup_operators: The backup operators AD group users list
      security_operators: Security operators AD domain users list
      kdc_hostname: Name of the AD machine
      kdc_ip: KDC Server IP address for the AD machine
      nfs_users_with_ldap: Bool, if enabled, will allow access to local users
        and LDAP users. Disable, if only needed for LDAP users
      ldap_signing: Bool that specifies whether or not LDAP traffic needs to
        be signed
      encrypt_dc_connections: Bool, if enabled, traffic between SMB server
        and DC will be encrypted
      description: the description of the Active Directory
      labels: the labels for the Active Directory

    Returns:
      The configuration that will be used as the request body for creating a
      Cloud NetApp Active Directory.
    """
    active_directory = self.messages.ActiveDirectory()
    active_directory.name = name
    active_directory.domain = domain
    active_directory.site = site
    active_directory.dns = dns
    active_directory.netBiosPrefix = net_bios_prefix
    active_directory.organizationalUnit = organizational_unit
    active_directory.aesEncryption = aes_encryption
    active_directory.username = username
    active_directory.password = password
    active_directory.backupOperators = (
        backup_operators if backup_operators else []
    )
    active_directory.securityOperators = (
        security_operators if security_operators else []
    )
    active_directory.nfsUsersWithLdap = nfs_users_with_ldap
    active_directory.kdcHostname = kdc_hostname
    active_directory.kdcIp = kdc_ip
    active_directory.ldapSigning = ldap_signing
    active_directory.encryptDcConnections = encrypt_dc_connections
    active_directory.description = description
    active_directory.labels = labels
    return active_directory

  def CreateActiveDirectory(self, activedirectory_ref, async_, config):
    """Create a Cloud NetApp Active Directory."""
    request = (
        self.messages.NetappProjectsLocationsActiveDirectoriesCreateRequest(
            parent=activedirectory_ref.Parent().RelativeName(),
            activeDirectoryId=activedirectory_ref.Name(),
            activeDirectory=config,
        )
    )
    create_op = self.client.projects_locations_activeDirectories.Create(request)
    if async_:
      return create_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        create_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)

  def ListActiveDirectories(self, location_ref, limit=None):
    """Make API calls to List active Cloud NetApp Active Directories.

    Args:
      location_ref: The parsed location of the listed NetApp Active Directories.
      limit: The number of Cloud NetApp Active Directories
        to limit the results to. This limit is passed to
        the server and the server does the limiting.

    Returns:
      Generator that yields the Cloud NetApp Active Directories.
    """
    request = self.messages.NetappProjectsLocationsActiveDirectoriesListRequest(
        parent=location_ref)
    # Check for unreachable locations.
    response = self.client.projects_locations_activeDirectories.List(request)
    for location in response.unreachable:
      log.warning('Location {} may be unreachable.'.format(location))
    return list_pager.YieldFromList(
        self.client.projects_locations_activeDirectories,
        request,
        field=constants.ACTIVE_DIRECTORY_RESOURCE,
        limit=limit,
        batch_size_attribute='pageSize')

  def GetActiveDirectory(self, activedirectory_ref):
    """Get Cloud NetApp Active Directory information."""
    request = self.messages.NetappProjectsLocationsActiveDirectoriesGetRequest(
        name=activedirectory_ref.RelativeName())
    return self.client.projects_locations_activeDirectories.Get(request)

  def DeleteActiveDirectory(self, activedirectory_ref, async_):
    """Deletes an existing Cloud NetApp Active Directory."""
    request = (
        self.messages.NetappProjectsLocationsActiveDirectoriesDeleteRequest(
            name=activedirectory_ref.RelativeName()
        )
    )
    return self._DeleteActiveDirectory(async_, request)

  def _DeleteActiveDirectory(self, async_, request):
    delete_op = self.client.projects_locations_activeDirectories.Delete(request)
    if async_:
      return delete_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        delete_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)

  def ParseUpdatedActiveDirectoryConfig(self,
                                        activedirectory_config,
                                        domain=None,
                                        site=None,
                                        dns=None,
                                        net_bios_prefix=None,
                                        organizational_unit=None,
                                        aes_encryption=None,
                                        username=None,
                                        password=None,
                                        backup_operators=None,
                                        security_operators=None,
                                        kdc_hostname=None,
                                        kdc_ip=None,
                                        nfs_users_with_ldap=None,
                                        ldap_signing=None,
                                        encrypt_dc_connections=None,
                                        description=None,
                                        labels=None):
    """Parses updates into an active directory config."""
    return self._adapter.ParseUpdatedActiveDirectoryConfig(
        activedirectory_config,
        domain=domain,
        site=site,
        dns=dns,
        net_bios_prefix=net_bios_prefix,
        organizational_unit=organizational_unit,
        aes_encryption=aes_encryption,
        username=username,
        password=password,
        backup_operators=backup_operators,
        security_operators=security_operators,
        kdc_hostname=kdc_hostname,
        kdc_ip=kdc_ip,
        nfs_users_with_ldap=nfs_users_with_ldap,
        ldap_signing=ldap_signing,
        encrypt_dc_connections=encrypt_dc_connections,
        description=description,
        labels=labels)

  def UpdateActiveDirectory(self, activedirectory_ref, activedirectory_config,
                            update_mask, async_):
    """Updates an Active Directory.

    Args:
      activedirectory_ref: the reference to the active directory.
      activedirectory_config: Active Directory config, the updated active
        directory.
      update_mask: str, a comma-separated list of updated fields.
      async_: bool, if False, wait for the operation to complete.

    Returns:
      An Operation or Active Directory config.
    """

    update_op = self._adapter.UpdateActiveDirectory(activedirectory_ref,
                                                    activedirectory_config,
                                                    update_mask)
    if async_:
      return update_op
    operation_ref = resources.REGISTRY.ParseRelativeName(
        update_op.name, collection=constants.OPERATIONS_COLLECTION)
    return self.WaitForOperation(operation_ref)


class ActiveDirectoriesAdapter(object):
  """Adapter for the Cloud NetApp Files API for Active Directories."""

  def __init__(self):
    self.release_track = base.ReleaseTrack.GA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )

  def ParseUpdatedActiveDirectoryConfig(
      self,
      activedirectory_config,
      domain=None,
      site=None,
      dns=None,
      net_bios_prefix=None,
      organizational_unit=None,
      aes_encryption=None,
      username=None,
      password=None,
      backup_operators=None,
      security_operators=None,
      kdc_hostname=None,
      kdc_ip=None,
      nfs_users_with_ldap=None,
      ldap_signing=None,
      encrypt_dc_connections=None,
      description=None,
      labels=None,
  ):
    """Parses updates into an active directory config."""
    if domain is not None:
      activedirectory_config.domain = domain
    if site is not None:
      activedirectory_config.site = site
    if dns is not None:
      activedirectory_config.dns = dns
    if net_bios_prefix is not None:
      activedirectory_config.netBiosPrefix = net_bios_prefix
    if organizational_unit is not None:
      activedirectory_config.organizationalUnit = organizational_unit
    if aes_encryption is not None:
      activedirectory_config.aesEncryption = aes_encryption
    if username is not None:
      activedirectory_config.username = username
    if password is not None:
      activedirectory_config.password = password
    if backup_operators is not None:
      activedirectory_config.backupOperators = backup_operators
    if security_operators is not None:
      activedirectory_config.securityOperators = security_operators
    if kdc_hostname is not None:
      activedirectory_config.kdcHostname = kdc_hostname
    if kdc_ip is not None:
      activedirectory_config.kdcIp = kdc_ip
    if nfs_users_with_ldap is not None:
      activedirectory_config.nfsUsersWithLdap = nfs_users_with_ldap
    if ldap_signing is not None:
      activedirectory_config.ldapSigning = ldap_signing
    if encrypt_dc_connections is not None:
      activedirectory_config.encryptDcConnections = encrypt_dc_connections
    if description is not None:
      activedirectory_config.description = description
    if labels is not None:
      activedirectory_config.labels = labels
    return activedirectory_config

  def UpdateActiveDirectory(self, activedirectory_ref, activedirectory_config,
                            update_mask):
    """Send a Patch request for the Cloud NetApp Active Directory."""
    update_request = (
        self.messages.NetappProjectsLocationsActiveDirectoriesPatchRequest(
            activeDirectory=activedirectory_config,
            name=activedirectory_ref.RelativeName(),
            updateMask=update_mask))
    update_op = self.client.projects_locations_activeDirectories.Patch(
        update_request)
    return update_op


class BetaActiveDirectoriesAdapter(ActiveDirectoriesAdapter):
  """Adapter for the Beta Cloud NetApp Files API for Active Directories."""

  def __init__(self):
    super(BetaActiveDirectoriesAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.BETA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )


class AlphaActiveDirectoriesAdapter(BetaActiveDirectoriesAdapter):
  """Adapter for the Alpha Cloud NetApp Files API for Active Directories."""

  def __init__(self):
    super(AlphaActiveDirectoriesAdapter, self).__init__()
    self.release_track = base.ReleaseTrack.ALPHA
    self.client = netapp_api_util.GetClientInstance(
        release_track=self.release_track
    )
    self.messages = netapp_api_util.GetMessagesModule(
        release_track=self.release_track
    )
