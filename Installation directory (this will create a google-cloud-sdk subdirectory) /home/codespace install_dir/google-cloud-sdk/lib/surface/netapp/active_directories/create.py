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
"""Creates a Cloud NetApp Active Directory."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.active_directories import client as ad_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.active_directories import flags as activedirectories_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.GA

  detailed_help = {
      'DESCRIPTION': """\
          Creates an AD (Active Directory) config for Cloud NetApp Volumes.
          """,
      'EXAMPLES': """\
          The following command creates an AD named AD_NAME with the required arguments:

              $ {command} AD_NAME --location=us-central1 --domain=example-domain.com --dns=0.0.0.0 --net-bios-prefix=prefix-1 --enable-aes=true --username=user1 --password="secure1" --backup-operators=backup_op1,backup_op2 --security-operators=sec_op1,sec_op2 --enable-ldap-signing=false
          """,
  }

  @staticmethod
  def Args(parser):
    activedirectories_flags.AddActiveDirectoryCreateArgs(parser)

  def Run(self, args):
    """Create a Cloud NetApp Active Directory in the current project."""
    activedirectory_ref = args.CONCEPTS.active_directory.Parse()
    client = ad_client.ActiveDirectoriesClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.ActiveDirectory.LabelsValue)

    active_directory = client.ParseActiveDirectoryConfig(
        name=activedirectory_ref.RelativeName(),
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
        labels=labels,
    )
    result = client.CreateActiveDirectory(activedirectory_ref,
                                          args.async_,
                                          active_directory)
    if args.async_:
      command = 'gcloud {} netapp active-directories list'.format(
          self.ReleaseTrack().prefix)
      log.status.Print(
          'Check the status of the new active directory by listing all active'
          ' directories:\n  $ {} '.format(command)
      )
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create a Cloud NetApp Active Directory."""

  _RELEASE_TRACK = base.ReleaseTrack.ALPHA
