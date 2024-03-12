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
"""Surface for creating domain mappings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import deletion
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import console_io

DOMAIN_MAPPINGS_HELP_DOCS_URL = ('https://cloud.google.com/run/docs/'
                                 'mapping-custom-domains/')


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create domain mappings for Cloud Run for Anthos."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          For domain mapping support with fully managed Cloud Run, use
          `gcloud beta run domain-mappings create`.
          """,
      'EXAMPLES':
          """\
          To create a Cloud Run domain mapping, run:

              $ {command} --service=myapp --domain=www.example.com
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    parser.add_argument(
        '--service', required=True,
        help='Create domain mapping for the given service.')
    domain_mapping_presentation = presentation_specs.ResourcePresentationSpec(
        '--domain',
        resource_args.GetDomainMappingResourceSpec(),
        'Domain name is the ID of DomainMapping resource.',
        required=True,
        prefixes=False)
    parser.add_argument(
        '--force-override',
        action='store_true',
        help='Map this domain even if it is already mapped to another service.'
    )
    concept_parsers.ConceptParser([
        domain_mapping_presentation]).AddToParser(parser)

    parser.display_info.AddFormat(
        """table(
        name:label=NAME,
        type:label="RECORD TYPE",
        rrdata:label=CONTENTS)""")

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)

  def Run(self, args):
    """Create a domain mapping."""
    # domains.cloudrun.com api group only supports v1alpha1 on clusters.
    conn_context = connection_context.GetConnectionContext(
        args,
        flags.Product.RUN,
        self.ReleaseTrack(),
        version_override=('v1alpha1' if
                          platforms.GetPlatform() != platforms.PLATFORM_MANAGED
                          else None))
    domain_mapping_ref = args.CONCEPTS.domain.Parse()
    changes = [
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
    ]

    # Check if the provided domain has already been verified
    # if mapping to a non-CRoGKE service
    if platforms.GetPlatform() == platforms.PLATFORM_MANAGED:
      client = global_methods.GetServerlessClientInstance()
      all_domains = global_methods.ListVerifiedDomains(client)
      # If not already verified, explain and error out
      if all(d.id not in domain_mapping_ref.Name() for d in all_domains):
        if not all_domains:
          domains_text = 'You currently have no verified domains.'
        else:
          domains = ['* {}'.format(d.id) for d in all_domains]
          domains_text = ('Currently verified domains:\n{}'.format(
              '\n'.join(domains)))
        raise exceptions.DomainMappingCreationError(
            'The provided domain does not appear to be verified '
            'for the current account so a domain mapping '
            'cannot be created. Visit [{help}] for more information.'
            '\n{domains}'.format(
                help=DOMAIN_MAPPINGS_HELP_DOCS_URL, domains=domains_text))

    with serverless_operations.Connect(conn_context) as client:
      try:
        mapping = client.CreateDomainMapping(domain_mapping_ref, args.service,
                                             changes, args.force_override)
      except exceptions.DomainMappingAlreadyExistsError as e:
        if console_io.CanPrompt() and console_io.PromptContinue(
            ('This domain is already being used as a mapping elsewhere. '
             'The existing mapping can be overriden by passing '
             '`--force-override` or by continuing at the prompt below.'),
            prompt_string='Override the existing mapping'):
          deletion.Delete(domain_mapping_ref, client.GetDomainMapping,
                          client.DeleteDomainMapping, async_=False)
          mapping = client.CreateDomainMapping(domain_mapping_ref, args.service,
                                               changes, True)
        else:
          raise e

      for record in mapping.records:
        record.name = record.name or mapping.route_name
      return mapping.records


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaCreate(Create):
  """Create domain mappings."""

  detailed_help = {
      'DESCRIPTION': '{description}',
      'EXAMPLES':
          """\
          To create a Cloud Run domain mapping, run:

              $ {command} --service=myapp --domain=www.example.com
          """,
  }

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaCreate(BetaCreate):
  """Create domain mappings."""

  @staticmethod
  def Args(parser):
    Create.CommonArgs(parser)
