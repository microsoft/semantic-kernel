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
"""Flags and helpers for the Cloud NetApp Files Active Directories commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp import util as netapp_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

## Helper functions to add args / flags for Active Directory gcloud commands ##


def AddActiveDirectoryDomainArg(parser, required=True):
  """Adds a --domain arg to the given parser."""
  parser.add_argument(
      '--domain',
      type=str,
      required=required,
      help="""The Active Directory domain."""
  )


def AddActiveDirectorySiteArg(parser):
  """Adds a --site arg to the given parser."""
  parser.add_argument(
      '--site',
      type=str,
      help="""The Active Directory site the service\
          will limit Domain Controller discovery to."""
  )


def AddActiveDirectoryDnsArg(parser, required=True):
  """Adds a --dns arg to the given parser."""
  parser.add_argument(
      '--dns',
      type=str,
      required=required,
      help="""A comma separated list of DNS server IP addresses for the Active Directory domain."""
  )


def AddActiveDirectoryNetBiosArg(parser, required=True):
  """Adds a --net-bios-prefix arg to the given parser."""
  parser.add_argument(
      '--net-bios-prefix',
      type=str,
      required=required,
      help="""NetBIOS prefix name of the server."""
  )


def AddActiveDirectoryOrganizationalUnitArg(parser):
  """Adds a --organizational-unit arg to the given parser."""
  parser.add_argument(
      '--organizational-unit',
      type=str,
      help="""The Organizational Unit (OU) within the Windows Active Directory the user belongs to."""
  )


def AddActiveDirectoryAesEncryptionArg(parser):
  """Adds a --enable-aes arg to the given parser."""
  parser.add_argument(
      '--enable-aes',
      type=arg_parsers.ArgBoolean(truthy_strings=netapp_util.truthy,
                                  falsey_strings=netapp_util.falsey),
      help="""The Boolean value indiciating whether AES encryption will be enabled for SMB communication."""
  )


def AddActiveDirectoryUsernameArg(parser, required=True):
  """Adds a --username arg to the given parser."""
  parser.add_argument(
      '--username',
      type=str,
      required=required,
      help="""Username of the Active Directory domain administrator."""
  )


def AddActiveDirectoryPasswordArg(parser, required=True):
  """Adds a --password arg to the given parser."""
  parser.add_argument(
      '--password',
      type=str,
      required=required,
      help="""Password of the Active Directory domain administrator."""
  )


def AddActiveDirectoryBackupOperatorsArg(parser):
  """Adds a --backup-operators arg to the given parser."""
  parser.add_argument(
      '--backup-operators',
      type=arg_parsers.ArgList(element_type=str),
      metavar='BACKUP_OPERATOR',
      help="""Users to be added to the Built-in Backup Operator Active Directory group."""
  )


def AddActiveDirectorySecurityOperatorsArg(parser):
  """Adds a --security-operators arg to the given parser."""
  parser.add_argument(
      '--security-operators',
      type=arg_parsers.ArgList(element_type=str),
      metavar='SECURITY_OPERATOR',
      help="""Domain users to be given the Security privilege."""
  )


def AddActivevDirectoryKdcHostnameArg(parser):
  """Adds a --kdc-hostname arg to the given parser."""
  parser.add_argument(
      '--kdc-hostname',
      type=str,
      help="""Name of the Active Directory machine."""
  )


def AddActiveDirectoryKdcIpArg(parser):
  """Adds a --kdc-ip arg to the given parser."""
  parser.add_argument(
      '--kdc-ip',
      type=str,
      help="""KDC server IP address for the Active Directory machine."""
  )


def AddActiveDirectoryNfsUsersWithLdapArg(parser):
  """Adds a --nfs-users-with-ldap arg to the given parser."""
  parser.add_argument(
      '--nfs-users-with-ldap',
      type=arg_parsers.ArgBoolean(truthy_strings=netapp_util.truthy,
                                  falsey_strings=netapp_util.falsey),
      help="""Boolean flag that allows access to local users and LDAP users. If access is needed only for LDAP users, it has to be disabled."""
  )


def AddActiveDirectoryLdapSigningArg(parser):
  """Adds a --enable-ldap-signing arg to the given parser."""
  parser.add_argument(
      '--enable-ldap-signing',
      type=arg_parsers.ArgBoolean(truthy_strings=netapp_util.truthy,
                                  falsey_strings=netapp_util.falsey),
      help="""Boolean flag that specifies whether or not LDAP traffic needs to be signed."""
  )


def AddActiveDirectoryEncryptDcConnectionsArg(parser):
  """Adds a --encrypt-dc-connections arg to the given parser."""
  parser.add_argument(
      '--encrypt-dc-connections',
      type=arg_parsers.ArgBoolean(truthy_strings=netapp_util.truthy,
                                  falsey_strings=netapp_util.falsey),
      help="""Boolean flag that specifies whether traffic between SMB server to Domain Controller (DC) will be encrypted."""
  )


## Helper functions to combine Active Directory args / flags for ##
## gcloud commands ##


def AddActiveDirectoryCreateArgs(parser):
  """Add args for creating an Active Directory."""
  concept_parsers.ConceptParser([
      flags.GetActiveDirectoryPresentationSpec(
          'The Active Directory to create.')
  ]).AddToParser(parser)
  flags.AddResourceDescriptionArg(parser, 'Active Directory')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)
  AddActiveDirectoryDomainArg(parser)
  AddActiveDirectorySiteArg(parser)
  AddActiveDirectoryDnsArg(parser)
  AddActiveDirectoryNetBiosArg(parser)
  AddActiveDirectoryOrganizationalUnitArg(parser)
  AddActiveDirectoryAesEncryptionArg(parser)
  AddActiveDirectoryUsernameArg(parser)
  AddActiveDirectoryPasswordArg(parser)
  AddActiveDirectoryBackupOperatorsArg(parser)
  AddActiveDirectorySecurityOperatorsArg(parser)
  AddActivevDirectoryKdcHostnameArg(parser)
  AddActiveDirectoryKdcIpArg(parser)
  AddActiveDirectoryNfsUsersWithLdapArg(parser)
  AddActiveDirectoryLdapSigningArg(parser)
  AddActiveDirectoryEncryptDcConnectionsArg(parser)


def AddActiveDirectoryDeleteArgs(parser):
  """Add args for deleting an Active Directory."""
  concept_parsers.ConceptParser([
      flags.GetActiveDirectoryPresentationSpec(
          'The Active Directory to delete.')
  ]).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)


def AddActiveDirectoryUpdateArgs(parser):
  """Add args for updating an Active Directory."""
  concept_parsers.ConceptParser([
      flags.GetActiveDirectoryPresentationSpec(
          'The Active Directory to update.')
  ]).AddToParser(parser)
  flags.AddResourceDescriptionArg(parser, 'Active Directory')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)
  AddActiveDirectoryDomainArg(parser)
  AddActiveDirectorySiteArg(parser)
  AddActiveDirectoryDnsArg(parser)
  AddActiveDirectoryNetBiosArg(parser)
  AddActiveDirectoryOrganizationalUnitArg(parser)
  AddActiveDirectoryAesEncryptionArg(parser)
  AddActiveDirectoryUsernameArg(parser)
  AddActiveDirectoryPasswordArg(parser)
  AddActiveDirectoryBackupOperatorsArg(parser)
  AddActiveDirectorySecurityOperatorsArg(parser)
  AddActivevDirectoryKdcHostnameArg(parser)
  AddActiveDirectoryKdcIpArg(parser)
  AddActiveDirectoryNfsUsersWithLdapArg(parser)
  AddActiveDirectoryLdapSigningArg(parser)
  AddActiveDirectoryEncryptDcConnectionsArg(parser)
