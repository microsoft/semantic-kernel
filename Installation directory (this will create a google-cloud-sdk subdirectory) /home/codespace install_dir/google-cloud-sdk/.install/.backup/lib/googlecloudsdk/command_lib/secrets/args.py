# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Shared resource arguments and flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.secrets import completers as secrets_completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import resources

# Args


def AddDataFile(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('data-file', positional),
      metavar='PATH',
      help=('File path from which to read secret data. Set this to "-" to read '
            'the secret data from stdin.'),
      **kwargs)


def AddOutFile(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('out-file', positional),
      metavar='OUT-FILE-PATH',
      help=('File path to which secret data is written. If this flag is not '
            'provided secret data will be written to stdout in UTF-8 format.'),
      **kwargs)


def AddProject(parser, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('project', positional),
      resource_spec=GetProjectResourceSpec(),
      group_help='The project ID.',
      **kwargs).AddToParser(parser)


def AddLocation(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('location', positional),
      resource_spec=GetLocationResourceSpec(),
      group_help='The location {}.'.format(purpose),
      **kwargs).AddToParser(parser)


def AddReplicationPolicyFile(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('replication-policy-file', positional),
      metavar='REPLICATION-POLICY-FILE',
      help=(
          'JSON or YAML file to use to read the replication policy. The file '
          'must conform to '
          'https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets#replication.'
          'Set this to "-" to read from stdin.'),
      **kwargs)


def AddKmsKeyName(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('kms-key-name', positional),
      metavar='KMS-KEY-NAME',
      help=('Global KMS key with which to encrypt and decrypt the secret. Only '
            'valid for secrets with an automatic replication policy.'),
      **kwargs)


def AddSetKmsKeyName(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('set-kms-key', positional),
      metavar='SET-KMS-KEY',
      help=(
          'New KMS key with which to encrypt and decrypt future secret versions.'
      ),
      **kwargs)


def AddRemoveCmek(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('remove-cmek', positional),
      action='store_true',
      help=(
          'Remove customer managed encryption key so that future versions will '
          'be encrypted by a Google managed encryption key.'),
      **kwargs)


def AddReplicaLocation(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('location', positional),
      metavar='REPLICA-LOCATION',
      help=('Location of replica to update. For secrets with automatic '
            'replication policies, this can be omitted.'),
      **kwargs)


def AddSecret(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('secret', positional),
      resource_spec=GetSecretResourceSpec(),
      group_help='The secret {}.'.format(purpose),
      **kwargs).AddToParser(parser)


def AddVersion(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('version', positional),
      resource_spec=GetVersionResourceSpec(),
      group_help=('Numeric secret version {}.').format(purpose),
      **kwargs).AddToParser(parser)


def AddVersionOrAlias(parser, purpose, positional=False, **kwargs):
  concept_parsers.ConceptParser.ForResource(
      name=_ArgOrFlag('version', positional),
      resource_spec=GetVersionResourceSpec(),
      group_help=(
          'Numeric secret version {} or a configured alias (including \'latest\' to use the latest version).'
      ).format(purpose),
      **kwargs).AddToParser(parser)


def AddTopics(parser, positional=False, **kwargs):
  parser.add_argument(
      _ArgOrFlag('topics', positional),
      metavar='TOPICS',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=('List of Pub/Sub topics to configure on the secret.'),
      **kwargs)


def AddUpdateTopicsGroup(parser):
  """Add flags for specifying topics on secret updates."""

  group = parser.add_group(mutex=True, help='Topics.')
  group.add_argument(
      _ArgOrFlag('add-topics', False),
      metavar='ADD-TOPICS',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=('List of Pub/Sub topics to add to the secret.'))
  group.add_argument(
      _ArgOrFlag('remove-topics', False),
      metavar='REMOVE-TOPICS',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=('List of Pub/Sub topics to remove from the secret.'))
  group.add_argument(
      _ArgOrFlag('clear-topics', False),
      action='store_true',
      help=('Clear all Pub/Sub topics from the secret.'))


def AddUpdateReplicationGroup(parser):
  """Add flags for specifying replication policy updates."""
  group = parser.add_group(mutex=True, help='Replication update.')
  group.add_argument(
      _ArgOrFlag('remove-cmek', False),
      action='store_true',
      help=(
          'Remove customer managed encryption key so that future versions will '
          'be encrypted by a Google managed encryption key.'))
  subgroup = group.add_group(help='CMEK Update.')
  subgroup.add_argument(
      _ArgOrFlag('set-kms-key', False),
      metavar='SET-KMS-KEY',
      help=(
          'New KMS key with which to encrypt and decrypt future secret versions.'
      ))
  subgroup.add_argument(
      _ArgOrFlag('location', False),
      metavar='REPLICA-LOCATION',
      help=('Location of replica to update. For secrets with automatic '
            'replication policies, this can be omitted.'))


def AddCreateReplicationPolicyGroup(parser):
  """Add flags for specifying replication policy on secret creation."""

  group = parser.add_group(mutex=True, help='Replication policy.')
  group.add_argument(
      _ArgOrFlag('replication-policy-file', False),
      metavar='REPLICATION-POLICY-FILE',
      help=(
          'JSON or YAML file to use to read the replication policy. The file '
          'must conform to '
          'https://cloud.google.com/secret-manager/docs/reference/rest/v1/projects.secrets#replication.'
          'Set this to "-" to read from stdin.'))
  subgroup = group.add_group(help='Inline replication arguments.')
  subgroup.add_argument(
      _ArgOrFlag('replication-policy', False),
      metavar='POLICY',
      help=('The type of replication policy to apply to this secret. Allowed '
            'values are "automatic" and "user-managed". If user-managed then '
            '--locations must also be provided.'))
  subgroup.add_argument(
      _ArgOrFlag('kms-key-name', False),
      metavar='KMS-KEY-NAME',
      help=('Global KMS key with which to encrypt and decrypt the secret. Only '
            'valid for secrets with an automatic replication policy.'))

  subgroup.add_argument(
      _ArgOrFlag('locations', False),
      action=arg_parsers.UpdateAction,
      metavar='LOCATION',
      type=arg_parsers.ArgList(),
      help=('Comma-separated list of locations in which the secret should be '
            'replicated.'))


def AddCreateExpirationGroup(parser):
  """Add flags for specifying expiration on secret creates."""

  group = parser.add_group(mutex=True, help='Expiration.')
  group.add_argument(
      _ArgOrFlag('expire-time', False),
      metavar='EXPIRE-TIME',
      help=('Timestamp at which to automatically delete the secret.'))
  group.add_argument(
      _ArgOrFlag('ttl', False),
      metavar='TTL',
      help=(
          'Duration of time (in seconds) from the running of the command until '
          'the secret is automatically deleted.'))


def AddUpdateExpirationGroup(parser):
  """Add flags for specifying expiration on secret updates.."""

  group = parser.add_group(mutex=True, help='Expiration.')
  group.add_argument(
      _ArgOrFlag('expire-time', False),
      metavar='EXPIRE-TIME',
      help=('Timestamp at which to automatically delete the secret.'))
  group.add_argument(
      _ArgOrFlag('ttl', False),
      metavar='TTL',
      help=(
          'Duration of time (in seconds) from the running of the command until '
          'the secret is automatically deleted.'))
  group.add_argument(
      _ArgOrFlag('remove-expiration', False),
      action='store_true',
      help=(
          'If set, removes scheduled expiration from secret (if it had one).'))


def AddCreateRotationGroup(parser):
  """Add flags for specifying rotation on secret creates."""

  group = parser.add_group(mutex=False, help='Rotation.')
  group.add_argument(
      _ArgOrFlag('next-rotation-time', False),
      help=('Timestamp at which to send rotation notification.'))
  group.add_argument(
      _ArgOrFlag('rotation-period', False),
      help=('Duration of time (in seconds) between rotation notifications.'))


def AddUpdateRotationGroup(parser):
  """Add flags for specifying rotation on secret updates.."""

  group = parser.add_group(mutex=False, help='Rotation.')
  group.add_argument(
      _ArgOrFlag('next-rotation-time', False),
      help=('Timestamp at which to send rotation notification.'))
  group.add_argument(
      _ArgOrFlag('remove-next-rotation-time', False),
      action='store_true',
      help=('Remove timestamp at which to send rotation notification.'))
  group.add_argument(
      _ArgOrFlag('rotation-period', False),
      help=('Duration of time (in seconds) between rotation notifications.'))
  group.add_argument(
      _ArgOrFlag('remove-rotation-period', False),
      action='store_true',
      help=(
          'If set, removes the rotation period, cancelling all rotations except for the next one.'
      ))
  group.add_argument(
      _ArgOrFlag('remove-rotation-schedule', False),
      action='store_true',
      help=('If set, removes rotation policy from a secret.'))


def AddSecretEtag(parser):
  """Add flag for specifying the current secret etag."""
  parser.add_argument(
      _ArgOrFlag('etag', False),
      metavar='ETAG',
      help=(
          'Current entity tag (ETag) of the secret. If this flag is defined, the secret is updated only if the ETag provided matched the current secret\'s ETag.'
      ))


def AddVersionEtag(parser):
  """Add flag for specifying the current secret version etag."""
  parser.add_argument(
      _ArgOrFlag('etag', False),
      metavar='ETAG',
      help=(
          'Current entity tag (ETag) of the secret version. If this flag is defined, the version is updated only if the ETag provided matched the current version\'s ETag.'
      ))


def AddRegionalKmsKeyName(parser, positional=False, **kwargs):
  """Add flag for specifying the regional KMS key name."""
  parser.add_argument(
      _ArgOrFlag('regional-kms-key-name', positional),
      metavar='KMS-KEY-NAME',
      help=(
          'Regional KMS key with which to encrypt and decrypt the secret. Only '
          'valid for regional secrets.'
      ),
      **kwargs
  )


def _ArgOrFlag(name, positional):
  """Returns the argument name in resource argument format or flag format.

  Args:
      name (str): name of the argument
      positional (bool): whether the argument is positional

  Returns:
      arg (str): the argument or flag
  """
  if positional:
    return name.upper().replace('-', '_')
  return '--{}'.format(name)


def AddGlobalOrRegionalSecret(parser, purpose='create a secret', **kwargs):
  """Adds a secret resource.

  Secret resource can be global secret or regional secret. If command has
  "--location" then regional secret will be created or else global secret will
  be created.
  Regionl secret - projects/<project>/locations/<location>/secrets/<secret>
  Global secret - projects/<project>/secrets/<secret>

  Args:
      parser: given argument parser
      purpose: help text
      **kwargs: extra arguments
  """
  secret_or_region_secret_spec = multitype.MultitypeResourceSpec(
      'global or regional secret',
      GetSecretResourceSpec(),
      GetRegionalSecretResourceSpec(),
      allow_inactive=True,
      **kwargs,
  )

  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          'secret',
          secret_or_region_secret_spec,
          purpose,
          required=True,
          hidden=True,
      )
  ]).AddToParser(parser)


def AddGlobalOrRegionalVersion(parser, purpose='create a version', **kwargs):
  """Adds a version resource.

  Args:
      parser: given argument parser
      purpose: help text
      **kwargs: extra arguments
  """
  global_or_region_version_spec = multitype.MultitypeResourceSpec(
      'global or regional secret version',
      GetVersionResourceSpec(),
      GetRegionalVersionResourceSpec(),
      allow_inactive=True,
      **kwargs,
  )

  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          'version',
          global_or_region_version_spec,
          purpose,
          required=True,
          hidden=True,
      )
  ]).AddToParser(parser)


def AddGlobalOrRegionalVersionOrAlias(
    parser, purpose='create a version alias', **kwargs
):
  """Adds a version resource or alias.

  Args:
      parser: given argument parser
      purpose: help text
      **kwargs: extra arguments
  """
  global_or_region_version_spec = multitype.MultitypeResourceSpec(
      'global or regional secret version',
      GetVersionResourceSpec(),
      GetRegionalVersionResourceSpec(),
      allow_inactive=True,
      **kwargs,
  )

  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          'version',
          global_or_region_version_spec,
          purpose,
          required=True,
          hidden=True,
      )
  ]).AddToParser(parser)


### Attribute configurations


def GetProjectAttributeConfig():
  return concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG


def GetLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The location of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name')


def GetLocationResourceAttributeConfig():
  """Returns the attribute config for location resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text=(
          '[EXPERIMENTAL] The location of the {resource}.'
      ),
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name',
  )


def GetSecretAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='secret',
      help_text='The secret of the {resource}.',
      completer=secrets_completers.SecretsCompleter)


def GetRegionalSecretAttributeConfig():
  """Returns the attribute config for regional secret."""
  return concepts.ResourceParameterAttributeConfig(
      name='secret',
      help_text='The secret of the {resource}.',
      completer=secrets_completers.SecretsCompleter,
  )


def GetVersionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='version',
      help_text='The version of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name')


def GetRegionalVersionAttributeConfig():
  """Returns the attribute config for regional secret version."""
  return concepts.ResourceParameterAttributeConfig(
      name='version',
      help_text='The version of the {resource}.',
      completion_request_params={'fieldMask': 'name'},
      completion_id_field='name',
  )


# Resource specs


def GetProjectResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects',
      resource_name='project',
      plural_name='projects',
      disable_auto_completers=False,
      projectsId=GetProjectAttributeConfig())


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.locations',
      resource_name='location',
      plural_name='locations',
      disable_auto_completers=False,
      locationsId=GetLocationAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetSecretResourceSpec():
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.secrets',
      resource_name='secret',
      plural_name='secrets',
      disable_auto_completers=False,
      secretsId=GetSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetVersionResourceSpec():
  return concepts.ResourceSpec(
      'secretmanager.projects.secrets.versions',
      resource_name='version',
      plural_name='version',
      disable_auto_completers=False,
      versionsId=GetVersionAttributeConfig(),
      secretsId=GetSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig())


def GetRegionalSecretResourceSpec():
  """Returns the resource spec for regional secret."""
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.locations.secrets',
      resource_name='regional secret',
      plural_name='secrets',
      disable_auto_completers=False,
      secretsId=GetRegionalSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig(),
      locationsId=GetLocationResourceAttributeConfig(),
  )


def GetRegionalVersionResourceSpec():
  """Returns the resource spec for regional secret version."""
  return concepts.ResourceSpec(
      resource_collection='secretmanager.projects.locations.secrets.versions',
      resource_name='regional version',
      plural_name='version',
      disable_auto_completers=False,
      versionsId=GetRegionalVersionAttributeConfig(),
      secretsId=GetRegionalSecretAttributeConfig(),
      projectsId=GetProjectAttributeConfig(),
      locationsId=GetLocationResourceAttributeConfig(),
  )


# Resource parsers


def ParseProjectRef(ref, **kwargs):
  kwargs['collection'] = 'secretmanager.projects'
  return resources.REGISTRY.Parse(ref, **kwargs)


def ParseLocationRef(ref, **kwargs):
  kwargs['collection'] = 'secretmanager.projects.locations'
  return resources.REGISTRY.Parse(ref, **kwargs)


def ParseSecretRef(ref, **kwargs):
  kwargs['collection'] = 'secretmanager.projects.secrets'
  return resources.REGISTRY.Parse(ref, **kwargs)


# TODO(b/309085813) Refactor Usage of ParseXRef() with
# resources.REGISTRY.Parse(ref, collection=...'
def ParseRegionalSecretRef(ref, **kwargs):
  """Parses regional section secret into 'secretmanager.projects.locations.secrets' format .

  Args:
    ref: resource name of regional secret.
    **kwargs: extra arguments.

  Returns:
    Parsed secret.
  """
  kwargs['collection'] = 'secretmanager.projects.locations.secrets'
  return resources.REGISTRY.Parse(ref, **kwargs)


def ParseVersionRef(ref, **kwargs):
  kwargs['collection'] = 'secretmanager.projects.secrets.versions'
  return resources.REGISTRY.Parse(ref, **kwargs)


def ParseRegionalVersionRef(ref, **kwargs):
  """Parses regional section version into 'secretmanager.projects.locations.secrets.versions' format .

  Args:
    ref: resource name of regional secret version.
    **kwargs: extra arguments.

  Returns:
    Parsed secret version.
  """
  kwargs['collection'] = 'secretmanager.projects.locations.secrets.versions'
  return resources.REGISTRY.Parse(ref, **kwargs)
