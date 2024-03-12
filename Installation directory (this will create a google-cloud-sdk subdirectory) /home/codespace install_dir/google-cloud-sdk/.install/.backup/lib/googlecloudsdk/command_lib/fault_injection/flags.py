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
"""Flags for Fault Injection Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def GetFaultResourceSpec(arg_name='fault', help_text=None):
  """Constructs and returns the Resource specification for Fault."""

  def FaultAttributeConfig():
    return concepts.ResourceParameterAttributeConfig(
        name=arg_name, help_text=help_text
    )

  return concepts.ResourceSpec(
      'faultinjectiontesting.projects.locations.faults',
      resource_name='fault',
      faultsId=FaultAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
  )


def GetFaultResourceArg(
    arg_name='fault', help_text=None, positional=True, required=True
):
  """Constructs and returns the Fault Resource Argument."""

  help_text = help_text or 'Name for the Fault'

  return concept_parsers.ConceptParser.ForResource(
      '{}{}'.format('' if positional else '--', arg_name),
      GetFaultResourceSpec(),
      help_text,
      required=required,
  )


def GetExperimentResourceSpec(arg_name='experiment', help_text=None):
  """Constructs and returns the Resource specification for Fault."""

  def ExperimentAttributeConfig():
    return concepts.ResourceParameterAttributeConfig(
        name=arg_name, help_text=help_text
    )

  return concepts.ResourceSpec(
      'faultinjectiontesting.projects.locations.experiments',
      resource_name='experiment',
      experimentsId=ExperimentAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
  )


def GetExperimentResourceArg(
    arg_name='experiment', help_text=None, positional=True, required=True
):
  """Constructs and returns the Experiment Resource Argument."""

  help_text = help_text or 'Name for the Experiment'

  return concept_parsers.ConceptParser.ForResource(
      '{}{}'.format('' if positional else '--', arg_name),
      GetExperimentResourceSpec(),
      help_text,
      required=required,
  )


def GetJobResourceSpec(arg_name='job', help_text=None):
  """Constructs and returns the Resource specification for Job."""

  def JobAttributeConfig():
    return concepts.ResourceParameterAttributeConfig(
        name=arg_name, help_text=help_text
    )

  return concepts.ResourceSpec(
      'faultinjectiontesting.projects.locations.jobs',
      resource_name='job',
      jobsId=JobAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
  )


def GetJobResourceArg(
    arg_name='job', help_text=None, positional=True, required=True
):
  """Constructs and returns the Job Resource Argument."""

  help_text = help_text or 'Name of the Job'

  return concept_parsers.ConceptParser.ForResource(
      '{}{}'.format('' if positional else '--', arg_name),
      GetJobResourceSpec(),
      help_text,
      required=required,
  )


def LocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The Cloud location for the {resource}.',
      fallthroughs=[
          deps.ArgFallthrough('--location'),
      ],
  )


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'faultinjectiontesting.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def GetLocationResourceArg(
    arg_name='location',
    help_text=None,
    positional=False,
    required=False,
):
  """Constructs and returns the Location Resource Argument."""

  help_text = help_text or 'Location'

  return concept_parsers.ConceptParser.ForResource(
      '{}{}'.format('' if positional else '--', arg_name),
      GetLocationResourceSpec(),
      help_text,
      required=required,
  )


def AddDescribeFaultFlags(parser):
  GetFaultResourceArg().AddToParser(parser)


def AddDeleteFaultFlags(parser):
  GetFaultResourceArg().AddToParser(parser)


def AddCreateFaultFlags(parser):
  GetFaultResourceArg().AddToParser(parser)
  parser.add_argument(
      '--file',
      type=arg_parsers.YAMLFileContents(),
      metavar='FILE',
      help='The file containing the fault to be created.',
      required=True,
  )


def AddUpdateFaultFlags(parser):
  GetFaultResourceArg().AddToParser(parser)
  parser.add_argument(
      '--file',
      type=arg_parsers.YAMLFileContents(),
      metavar='FILE',
      help='The file containing the updated fault config.',
      required=True,
  )


def AddListFaultFlags(parser):
  GetLocationResourceArg(required=True).AddToParser(parser)
  parser.add_argument(
      '--service-name',
      type=str,
      help='service name.',
      required=False,
  )
  parser.add_argument(
      '--experiment-name',
      type=str,
      help='experiment name.',
      required=False,
  )


def AddDescribeExperimentFlags(parser):
  GetExperimentResourceArg().AddToParser(parser)


def AddDeleteExperimentFlags(parser):
  GetExperimentResourceArg().AddToParser(parser)


def AddCreateExperimentFlags(parser):
  GetExperimentResourceArg().AddToParser(parser)
  parser.add_argument(
      '--file',
      type=arg_parsers.YAMLFileContents(),
      metavar='FILE',
      help='The file containing the experiment to be created.',
      required=True,
  )


def AddUpdateExperimentFlags(parser):
  GetExperimentResourceArg().AddToParser(parser)
  parser.add_argument(
      '--file',
      type=arg_parsers.YAMLFileContents(),
      metavar='FILE',
      help='The file containing the updated experiment config.',
      required=True,
  )


def AddListExperimentFlags(parser):
  GetLocationResourceArg(required=True).AddToParser(parser)
  parser.add_argument(
      '--sd-service-name',
      type=str,
      help='service name.',
      required=False,
  )


def AddDescribeJobFlags(parser):
  GetJobResourceArg().AddToParser(parser)


def AddListJobFlags(parser):
  """Add job list Flags."""

  GetLocationResourceArg(required=True).AddToParser(parser)
  concept_parsers.ConceptParser([
      presentation_specs.ResourcePresentationSpec(
          '--experiment',
          GetExperimentResourceSpec(),
          'The experiment resource.',
          prefixes=True,
          required=False,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--fault',
          GetFaultResourceSpec(),
          'The fault resource.',
          prefixes=True,
          required=False,
      ),
  ]).AddToParser(parser)
  parser.add_argument(
      '--target-name',
      type=str,
      help='target name.',
      required=False,
  )
  parser.add_argument(
      '--days',
      type=int,
      help='Days.',
      required=False,
  )


def AddCreateJobFlags(parser):
  """Add job Create Flags."""

  concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              'JOB',
              GetJobResourceSpec(),
              'The Job resource.',
              flag_name_overrides={'location': '--location'},
              prefixes=True,
              required=True,
          ),
          presentation_specs.ResourcePresentationSpec(
              '--experiment',
              GetExperimentResourceSpec(),
              'The experiment resource.',
              # This hides the location flag for experiment resource.
              flag_name_overrides={
                  'location': '',
                  'project': '',
              },
              prefixes=True,
              required=True,
          ),
      ],
  ).AddToParser(parser)
  parser.add_argument(
      '--fault-targets',
      type=arg_parsers.ArgList(),
      metavar='LIST',
      help='targets for the faults in experiment. Provide them in sequence',
      required=True,
  )
  parser.add_argument(
      '--dry-run',
      action='store_true',
      default=False,
      help='Dry run mode.',

  )


def AddDeleteJobFlags(parser):
  GetJobResourceArg().AddToParser(parser)
