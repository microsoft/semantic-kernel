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
"""Common flags for some of the Looker commands.

Flags are specified with functions that take in a single argument, the parser,
and add the newly constructed flag to that parser.

Example:

def AddFlagName(parser):
  parser.add_argument(
    '--flag-name',
    ... // Other flag details.
  )
"""

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


class InstanceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceCompleter, self).__init__(
        collection='looker.projects.locations.instances',
        list_command='looker instances list',
        **kwargs
    )


def AddInstance(parser):
  parser.add_argument(
      '--instance',
      required=True,
      completer=InstanceCompleter,
      help=""" \
              ID of the instance or fully qualified identifier for the instance.
              To set the instance attribute:

              - provide the argument --instance on the command line.
          """,
  )


def AddInstanceConcept(parser, instance_concept_str):
  concept_parsers.ConceptParser(
      [GetInstancePresentationSpec(instance_concept_str)]
  ).AddToParser(parser)


def AddKmsKeyGroup(parser):
  """Register flags for KMS Key."""
  key_group = parser.add_group(
      required=True,
      help=(
          'Key resource - The Cloud KMS (Key Management Service) cryptokey'
          ' that will be used to protect the Looker instance and backups. The'
          " 'Looker Service Agent' service account must hold role 'Cloud"
          " KMS CryptoKey Encrypter'. The arguments in this group"
          ' can be used to specify the attributes of this resource.'
      ),
  )

  key_group.add_argument(
      '--kms-key',
      metavar='KMS_KEY',
      required=True,
      help='Fully qualified identifier (name) for the key.',
  )


def AddTargetGcsUriGroup(parser):
  """Register flags for Target GCS URI."""
  target_group = parser.add_group(
      mutex=True,
      required=True,
      help=(
          'Export Destination - The path and storage where the export will be'
          ' stored.'
      ),
  )
  target_group.add_argument(
      '--target-gcs-uri',
      metavar='TARGET_GCS_URI',
      help=(
          'The path to the folder in Google Cloud Storage where the export will'
          ' be stored. The URI is in the form `gs://bucketName/folderName`. The'
          ' Looker Service Agent should have the role Storage Object Creator.'
      ),
  )


def AddExportInstanceArgs(parser):
  """Register flags Export Instance command."""
  AddInstanceConcept(
      parser,
      (
          'Arguments and flags that specify the Looker instance you want to'
          ' export.'
      ),
  )
  AddTargetGcsUriGroup(parser)
  AddKmsKeyGroup(parser)


def AddImportInstanceArgs(parser):
  """Register flags Import Instance command."""
  AddInstanceConcept(
      parser,
      (
          'Arguments and flags that specify the Looker instance you want to'
          ' import.'
      ),
  )
  source_group = parser.add_group(
      mutex=True,
      required=True,
      help=(
          'Import Destination - The path and storage where the import will be'
          ' retrieved from.'
      ),
  )
  source_group.add_argument(
      '--source-gcs-uri',
      metavar='SOURCE_GCS_URI',
      help=(
          'The path to the folder in Google Cloud Storage where the import'
          ' will be retrieved from. The URI is in the form'
          ' `gs://bucketName/folderName`.'
      ),
  )


def GetRegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'region', 'The region of the {resource}.'
  )


def GetInstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      'instance', 'The instance of the {resource}.'
  )


def GetInstanceResourceSpec():
  return concepts.ResourceSpec(
      'looker.projects.locations.instances',
      'instance',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=GetRegionAttributeConfig(),
      instancesId=GetInstanceAttributeConfig(),
  )


def GetInstancePresentationSpec(group_help):
  return presentation_specs.ResourcePresentationSpec(
      'instance', GetInstanceResourceSpec(), group_help, required=True
  )
