# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Cloud NetApp Files KMS Configs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


KMS_CONFIGS_LIST_FORMAT = """\
    table(
        name.basename():label=KMS_CONFIG_NAME:sort=1,
        name.segment(3):label=LOCATION,
        cryptoKeyName,
        state
    )"""


## Resource Attribute Config for KMS Key ##


def GetKmsKeyAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-key', help_text='The KMS key of the {resource}'
  )


def GetKmsKeyRingAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-keyring', help_text='The KMS keyring of the {resource}'
  )


def GetKmsProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-project',
      help_text='The Cloud project for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(properties.VALUES.core.project)],
  )


def GetKmsLocationAttributeConfig():
  fallthroughs = [
      ## if --kms-location is not set, use value from --location or
      ## gcloud config get-value netapp/location or netapp/region
      deps.ArgFallthrough('--location'),
      deps.PropertyFallthrough(properties.VALUES.netapp.location),
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='kms-location',
      help_text='The Cloud location for the {resource}.',
      fallthroughs=fallthroughs,
  )


def GetKmsKeyResourceSpec():
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name='kms_key',
      projectsId=GetKmsProjectAttributeConfig(),
      locationsId=GetKmsLocationAttributeConfig(),
      keyRingsId=GetKmsKeyRingAttributeConfig(),
      cryptoKeysId=GetKmsKeyAttributeConfig(),
  )


## Helper functions to add args / flags for KMS Config gcloud commands ##


def AddKmsKeyResourceArg(parser, required=True):
  concept_parsers.ConceptParser.ForResource(
      name='--kms-key',
      resource_spec=GetKmsKeyResourceSpec(),
      group_help=(
          'The Cloud KMS (Key Management Service) Crypto Key that will be used'
      ),
      required=required,
  ).AddToParser(parser)


## Helper functions for KMS Configs surface command


def ConstructCryptoKeyName(kms_project, kms_location, kms_keyring, kms_key):
  return 'projects/%s/locations/%s/keyRings/%s/cryptoKeys/%s' % (
      kms_project,
      kms_location,
      kms_keyring,
      kms_key,
  )


def ExtractKmsProjectFromCryptoKeyName(name):
  name_split = name.split('/')
  return name_split[1]


def ExtractKmsLocationFromCryptoKeyName(name):
  name_split = name.split('/')
  return name_split[3]


def ExtractKmsKeyRingFromCryptoKeyName(name):
  name_split = name.split('/')
  return name_split[5]


def ExtractKmsCryptoKeyFromCryptoKeyName(name):
  name_split = name.split('/')
  return name_split[7]


## Helper functions to combine KMS Configs args / flags for gcloud commands ##


def AddKMSConfigCreateArgs(parser):
  """Add args for creating a KMS Config."""
  concept_parsers.ConceptParser(
      [flags.GetKmsConfigPresentationSpec('The KMS Config to create')]
  ).AddToParser(parser)
  AddKmsKeyResourceArg(parser, required=True)
  flags.AddResourceDescriptionArg(parser, 'KMS Config')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddCreateLabelsFlags(parser)


def AddKMSConfigDeleteArgs(parser):
  """Add args for deleting a KMS Config."""
  concept_parsers.ConceptParser(
      [flags.GetKmsConfigPresentationSpec('The KMS Config to delete')]
  ).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)


def AddKMSConfigUpdateArgs(parser):
  """Add args for updating a KMS Config."""
  concept_parsers.ConceptParser(
      [flags.GetKmsConfigPresentationSpec('The KMS Config to update')]
  ).AddToParser(parser)
  AddKmsKeyResourceArg(parser, required=False)
  flags.AddResourceDescriptionArg(parser, 'KMS Config')
  flags.AddResourceAsyncFlag(parser)
  labels_util.AddUpdateLabelsFlags(parser)


def AddKMSConfigEncryptArgs(parser):
  """Add args for encrypting volumes under a KMS Config."""
  concept_parsers.ConceptParser(
      [flags.GetKmsConfigPresentationSpec('The KMS Config used to encrypt')]
  ).AddToParser(parser)
  flags.AddResourceAsyncFlag(parser)
