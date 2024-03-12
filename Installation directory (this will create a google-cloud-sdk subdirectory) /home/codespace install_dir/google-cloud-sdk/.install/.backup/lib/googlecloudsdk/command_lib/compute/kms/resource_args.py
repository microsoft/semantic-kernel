# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Shared resource flags for kms related compute commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def KeyAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-key',
      help_text='The KMS key of the {resource}.')


def KeyringAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-keyring',
      help_text='The KMS keyring of the {resource}.')


def LocationAttributeConfig(region_fallthrough=False):
  fallthroughs = []
  if region_fallthrough:
    fallthroughs.append(deps.ArgFallthrough('--region'))
  return concepts.ResourceParameterAttributeConfig(
      name='kms-location',
      help_text='The Cloud location for the {resource}.',
      fallthroughs=fallthroughs)


def ProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-project',
      help_text='The Cloud project for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(properties.VALUES.core.project)])


def GetKmsKeyResourceSpec(region_fallthrough=False):
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name='key',
      cryptoKeysId=KeyAttributeConfig(),
      keyRingsId=KeyringAttributeConfig(),
      locationsId=LocationAttributeConfig(
          region_fallthrough=region_fallthrough),
      projectsId=ProjectAttributeConfig(),
      disable_auto_completers=False)


def AddKmsKeyResourceArg(parser,
                         resource,
                         region_fallthrough=False,
                         boot_disk_prefix=False,
                         instance_prefix=False):
  """Add a resource argument for a KMS key.

  Args:
    parser: the parser for the command.
    resource: str, the name of the resource that the cryptokey will be used to
      protect.
    region_fallthrough: bool, True if the command has a region flag that should
      be used as a fallthrough for the kms location.
    boot_disk_prefix: If the key flags have the 'boot-disk' prefix.
    instance_prefix: If the key flags have the 'instance' prefix.
  """
  flag_name_overrides = None
  kms_flags = ['kms-key', 'kms-keyring', 'kms-location', 'kms-project']
  name = '--kms-key'
  if boot_disk_prefix:
    flag_name_overrides = dict(
        [(flag, '--boot-disk-' + flag) for flag in kms_flags])
    name = '--boot-disk-kms-key'
  elif instance_prefix:
    flag_name_overrides = dict([
        (flag, '--instance-' + flag) for flag in kms_flags
    ])
    name = '--instance-kms-key'

  concept_parsers.ConceptParser.ForResource(
      name,
      GetKmsKeyResourceSpec(region_fallthrough=region_fallthrough),
      'The Cloud KMS (Key Management Service) cryptokey that will be used to '
      'protect the {}.'.format(resource),
      flag_name_overrides=flag_name_overrides).AddToParser(parser)
