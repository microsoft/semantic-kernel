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
"""Flags for binauthz command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.container.binauthz import arg_parsers
from googlecloudsdk.command_lib.kms import flags as kms_flags
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs as presentation_specs_lib


def _GetNoteResourceSpec():
  return concepts.ResourceSpec(
      'containeranalysis.projects.notes',
      resource_name='note',
      projectsId=concepts.ResourceParameterAttributeConfig(
          name='project',
          help_text='The Container Analysis project for the {resource}.',
      ),
      notesId=concepts.ResourceParameterAttributeConfig(
          name='note',
          help_text='The Container Analysis Note ID for the {resource}.',
      ),
  )


def _FormatArgName(base_name, positional):
  if positional:
    return base_name.replace('-', '_').upper()
  else:
    return '--' + base_name.replace('_', '-').lower()


def GetNotePresentationSpec(
    group_help,
    base_name='note',
    required=True,
    positional=True,
    use_global_project_flag=False,
):
  """Construct a resource spec for a Container Analysis note flag."""
  flag_overrides = None
  if not use_global_project_flag:
    flag_overrides = {
        'project': _FormatArgName('{}-project'.format(base_name), positional),
    }
  return presentation_specs_lib.ResourcePresentationSpec(
      name=_FormatArgName(base_name, positional),
      concept_spec=_GetNoteResourceSpec(),
      group_help=group_help,
      required=required,
      flag_name_overrides=flag_overrides,
  )


def _GetAttestorResourceSpec():
  return concepts.ResourceSpec(
      'binaryauthorization.projects.attestors',
      resource_name='attestor',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      attestorsId=concepts.ResourceParameterAttributeConfig(
          name='name',
          help_text='The ID of the {resource}.',
      ),
  )


def GetAttestorPresentationSpec(
    group_help,
    base_name='attestor',
    required=True,
    positional=True,
    use_global_project_flag=True,
):
  """Construct a resource spec for an attestor flag."""
  flag_overrides = None
  if not use_global_project_flag:
    flag_overrides = {
        'project': _FormatArgName('{}-project'.format(base_name), positional),
    }
  return presentation_specs_lib.ResourcePresentationSpec(
      name=_FormatArgName(base_name, positional),
      concept_spec=_GetAttestorResourceSpec(),
      group_help=group_help,
      required=required,
      flag_name_overrides=flag_overrides,
  )


def _GetCryptoKeyVersionResourceSpec():
  return concepts.ResourceSpec(
      kms_flags.CRYPTO_KEY_VERSION_COLLECTION,
      resource_name='CryptoKeyVersion',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=concepts.ResourceParameterAttributeConfig(
          name='location',
          help_text='The location of the {resource}.',
      ),
      keyRingsId=concepts.ResourceParameterAttributeConfig(
          name='keyring',
          help_text='The keyring of the {resource}.',
      ),
      cryptoKeysId=concepts.ResourceParameterAttributeConfig(
          name='key',
          help_text='The key of the {resource}.',
      ),
      cryptoKeyVersionsId=concepts.ResourceParameterAttributeConfig(
          name='version',
          help_text='The key version of the {resource}.',
      ),
  )


def GetCryptoKeyVersionPresentationSpec(
    group_help,
    base_name='keyversion',
    required=True,
    positional=True,
    use_global_project_flag=True,
):
  """Construct a resource spec for a CryptoKeyVersion flag."""
  flag_overrides = None
  if not use_global_project_flag:
    flag_overrides = {
        'project': _FormatArgName('{}-project'.format(base_name), positional),
    }
  return presentation_specs_lib.ResourcePresentationSpec(
      name=_FormatArgName(base_name, positional),
      concept_spec=_GetCryptoKeyVersionResourceSpec(),
      group_help=group_help,
      required=required,
      prefixes=not use_global_project_flag,
      flag_name_overrides=flag_overrides,
  )


def AddConcepts(parser, *presentation_specs):
  concept_parsers.ConceptParser(presentation_specs).AddToParser(parser)


def AddArtifactUrlFlag(parser, required=True):
  parser.add_argument(
      '--artifact-url',
      required=required,
      type=str,
      help=(
          'Container URL. May be in the `gcr.io/repository/image` format,'
          ' or may optionally contain the `http` or `https` scheme'
      ),
  )


def _GetPlatformResourceSpec():
  return concepts.ResourceSpec(
      'binaryauthorization.projects.platforms',
      resource_name='platform',
      api_version='v1',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      platformsId=concepts.ResourceParameterAttributeConfig(
          name='platform', help_text='The platform.'
      ),
  )


def AddPlatformResourceArg(parser, verb):
  """Add a resource argument for a platform (containing platform policies).

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to list'. (No other
      values besides 'to list' are expected.)
  """
  # Note: "resource arguments" (go/gcloud-creating-commands#resource-arguments)
  # requires the main resource to be a positional argument, not a keyword, so
  # --platform is not allowed when the main resource is a platform, even though
  # it is allowed when the main resource is a policy.
  concept_parsers.ConceptParser.ForResource(
      'platform_resource_name',
      _GetPlatformResourceSpec(),
      'The platform whose policies {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def _GetPlatformPolicyResourceSpec():
  return concepts.ResourceSpec(
      'binaryauthorization.projects.platforms.policies',
      resource_name='policy',
      api_version='v1',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      platformsId=concepts.ResourceParameterAttributeConfig(
          name='platform',
          help_text=(
              'The platform that the {resource} belongs to. '
              'PLATFORM must be one of the following: cloudRun, gke.'
          ),
      ),
      policyId=concepts.ResourceParameterAttributeConfig(
          name='policy', help_text='The ID of the {resource}.'
      ),
  )


def AddPlatformPolicyResourceArg(parser, verb):
  """Add a resource argument for a policy.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'policy_resource_name',
      _GetPlatformPolicyResourceSpec(),
      'The resource name of the policy {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddEvaluationUnitArg(parser):
  """Adds a resource argument from file or from one or more images."""
  evaluation_unit_group = parser.add_group(mutex=True, required=True)
  evaluation_unit_group.add_argument(
      '--resource',
      required=False,
      type=arg_parsers.ResourceFileName,
      help=(
          'The JSON or YAML file containing the Kubernetes resource to'
          ' evaluate.'
      ),
  )
  evaluation_unit_group.add_argument(
      '--image',
      required=False,
      action='append',
      help=(
          'The image to evaluate. If the policy being evaluated has scoped'
          ' checksets, this mode of evaluation will always use the default'
          ' (unscoped) checkset.'
      ),
  )


def AddNoUploadArg(parser):
  """Adds a --no-upload flag to parser."""
  parser.add_argument(
      '--no-upload',
      action='store_true',
      default=False,
      help=(
          'Do not upload the generated attestations to the image registry'
          ' (using Sigstore tag conventions). Note, attestations are never'
          ' uploaded to the transparency log.'
      ),
  )


def AddOutputFileArg(parser):
  """Adds the output file argument to parser."""
  parser.add_argument(
      '--output-file',
      help=(
          'If a resource is provided and deemed to be conformant, attestations'
          ' will be added as annotations on the resource and writen back to'
          ' this file path in the same format as the input file.'
      ),
  )


def AddDockerCredsArgs(parser):
  """Adds the docker creds args to parser."""
  docker_args_group = parser.add_group(mutex=False, required=False)
  docker_args_group.add_argument(
      '--use-docker-creds',
      required=False,
      action='store_true',
      default=False,
      help=(
          'Whether to use the configuration file where Docker saves'
          ' authentication credentials when uploading attestations to the'
          ' registry. If this flag is not passed, or valid credentials are not'
          ' found, an OAuth2 token for the active gcloud account is used. See'
          ' https://cloud.google.com/artifact-registry/docs/docker/authentication'
          ' for more information.'
      ),
  )
  docker_args_group.add_argument(
      '--docker-config-dir',
      required=False,
      help=(
          'Override the directory where the Docker configuration file is'
          ' searched for. Credentials are pulled from the config.json file'
          ' under this directory. Defaults to $HOME/.docker.'
      ),
  )
