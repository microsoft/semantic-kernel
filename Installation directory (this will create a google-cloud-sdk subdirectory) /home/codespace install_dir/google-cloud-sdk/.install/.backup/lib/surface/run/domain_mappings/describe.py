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

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.Command):
  """Describe domain mappings for Cloud Run for Anthos."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}

          For domain mapping support with fully managed Cloud Run, use
          `gcloud beta run domain-mappings describe`.""",
      'EXAMPLES':
          """\
          To describe a Cloud Run domain mapping, run:

              $ {command} --domain=www.example.com
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    domain_mapping_presentation = presentation_specs.ResourcePresentationSpec(
        '--domain',
        resource_args.GetDomainMappingResourceSpec(),
        'Domain name is the ID of DomainMapping resource.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([
        domain_mapping_presentation]).AddToParser(parser)

    parser.display_info.AddFormat('yaml')

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def Run(self, args):
    """Describe a domain mapping."""
    # domains.cloudrun.com api group only supports v1alpha1 on clusters.
    conn_context = connection_context.GetConnectionContext(
        args,
        flags.Product.RUN,
        self.ReleaseTrack(),
        version_override=('v1alpha1' if
                          platforms.GetPlatform() != platforms.PLATFORM_MANAGED
                          else None))
    domain_mapping_ref = args.CONCEPTS.domain.Parse()
    with serverless_operations.Connect(conn_context) as client:
      domain_mapping = client.GetDomainMapping(domain_mapping_ref)
      if not domain_mapping:
        raise exceptions.ArgumentError(
            'Cannot find domain mapping for domain name [{}]'.format(
                domain_mapping_ref.domainmappingsId))
      return domain_mapping


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaDescribe(Describe):
  """Describe domain mappings."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To describe a Cloud Run domain mapping, run:

              $ {command} --domain=www.example.com
          """,
  }

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDescribe(BetaDescribe):
  """Describe domain mappings."""

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)
