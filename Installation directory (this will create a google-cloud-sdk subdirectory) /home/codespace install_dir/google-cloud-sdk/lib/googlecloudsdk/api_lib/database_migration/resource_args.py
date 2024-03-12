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
"""Shared resource flags for Database Migration Service commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def ConnectionProfileAttributeConfig(name='connection_profile'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The connection profile of the {resource}.')


def MigrationJobAttributeConfig(name='migration_job'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The migration job of the {resource}.')


def PrivateConnectionAttributeConfig(name='private_connection'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The private connection of the {resource}.')


def ServiceAttachmentAttributeConfig(name='service_attachment'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The service attachment of the {resource}.'
  )


def ConversionWorkspaceAttributeConfig(name='conversion_workspace'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The conversion workspace of the {resource}.'
  )


def CmekKeyAttributeConfig(name='cmek-key'):
  # For anchor attribute, help text is generated automatically.
  return concepts.ResourceParameterAttributeConfig(name=name)


def CmekKeyringAttributeConfig(name='cmek-keyring'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The CMEK keyring id of the {resource}.'
  )


def CmekProjectAttributeConfig(name='cmek-project'):
  return concepts.ResourceParameterAttributeConfig(
      name=name, help_text='The Cloud project id for the {resource}.'
  )


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region', help_text='The Cloud region for the {resource}.')


def GetRegionResourceSpec(resource_name='region'):
  return concepts.ResourceSpec(
      'datamigration.projects.locations',
      resource_name=resource_name,
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetConnectionProfileResourceSpec(resource_name='connection_profile'):
  return concepts.ResourceSpec(
      'datamigration.projects.locations.connectionProfiles',
      resource_name=resource_name,
      connectionProfilesId=ConnectionProfileAttributeConfig(name=resource_name),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetMigrationJobResourceSpec(resource_name='migration_job'):
  return concepts.ResourceSpec(
      'datamigration.projects.locations.migrationJobs',
      resource_name=resource_name,
      migrationJobsId=MigrationJobAttributeConfig(name=resource_name),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetPrivateConnectionResourceSpec(resource_name='private_connection'):
  return concepts.ResourceSpec(
      'datamigration.projects.locations.privateConnections',
      resource_name=resource_name,
      api_version='v1',
      privateConnectionsId=PrivateConnectionAttributeConfig(name=resource_name),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetServiceAttachmentResourceSpec(resource_name='service_attachment'):
  return concepts.ResourceSpec(
      'compute.serviceAttachments',
      resource_name=resource_name,
      serviceAttachment=ServiceAttachmentAttributeConfig(name=resource_name),
      project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetConversionWorkspaceResourceSpec(resource_name='conversion_workspace'):
  return concepts.ResourceSpec(
      'datamigration.projects.locations.conversionWorkspaces',
      resource_name=resource_name,
      api_version='v1',
      conversionWorkspacesId=ConversionWorkspaceAttributeConfig(
          name=resource_name),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)


def GetCmekKeyResourceSpec(resource_name='cmek-key'):
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name=resource_name,
      api_version='v1',
      cryptoKeysId=CmekKeyAttributeConfig(),
      keyRingsId=CmekKeyringAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=CmekProjectAttributeConfig(),
      disable_auto_completers=False,
  )


def GetKMSKeyResourceSpec(resource_name='kms-key'):
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name=resource_name,
      api_version='v1',
      cryptoKeysId=CmekKeyAttributeConfig('kms-key'),
      keyRingsId=CmekKeyringAttributeConfig('kms-keyring'),
      locationsId=RegionAttributeConfig(),
      projectsId=CmekProjectAttributeConfig('kms-project'),
      disable_auto_completers=False,
  )


def AddConnectionProfileResourceArg(parser, verb, positional=True):
  """Add a resource argument for a database migration connection profile.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'connection_profile'
  else:
    name = '--connection-profile'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetConnectionProfileResourceSpec(),
      'The connection profile {}.'.format(verb),
      required=True).AddToParser(parser)


def AddCloudSqlConnectionProfileResourceArgs(parser, verb):
  """Add resource arguments for a database migration CloudSQL connection profile.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          'connection_profile',
          GetConnectionProfileResourceSpec(),
          'The connection profile {}.'.format(verb),
          required=True),
      presentation_specs.ResourcePresentationSpec(
          '--source-id',
          GetConnectionProfileResourceSpec(),
          'Database Migration Service source connection profile ID.',
          required=True,
          flag_name_overrides={'region': ''}),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--source-id.region': ['--region']
      }).AddToParser(parser)


def AddAlloyDBConnectionProfileResourceArgs(parser, verb):
  """Add resource arguments for a database migration AlloyDB connection profile.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          'connection_profile',
          GetConnectionProfileResourceSpec(),
          'The connection profile {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--kms-key',
          GetKMSKeyResourceSpec(),
          (
              'Name of the CMEK (customer-managed encryption key) used for this'
              ' AlloyDB cluster. For example,'
              ' projects/myProject/locations/us-central1/keyRings/myKeyRing/cryptoKeys/myKey.'
          ),
          flag_name_overrides={'region': ''},
      ),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={'--kms-key.region': ['--region']},
  ).AddToParser(parser)


def AddCmekResourceArgs(parser):
  """Add a resource argument for a connection profile cmek.

  Args:
    parser: the parser for the command.
  """
  concept_parsers.ConceptParser.ForResource(
      '--cmek-key',
      GetCmekKeyResourceSpec(),
      'Name of the CMEK (customer-managed encryption key) used for'
      ' the connection profile. For example,'
      ' projects/myProject/locations/us-central1/keyRings/myKeyRing/cryptoKeys/myKey.',
      flag_name_overrides={'region': ''},
  ).AddToParser(parser)


def AddOracleConnectionProfileResourceArg(parser,
                                          verb,
                                          positional=True,
                                          required=True):
  """Add a resource argument for a database migration oracle cp.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
    required: bool, if True, means that a flag is required.
  """
  if positional:
    name = 'connection_profile'
  else:
    name = '--connection-profile'

  connectivity_parser = parser.add_group(mutex=True)
  connectivity_parser.add_argument(
      '--static-ip-connectivity',
      action='store_true',
      help="""use static ip connectivity""")

  forward_ssh_parser = connectivity_parser.add_group()
  forward_ssh_parser.add_argument(
      '--forward-ssh-hostname',
      help="""Hostname for the SSH tunnel.""",
      required=required)
  forward_ssh_parser.add_argument(
      '--forward-ssh-username',
      help="""Username for the SSH tunnel.""",
      required=required)
  forward_ssh_parser.add_argument(
      '--forward-ssh-port',
      help="""Port for the SSH tunnel, default value is 22.\
      """,
      default=22)
  password_group = forward_ssh_parser.add_group(required=required, mutex=True)
  password_group.add_argument(
      '--forward-ssh-password', help="""\
          SSH password.
          """)
  password_group.add_argument(
      '--forward-ssh-private-key', help='SSH private key..')

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetConnectionProfileResourceSpec(),
          'The connection profile {}.'.format(verb),
          required=True),
      presentation_specs.ResourcePresentationSpec(
          '--private-connection',
          GetPrivateConnectionResourceSpec(),
          'Resource ID of the private connection.',
          flag_name_overrides={'region': ''},
          group=connectivity_parser)
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--private-connection.region': ['--region']
      }).AddToParser(parser)


def AddPostgresqlConnectionProfileResourceArg(parser, verb, positional=True):
  """Add a resource argument for a database migration postgresql cp.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'connection_profile'
  else:
    name = '--connection-profile'

  connectivity_parser = parser.add_group(mutex=True)
  connectivity_parser.add_argument(
      '--static-ip-connectivity',
      action='store_true',
      help="""use static ip connectivity""",
  )

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetConnectionProfileResourceSpec(),
          'The connection profile {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--psc-service-attachment',
          GetServiceAttachmentResourceSpec(),
          'Resource ID of the service attachment.',
          flag_name_overrides={'region': ''},
          group=connectivity_parser,
      ),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--psc-service-attachment.region': ['--region']
      }).AddToParser(parser)


def AddMigrationJobResourceArgs(parser, verb, required=False):
  """Add resource arguments for creating/updating a database migration job.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    required: boolean, whether source/dest resource args are required.
  """
  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          'migration_job',
          GetMigrationJobResourceSpec(),
          'The migration job {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--source',
          GetConnectionProfileResourceSpec(),
          (
              'ID of the source connection profile, representing the source'
              ' database.'
          ),
          required=required,
          flag_name_overrides={'region': ''},
      ),
      presentation_specs.ResourcePresentationSpec(
          '--destination',
          GetConnectionProfileResourceSpec(),
          (
              'ID of the destination connection profile, representing the '
              'destination database.'
          ),
          required=required,
          flag_name_overrides={'region': ''},
      ),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--source.region': ['--region'],
          '--destination.region': ['--region'],
      },
  ).AddToParser(parser)


def AddHeterogeneousMigrationJobResourceArgs(parser, verb, required=False):
  """Add resource arguments for creating/updating a heterogeneous database mj.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    required: boolean, whether source/dest resource args are required.
  """
  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          'migration_job',
          GetMigrationJobResourceSpec(),
          'The migration job {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--source',
          GetConnectionProfileResourceSpec(),
          (
              'ID of the source connection profile, representing the source'
              ' database.'
          ),
          required=required,
          flag_name_overrides={'region': ''},
      ),
      presentation_specs.ResourcePresentationSpec(
          '--destination',
          GetConnectionProfileResourceSpec(),
          (
              'ID of the destination connection profile, representing the '
              'destination database.'
          ),
          required=required,
          flag_name_overrides={'region': ''},
      ),
      presentation_specs.ResourcePresentationSpec(
          '--conversion-workspace',
          GetConversionWorkspaceResourceSpec(),
          'Name of the conversion workspaces to be used for the migration job',
          flag_name_overrides={'region': ''},
      ),
      presentation_specs.ResourcePresentationSpec(
          '--cmek-key',
          GetCmekKeyResourceSpec(),
          (
              'Name of the CMEK (customer-managed encryption key) used for'
              ' the migration job'
          ),
          flag_name_overrides={'region': ''},
      ),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--source.region': ['--region'],
          '--destination.region': ['--region'],
          '--conversion-workspace.region': ['--region'],
          '--cmek-key.region': ['--region'],
      },
  ).AddToParser(parser)


def GetVpcResourceSpec():
  """Constructs and returns the Resource specification for VPC."""

  def VpcAttributeConfig():
    return concepts.ResourceParameterAttributeConfig(
        name='vpc',
        help_text=(
            'fully qualified name of the VPC database migration will peer to.'
        ),
    )

  return concepts.ResourceSpec(
      'compute.networks',
      resource_name='vpc',
      network=VpcAttributeConfig(),
      project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddPrivateConnectionResourceArg(parser, verb, positional=True):
  """Add a resource argument for a database migration private connection.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'private_connection'
  else:
    name = '--private-connection'

  vpc_peering_config_parser = parser.add_group(required=True)

  vpc_peering_config_parser.add_argument(
      '--subnet',
      help="""A free subnet for peering. (CIDR of /29).""",
      required=True,
  )

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetPrivateConnectionResourceSpec(),
          'The private connection {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--vpc',
          GetVpcResourceSpec(),
          'Resource name of the private connection.',
          group=vpc_peering_config_parser,
          required=True,
      ),
  ]
  concept_parsers.ConceptParser(resource_specs).AddToParser(parser)


def AddPrivateConnectionDeleteResourceArg(parser, verb, positional=True):
  """Add a resource argument for a database migration private connection.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'private_connection'
  else:
    name = '--private-connection'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetPrivateConnectionResourceSpec(),
          'The private connection {}.'.format(verb),
          required=True,
      )
  ]
  concept_parsers.ConceptParser(resource_specs).AddToParser(parser)


def AddConversionWorkspaceResourceArg(parser, verb, positional=True):
  """Add a resource argument for a database migration conversion workspace.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'conversion_workspace'
  else:
    name = '--conversion-workspace'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetConversionWorkspaceResourceSpec(),
      'The conversion workspace {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddConversionWorkspaceSeedResourceArg(parser, verb, positional=True):
  """Add a resource argument for seeding a database migration cw.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to seed'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'conversion_workspace'
  else:
    name = '--conversion-workspace'

  connection_profile = parser.add_group(mutex=True, required=True)

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetConversionWorkspaceResourceSpec(),
          'The conversion workspace {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--source-connection-profile',
          GetConnectionProfileResourceSpec(),
          'The connection profile {} from.'.format(verb),
          flag_name_overrides={'region': ''},
          group=connection_profile,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--destination-connection-profile',
          GetConnectionProfileResourceSpec(),
          'The connection profile {} from.'.format(verb),
          flag_name_overrides={'region': ''},
          group=connection_profile,
      ),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--source-connection-profile.region': ['--region'],
          '--destination-connection-profile.region': ['--region'],
      }).AddToParser(parser)


def AddConversionWorkspaceApplyResourceArg(parser, verb, positional=True):
  """Add a resource argument for applying a database migration cw.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to apply'.
    positional: bool, if True, means that the resource is a positional rather
      than a flag.
  """
  if positional:
    name = 'conversion_workspace'
  else:
    name = '--conversion-workspace'

  resource_specs = [
      presentation_specs.ResourcePresentationSpec(
          name,
          GetConversionWorkspaceResourceSpec(),
          'The conversion workspace {}.'.format(verb),
          required=True,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--destination-connection-profile',
          GetConnectionProfileResourceSpec(),
          'The connection profile {} to.'.format(verb),
          flag_name_overrides={'region': ''},
          required=True,
      ),
  ]
  concept_parsers.ConceptParser(
      resource_specs,
      command_level_fallthroughs={
          '--destination-connection-profile.region': ['--region']
      }).AddToParser(parser)
