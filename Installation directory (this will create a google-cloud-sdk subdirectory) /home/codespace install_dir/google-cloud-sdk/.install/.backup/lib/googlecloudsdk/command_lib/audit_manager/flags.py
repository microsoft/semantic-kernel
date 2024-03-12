# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the Audit Manager related commands."""

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import multitype
from googlecloudsdk.command_lib.audit_manager import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


_AUDIT_REPORT_FORMATS = ['odf']
_AUDIT_SCOPE_REPORT_FORMATS = ['odf']


def GetProjectParam(args):
  return f'--project {args.project}'


def GetFolderParam(args):
  return f'--folder {args.folder}'


def GetProjectOrFolderParam(args):
  if args.folder is None:
    return GetProjectParam(args)

  return GetFolderParam(args)


def GetLocationParam(args):
  return f'--location {args.location}'


def GetEligibleGcsBucketParam(args):
  return f'--eligible-gcs-buckets "{args.gcs_uri}"'


def GetCommandPrefix(command_path):
  idx = command_path.index('audit-manager') + 1
  return ' '.join(command_path[:idx])


def AddDescribeOperationFlags(parser):
  spec = multitype.MultitypeResourceSpec(
      'operation',
      resource_args.GetOperationResourceSpecByFolder(),
      resource_args.GetOperationResourceSpecByProject(),
      allow_inactive=True,
  )
  concept_parsers.ConceptParser([
      presentation_specs.MultitypeResourcePresentationSpec(
          'operation',
          spec,
          '',
          required=True,
      )
  ]).AddToParser(parser)


def AddProjectOrFolderFlags(parser, help_text, required=True):
  group = parser.add_mutually_exclusive_group(required=required)
  group.add_argument('--project', help='Project Id {}'.format(help_text))
  group.add_argument('--folder', help='Folder Id {}'.format(help_text))


def AddLocationFlag(parser, help_text, required=True):
  parser.add_argument(
      '--location',
      required=required,
      help='The location where {}.'.format(help_text),
  )


def AddComplianceStandardFlag(parser, required=True):
  parser.add_argument(
      '--compliance-standard',
      help=(
          'Compliance Standard against which the Report must be generated.'
          ' Eg: FEDRAMP_MODERATE'
      ),
      required=required,
  )


def AddReportFormatFlag(parser, required=True):
  parser.add_argument(
      '--report-format',
      required=required,
      choices=_AUDIT_REPORT_FORMATS,
      help='The format in which the audit report should be created.',
  )


def AddScopeReportFormatFlag(parser, required=True):
  parser.add_argument(
      '--report-format',
      required=required,
      choices=_AUDIT_SCOPE_REPORT_FORMATS,
      help='The format in which the audit scope report should be created.',
  )


def AddOutputDirectoryFormatFlag(parser, required=False):
  parser.add_argument(
      '--output-directory',
      required=required,
      help='The directory path where the scope report should be created .',
  )


def AddOutputFileNameFormatFlag(parser, required=True):
  parser.add_argument(
      '--output-file-name',
      required=required,
      help='The name by while scope report should be created .',
  )


def AddDestinationFlags(parser, required=True):
  group = parser.add_mutually_exclusive_group(required=required)
  group.add_argument(
      '--gcs-uri',
      help=(
          'Destination Cloud storage bucket where report and evidence must be'
          ' uploaded. The Cloud storage bucket provided here must be selected'
          ' among the buckets entered during the enrollment process.'
      ),
  )


def AddEligibleDestinationsFlags(parser, required=True):
  group = parser.add_group(required=required)
  group.add_argument(
      '--eligible-gcs-buckets',
      metavar='BUCKET URI',
      type=arg_parsers.ArgList(min_length=1),
      help=(
          'Eligible cloud storage buckets where report and evidence can be'
          ' uploaded.'
      ),
  )
