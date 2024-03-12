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
"""Updates a Cloud NetApp Active Directory."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.active_directories import client as ad_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.active_directories import flags as activedirectories_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Updates AD (Active Directory) configs for Cloud NetApp Volumes.
          """,
      'EXAMPLES': """\
          The following command updates an AD config in the given project and location with specified arguments:

              $ {command} AD_NAME --location=us-central1 --domain=new-domain.com --dns=1.1.1.1 --site=new_site --net-bios-prefix=new_prefix --organizational-unit=ou2 --enable-aes=true --username=user2 --password="secure2" --backup-operators=backup_op3 --security-operators=secure_op3 --enable-ldap-signing=true --encrypt-dc-connections=yes --kdc-hostname=kdc-host1
          """,
  }

  @staticmethod
  def Args(parser):
    activedirectories_flags.AddActiveDirectoryUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Storage Pool in the current project."""
    activedirectory_ref = args.CONCEPTS.active_directory.Parse()
    client = ad_client.ActiveDirectoriesClient(self._RELEASE_TRACK)
    orig_activedirectory = client.GetActiveDirectory(activedirectory_ref)

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    # Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(client.messages.ActiveDirectory.LabelsValue,
                                 orig_activedirectory.labels).GetOrNone()
    else:
      labels = None
    active_directory = client.ParseUpdatedActiveDirectoryConfig(
        orig_activedirectory,
        domain=args.domain,
        site=args.site,
        dns=args.dns,
        net_bios_prefix=args.net_bios_prefix,
        organizational_unit=args.organizational_unit,
        aes_encryption=args.enable_aes,
        username=args.username,
        password=args.password,
        backup_operators=args.backup_operators,
        security_operators=args.security_operators,
        kdc_hostname=args.kdc_hostname,
        kdc_ip=args.kdc_ip,
        nfs_users_with_ldap=args.nfs_users_with_ldap,
        ldap_signing=args.enable_ldap_signing,
        encrypt_dc_connections=args.encrypt_dc_connections,
        description=args.description,
        labels=labels)

    updated_fields = []
    # TODO(b/243601146) add config mapping and separate config file for update
    if args.IsSpecified('domain'):
      updated_fields.append('domain')
    if args.IsSpecified('site'):
      updated_fields.append('site')
    if args.IsSpecified('dns'):
      updated_fields.append('dns')
    if args.IsSpecified('net_bios_prefix'):
      updated_fields.append('netBiosPrefix')
    if args.IsSpecified('organizational_unit'):
      updated_fields.append('organizationalUnit')
    if args.IsSpecified('enable_aes'):
      updated_fields.append('aesEncryption')
    if args.IsSpecified('username'):
      updated_fields.append('username')
    if args.IsSpecified('password'):
      updated_fields.append('password')
    if args.IsSpecified('backup_operators'):
      updated_fields.append('backupOperators')
    if args.IsSpecified('security_operators'):
      updated_fields.append('securityOperators')
    if args.IsSpecified('kdc_hostname'):
      updated_fields.append('kdcHostname')
    if args.IsSpecified('kdc_ip'):
      updated_fields.append('kdcIp')
    if args.IsSpecified('nfs_users_with_ldap'):
      updated_fields.append('nfsUsersWithLdap')
    if args.IsSpecified('enable_ldap_signing'):
      updated_fields.append('ldapSigning')
    if args.IsSpecified('encrypt_dc_connections'):
      updated_fields.append('encryptDcConnections')
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (args.IsSpecified('update_labels') or
        args.IsSpecified('remove_labels') or args.IsSpecified('clear_labels')):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateActiveDirectory(activedirectory_ref, active_directory,
                                          update_mask, args.async_)
    if args.async_:
      command = 'gcloud {} netapp active-directories list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the updated active directory by listing all'
          ' active directories:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  """Update a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA

