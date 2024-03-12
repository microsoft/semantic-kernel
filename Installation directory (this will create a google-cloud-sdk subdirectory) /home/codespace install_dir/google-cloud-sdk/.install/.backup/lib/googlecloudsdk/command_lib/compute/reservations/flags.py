# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute reservations commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags


def GetDescriptionFlag(is_fr=False):
  help_text = """\
  An optional description of the {} to create.
  """.format('future reservation' if is_fr else 'reservation')

  return base.Argument(
      '--description',
      help=help_text)


def GetRequireSpecificAllocation():
  help_text = """\
  Indicates whether the reservation can be consumed by VMs with "any reservation"
  defined. If enabled, then only VMs that target this reservation by name using
  `--reservation-affinity=specific` can consume from this reservation.
  """
  return base.Argument(
      '--require-specific-reservation', action='store_true', help=help_text)


def GetVmCountFlag(required=True):
  help_text = """\
  The number of VM instances that are allocated to this reservation.
  The value of this field must be an int in the range [1, 1000].
  """
  return base.Argument(
      '--vm-count', required=required, type=int, help=help_text)


def GetMinCpuPlatform():
  """Gets the --min-cpu-platform flag."""
  return base.Argument(
      '--min-cpu-platform',
      help='Optional minimum CPU platform of the reservation to create.')


def GetLocationHint():
  """Gets the --location-hint flag."""
  return base.Argument(
      '--location-hint',
      hidden=True,
      help="""\
      Used by internal tools to control sub-zone location of the instance.
      """)


def GetMachineType(required=True):
  """Gets the --machine-type flag."""
  help_text = """\
  The type of machine (name only) that has a fixed number of vCPUs and a fixed
  amount of memory. You can also specify a custom machine type by using the
  pattern `custom-number_of_CPUs-amount_of_memory`-for example,
  `custom-32-29440`.
  """
  return base.Argument('--machine-type', required=required, help=help_text)


def GetLocalSsdFlag(custom_name=None):
  """Gets the --local-ssd flag."""
  help_text = """\
  Manage the size and the interface of local SSD to use. See
  https://cloud.google.com/compute/docs/disks/local-ssd for more information.
  *interface*::: The kind of disk interface exposed to the VM for this SSD. Valid
  values are `scsi` and `nvme`. SCSI is the default and is supported by more
  guest operating systems. NVME may provide higher performance.
  *size*::: The size of the local SSD in base-2 GB.
  """
  return base.Argument(
      custom_name if custom_name else '--local-ssd',
      type=arg_parsers.ArgDict(spec={
          'interface': (lambda x: x.upper()),
          'size': int,
      }),
      action='append',
      help=help_text)


def GetLocalSsdFlagWithCount(custom_name=None):
  """Gets the --local-ssd flag."""
  help_text = """\
  Manage the size and the interface of local SSD to use. See
  https://cloud.google.com/compute/docs/disks/local-ssd for more information.
  *interface*::: The kind of disk interface exposed to the VM for this SSD. Valid
  values are `scsi` and `nvme`. SCSI is the default and is supported by more
  guest operating systems. NVME may provide higher performance.
  *size*::: The size of the local SSD in base-2 GB.
  *count*::: The number of local SSD to use per VM. Default value is 1.
  """
  return base.Argument(
      custom_name if custom_name else '--local-ssd',
      type=arg_parsers.ArgDict(spec={
          'interface': (lambda x: x.upper()),
          'size': int,
          'count': int
      }),
      action='append',
      help=help_text)


def GetAcceleratorFlag(custom_name=None):
  """Gets the --accelerator flag."""
  help_text = """\
  Manage the configuration of the type and number of accelerator cards attached.
  *count*::: The number of accelerators to attach to each instance in the reservation.
  *type*::: The specific type (e.g. `nvidia-tesla-k80` for nVidia Tesla K80) of
  accelerator to attach to instances in the reservation. Use `gcloud compute accelerator-types list`
  to learn about all available accelerator types.
  """
  return base.Argument(
      custom_name if custom_name else '--accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'count': int,
              'type': str,
          }, required_keys=['count', 'type']),
      action='append',
      help=help_text)


def GetSharedSettingFlag(custom_name=None):
  """Gets the --share-setting flag."""
  help_text = """\
  Specify if this reservation is shared, and if so, the type of sharing. If you
  omit this flag, this value is local (not shared) by default.
  """
  return base.Argument(
      custom_name if custom_name else '--share-setting',
      choices=['local', 'projects', 'folders'],
      help=help_text)


def GetShareWithFlag(custom_name=None):
  """Gets the --share-with flag."""
  help_text = """\
  If this reservation is shared (--share-setting is not local), provide a list
  of all of the specific projects or folders that this reservation is shared
  with. List must contain project IDs or project numbers or folder IDs.
  """
  return base.Argument(
      custom_name if custom_name else '--share-with',
      type=arg_parsers.ArgList(min_length=1),
      metavar='SHARE_WITH',
      help=help_text)


def GetAddShareWithFlag(custom_name=None):
  """Gets the --add-share-with flag."""
  help_text = """\
  A list of specific projects to add to the list of projects that this
  reservation is shared with. List must contain project IDs or project numbers.
  """
  return base.Argument(
      custom_name if custom_name else '--add-share-with',
      type=arg_parsers.ArgList(min_length=1),
      metavar='PROJECT',
      help=help_text)


def GetRemoveShareWithFlag(custom_name=None):
  """Gets the --remove-share-with flag."""
  help_text = """\
  A list of specific projects to remove from the list of projects that this
  reservation is shared with. List must contain project IDs or project numbers.
  """
  return base.Argument(
      custom_name if custom_name else '--remove-share-with',
      type=arg_parsers.ArgList(min_length=1),
      metavar='PROJECT',
      help=help_text)


def GetDeleteAtTimeFlag():
  """Gets the --delete-at-time flag."""
  help_text = """\
  Automatically deletes the reservation at a specific time from its creation.
  The specified time must be an RFC3339 timestamp, which must be
  formatted as "YYYY-MM-DDTHH:MM:SSZ" where YYYY = year, MM = month, DD = day,
  HH = hours, MM = minutes, SS = seconds, and Z = time zone in
  Coordinated Universal Time (UTC). For example, specify 2021-11-20T07:00:00Z.
  """
  return base.Argument(
      '--delete-at-time', type=arg_parsers.Datetime.Parse, help=help_text
  )


def GetDeleteAfterDurationFlag():
  help_text = """\
  Automatically deletes the reservations after a specified number of
  days, hours, minutes, or seconds from its creation. For example,
  specify 30m for 30 minutes, or 1d2h3m4s for 1 day, 2 hours,
  3 minutes, and 4 seconds. For more information, see $ gcloud topic datetimes.
  """
  return base.Argument(
      '--delete-after-duration',
      type=arg_parsers.Duration(),
      help=help_text,
  )


def GetDisableAutoDelete():
  """Gets the --disable-auto-delete flag."""
  help_text = """\
  Disables the auto-delete setting for the reservation.
  """
  return base.Argument(
      '--disable-auto-delete', action='store_true',
      help=help_text)


def GetResourcePolicyFlag(custom_name=None):
  """Gets the --resource-policies flag."""
  help_text = """\
  The resource policies to include in this reservation. If you omit this flag,
  no resource policies are added. You can specify any string as the key, and
  specify the name of a resource policy as the value.
  """
  return base.Argument(
      custom_name or '--resource-policies',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text)


def GetSourceInstanceTemplateFlag(custom_name=None):
  """Gets the --source-instance-template flag."""
  help_text = """\
  The url of the instance template that will be used to populate the fields of
  the reservation. Instance properties can not be defined in addition to source
  instance template.
  """
  return base.Argument(
      custom_name or '--source-instance-template', help=help_text
  )


def AddCreateFlags(parser,
                   support_fleet=False,
                   support_share_setting=False,
                   support_ssd_count=False,
                   support_auto_delete=False):
  """Adds all flags needed for the create command."""
  GetDescriptionFlag().AddToParser(parser)

  # create the group for all properties used in SpecificSkuReservations
  specific_sku_group = base.ArgumentGroup(
      'Manage the SpecificSKU reservation properties.', required=True)

  specific_sku_group.AddArgument(GetRequireSpecificAllocation())
  specific_sku_group.AddArgument(GetVmCountFlag())
  specific_sku_group.AddArgument(GetResourcePolicyFlag())

  # create the sku properties group for the SpecificSkuReservation
  # this group allows instance properties XOR source instance template
  # to be provided
  specific_sku_properties_group = base.ArgumentGroup(
      'Manage the instance properties for the SpecificSKU reservation.',
      required=True,
      mutex=True)
  specific_sku_properties_group.AddArgument(GetSourceInstanceTemplateFlag())

  # create the instance properties group for the SpecificSkuReservation
  instance_properties_group = base.ArgumentGroup(
      'Define the individual instance properties for the SpecificSKU'
      ' reservation.',
      required=False,
  )
  instance_properties_group.AddArgument(GetMinCpuPlatform())
  instance_properties_group.AddArgument(GetMachineType())
  if support_ssd_count:
    instance_properties_group.AddArgument(GetLocalSsdFlagWithCount())
  else:
    instance_properties_group.AddArgument(GetLocalSsdFlag())
  instance_properties_group.AddArgument(GetAcceleratorFlag())
  instance_properties_group.AddArgument(GetLocationHint())
  if support_fleet:
    instance_properties_group.AddArgument(
        instance_flags.AddMaintenanceFreezeDuration())
    instance_properties_group.AddArgument(
        instance_flags.AddMaintenanceInterval())

  # add all the groups to each other and the parser
  specific_sku_properties_group.AddArgument(instance_properties_group)
  specific_sku_group.AddArgument(specific_sku_properties_group)
  specific_sku_group.AddToParser(parser)

  if support_share_setting:
    share_group = base.ArgumentGroup(
        'Manage the properties of a shared reservation.', required=False)
    share_group.AddArgument(GetSharedSettingFlag())
    share_group.AddArgument(GetShareWithFlag())
    share_group.AddToParser(parser)

  if support_auto_delete:
    auto_delete_group = base.ArgumentGroup(
        'Manage auto-delete properties for reservations.',
        required=False,
        mutex=True,
    )
    auto_delete_group.AddArgument(GetDeleteAtTimeFlag())
    auto_delete_group.AddArgument(GetDeleteAfterDurationFlag())
    auto_delete_group.AddToParser(parser)
