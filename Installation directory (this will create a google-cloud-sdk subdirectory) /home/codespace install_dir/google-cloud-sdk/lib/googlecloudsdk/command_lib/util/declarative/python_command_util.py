# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Convenience utilities for building python calliope config export commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.declarative import flags as declarative_config_flags
from googlecloudsdk.command_lib.util.declarative.clients import kcc_client


def BuildHelpText(singular, plural=None, service=None, begins_with_vowel=False):
  """Builds and returns help text for declarative export commands."""

  # If plural not specified, just add an 's'.
  plural = plural or '{}s'.format(singular)

  # First mentions should include service name if provided.
  singular_with_service = singular
  if service:
    singular_with_service = '{} {}'.format(service, singular)

  # Determine if resource starts with a vowel and use 'a' or 'an' respectively.
  a_or_an = 'a'
  if begins_with_vowel:
    a_or_an = 'an'

  resource_name = '-'.join(singular.lower().split())

  detailed_help = {
      'brief':
          'Export the configuration for {a_or_an} {singular_with_service}.'
          .format(a_or_an=a_or_an, singular_with_service=singular_with_service),
      'DESCRIPTION':
          """\
            *{{command}}* exports the configuration for {a_or_an} {singular_with_service}.

            {singular_capitalized} configurations can be exported in
            Kubernetes Resource Model (krm) or Terraform HCL formats. The
            default format is `krm`.

            Specifying `--all` allows you to export the configurations for all
            {plural} within the project.

            Specifying `--path` allows you to export the configuration(s) to
            a local directory.
          """.format(
              singular_capitalized=singular.capitalize(),
              singular_with_service=singular_with_service,
              plural=plural,
              a_or_an=a_or_an),
      'EXAMPLES':
          """\
            To export the configuration for {a_or_an} {singular}, run:

              $ {{command}} my-{resource_name}

            To export the configuration for {a_or_an} {singular} to a file, run:

              $ {{command}} my-{resource_name} --path=/path/to/dir/

            To export the configuration for {a_or_an} {singular} in Terraform
            HCL format, run:

              $ {{command}} my-{resource_name} --resource-format=terraform

            To export the configurations for all {plural} within a
            project, run:

              $ {{command}} --all
          """.format(
              singular=singular,
              plural=plural,
              resource_name=resource_name,
              a_or_an=a_or_an)
  }
  return detailed_help


def RegisterArgs(parser, add_to_parser, **kwargs):
  mutex_group = parser.add_group(mutex=True, required=True)
  resource_group = mutex_group.add_group()
  add_to_parser(resource_group, **kwargs)
  declarative_config_flags.AddAllFlag(mutex_group, collection='project')
  declarative_config_flags.AddPathFlag(parser)
  declarative_config_flags.AddFormatFlag(parser)


def RunExport(args, collection, resource_ref):
  client = kcc_client.KccClient()
  if getattr(args, 'all', None):
    return client.ExportAll(args=args, collection=collection)
  return client.Export(args, resource_uri=resource_ref)
