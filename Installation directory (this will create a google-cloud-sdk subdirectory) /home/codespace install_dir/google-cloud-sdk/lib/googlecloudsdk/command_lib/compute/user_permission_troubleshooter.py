# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Troubleshoot user permission for ssh connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log

_API_COMPUTE_CLIENT_NAME = 'compute'
_API_IAM_CLIENT_NAME = 'iam'
_API_RESOURCEMANAGER_CLIENT_NAME = 'cloudresourcemanager'
_API_IAP_CLIENT_NAME = 'iap'
_API_CLIENT_VERSION_V1 = 'v1'
_API_CLIENT_VERSION_V3 = 'v3'

INSTANCE_PROJECT_MESSAGE = 'You need the IAM permissions {0}\n'

SERVICE_ACCOUNT_MESSAGE = (
    'The VM has an attached service account. You need the permission '
    'iam.serviceAccounts.actAs on the project or service account. '
    'Alternatively, this permission is included in the '
    'roles/iam.serviceAccountUser role.\nHelp for service account permission: '
    'https://cloud.google.com/iam/docs/service-accounts-actas\nHelp for '
    'service account role: '
    'https://cloud.google.com/iam/docs/service-accounts\n')

OS_LOGIN_MESSAGE = (
    'You need the Compute OS Admin Login role (roles/compute.osAdminLogin) or '
    'the Compute OS Login role (roles/compute.osLogin).\nHelp for roles: '
    'https://cloud.google.com/compute/docs/access/iam#predefinedroles\n')

IAP_MESSAGE = (
    'You need permission to SSH to a private IP address: '
    'iap.tunnelInstances.accessViaIAP.\nHelp for IAP permissions: '
    'https://cloud.google.com/iap/docs/managing-access\n')

instance_permissions = ['compute.instances.get', 'compute.instances.use']
project_permissions = [
    'resourcemanager.projects.get',
    'compute.projects.get',
    'compute.zoneOperations.get',
    'compute.globalOperations.get',
]
serviceaccount_permissions = [
    'iam.serviceAccounts.actAs',
    'iam.serviceAccounts.get',
]
oslogin_permissions = [
    'compute.instances.osAdminLogin',
    'compute.instances.osLogin',
]
iap_permissions = ['iap.tunnelInstances.accessViaIAP']


class UserPermissionTroubleshooter(ssh_troubleshooter.SshTroubleshooter):
  """Check user permission.

  Perform IAM authorization checks for the following IAM resources: instance,
  project, service account, IAP, and OS Login if applicable.

  Attributes:
    project: The project object.
    instance: The instance object.
    zone: str, the zone name.
    iap_tunnel_args: SshTunnelArgs or None if IAP Tunnel is disabled.
  """

  def __init__(self, project, zone, instance, iap_tunnel_args):
    self.project = project
    self.zone = zone
    self.instance = instance
    self.iap_tunnel_args = iap_tunnel_args
    self.compute_client = apis.GetClientInstance(_API_COMPUTE_CLIENT_NAME,
                                                 _API_CLIENT_VERSION_V1)
    self.compute_message = apis.GetMessagesModule(_API_COMPUTE_CLIENT_NAME,
                                                  _API_CLIENT_VERSION_V1)
    self.iam_client = apis.GetClientInstance(_API_IAM_CLIENT_NAME,
                                             _API_CLIENT_VERSION_V1)
    self.iam_message = apis.GetMessagesModule(_API_IAM_CLIENT_NAME,
                                              _API_CLIENT_VERSION_V1)
    self.resourcemanager_client_v3 = apis.GetClientInstance(
        _API_RESOURCEMANAGER_CLIENT_NAME, _API_CLIENT_VERSION_V3)
    self.resourcemanager_message_v3 = apis.GetMessagesModule(
        _API_RESOURCEMANAGER_CLIENT_NAME, _API_CLIENT_VERSION_V3)
    self.iap_client = apis.GetClientInstance(_API_IAP_CLIENT_NAME,
                                             _API_CLIENT_VERSION_V1)
    self.iap_message = apis.GetMessagesModule(_API_IAP_CLIENT_NAME,
                                              _API_CLIENT_VERSION_V1)
    self.enable_oslogin = False
    self.issues = {}

  def check_prerequisite(self):
    """Validate if the user has enabled oslogin."""
    self.enable_oslogin = self._IsOsLoginEnabled()

  def cleanup_resources(self):
    return

  def troubleshoot(self):
    log.status.Print('---- Checking user permissions ----')

    if self.enable_oslogin:
      # We don't check to see if public key is already in profile and
      # POSIX information here. We only check if OS Login is enabled.
      if self._CheckOsLoginPermissions():
        self.issues['oslogin'] = OS_LOGIN_MESSAGE
    else:
      # Require metadata access permission if not enable oslogin.
      instance_permissions.append('compute.instances.setMetadata')
      project_permissions.append('compute.projects.setCommonInstanceMetadata')

    # Check IAM on instance and project.
    missing_instance_project = sorted(self._CheckInstancePermissions().union(
        self._CheckProjectPermissions()))
    if missing_instance_project:
      self.issues['instance_project'] = INSTANCE_PROJECT_MESSAGE.format(
          ' '.join(missing_instance_project))

    # Check IAM on service account
    if self.instance.serviceAccounts and self._CheckServiceAccountPermissions():
      self.issues['serviceaccount'] = SERVICE_ACCOUNT_MESSAGE

    # Check IAM on IAP.
    if self.iap_tunnel_args and self._CheckIapPermissions():
      self.issues['iap'] = IAP_MESSAGE

    # Prompt appropriate messages to user.
    log.status.Print('User permissions: {0} issue(s) found.\n'.format(
        len(self.issues.keys())))
    for message in self.issues.values():
      log.status.Print(message)

  def _CheckIapPermissions(self):
    """Check if user miss any IAP Permissions.

    Returns:
      set, missing IAM permissions.
    """
    iam_request = self.iap_message.TestIamPermissionsRequest(
        permissions=iap_permissions)
    resource = 'projects/{}/iap_tunnel/zones/{}/instances/{}'.format(
        self.project.name, self.zone, self.instance.name)
    request = self.iap_message.IapTestIamPermissionsRequest(
        resource=resource, testIamPermissionsRequest=iam_request)
    response = self.iap_client.v1.TestIamPermissions(request)
    return set(iap_permissions) - set(response.permissions)

  def _CheckServiceAccountPermissions(self):
    """Check whether user has service account IAM permissions.

    Returns:
       set, missing IAM permissions.
    """
    iam_request = self.iam_message.TestIamPermissionsRequest(
        permissions=serviceaccount_permissions)
    request = self.iam_message.IamProjectsServiceAccountsTestIamPermissionsRequest(
        resource='projects/{project}/serviceAccounts/{serviceaccount}'.format(
            project=self.project.name,
            serviceaccount=self.instance.serviceAccounts[0].email),
        testIamPermissionsRequest=iam_request)
    response = self.iam_client.projects_serviceAccounts.TestIamPermissions(
        request)

    return set(serviceaccount_permissions) - set(response.permissions)

  def _CheckOsLoginPermissions(self):
    """Check whether user has oslogin IAM permissions.

    Returns:
      set, missing IAM permissions.
    """
    response = self._ComputeTestIamPermissions(oslogin_permissions)
    return set(oslogin_permissions) - set(response.permissions)

  def _CheckInstancePermissions(self):
    """Check whether user has IAM permission on instance resource.

    Returns:
      set, missing IAM permissions.
    """
    response = self._ComputeTestIamPermissions(instance_permissions)
    return set(instance_permissions) - set(response.permissions)

  def _ComputeTestIamPermissions(self, permissions):
    """Call TestIamPermissions to check whether user has certain IAM permissions.

    Args:
      permissions: list, the permissions to check for the instance resource.

    Returns:
      TestPermissionsResponse, the API response from TestIamPermissions.
    """
    iam_request = self.compute_message.TestPermissionsRequest(
        permissions=permissions)
    request = self.compute_message.ComputeInstancesTestIamPermissionsRequest(
        project=self.project.name,
        resource=self.instance.name,
        testPermissionsRequest=iam_request,
        zone=self.zone)
    return self.compute_client.instances.TestIamPermissions(request)

  def _CheckProjectPermissions(self):
    """Check whether user has IAM permission on project resource.

    Returns:
      set, missing IAM permissions.
    """
    response = self._ResourceManagerTestIamPermissions(project_permissions)
    return set(project_permissions) - set(response.permissions)

  def _ResourceManagerTestIamPermissions(self, permissions):
    """Check whether user has IAM permission on resource manager.

    Args:
      permissions: list, the permissions to check for the project resource.

    Returns:
      set, missing IAM permissions.
    """
    iam_request = self.resourcemanager_message_v3.TestIamPermissionsRequest(
        permissions=permissions)
    request = self.resourcemanager_message_v3.CloudresourcemanagerProjectsTestIamPermissionsRequest(
        resource='projects/{project}'.format(project=self.project.name),
        testIamPermissionsRequest=iam_request)
    return self.resourcemanager_client_v3.projects.TestIamPermissions(request)

  def _IsOsLoginEnabled(self):
    """Check whether OS Login is enabled on the VM.

    Returns:
      boolean, indicates whether OS Login is enabled.
    """
    oslogin_enabled = ssh.FeatureEnabledInMetadata(
        self.instance, self.project, ssh.OSLOGIN_ENABLE_METADATA_KEY)

    return bool(oslogin_enabled)
