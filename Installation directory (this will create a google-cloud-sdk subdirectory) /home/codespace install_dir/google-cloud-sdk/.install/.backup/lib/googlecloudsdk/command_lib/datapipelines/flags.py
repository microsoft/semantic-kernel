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
"""Flags and helpers for the compute related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region', help_text='The Cloud region for the {resource}.')


def GetPipelineResourceArg(arg_name='pipeline',
                           help_text=None,
                           positional=True,
                           required=True):
  """Constructs and returns the Pipeline Resource Argument."""

  def GetPipelineResourceSpec():
    """Constructs and returns the Resource specification for Pipeline."""

    def PipelineAttributeConfig():
      return concepts.ResourceParameterAttributeConfig(
          name=arg_name, help_text=help_text)

    return concepts.ResourceSpec(
        'datapipelines.projects.locations.pipelines',
        resource_name='pipeline',
        pipelinesId=PipelineAttributeConfig(),
        locationsId=RegionAttributeConfig(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
        disable_auto_completers=False)

  help_text = help_text or 'Name for the Data Pipelines Pipeline.'

  return concept_parsers.ConceptParser.ForResource(
      '{}{}'.format('' if positional else '--', arg_name),
      GetPipelineResourceSpec(),
      help_text,
      required=required)


def AddCreatePipelineFlags(parser):
  GetPipelineResourceArg().AddToParser(parser)


def AddUpdatePipelineFlags(parser):
  GetPipelineResourceArg().AddToParser(parser)


def AddDescribePipelineFlags(parser):
  GetPipelineResourceArg().AddToParser(parser)


def AddDeletePipelineFlags(parser):
  GetPipelineResourceArg().AddToParser(parser)


def AddStopPipelineFlags(parser):
  GetPipelineResourceArg().AddToParser(parser)


def AddRunPipelineFlags(parser):
  GetPipelineResourceArg().AddToParser(parser)


def AddListJobsFlags(parser):
  GetPipelineResourceArg(positional=False).AddToParser(parser)


def AddRegionResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI region.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  region_resource_spec = concepts.ResourceSpec(
      'datapipelines.projects.locations',
      resource_name='region',
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)

  concept_parsers.ConceptParser.ForResource(
      '--region',
      region_resource_spec,
      'Cloud region {}.'.format(verb),
      required=True).AddToParser(parser)


def GetDisplayNameArg(noun, required=False):
  return base.Argument(
      '--display-name',
      required=required,
      help='Display name of the {noun}.'.format(noun=noun))


def GetPipelineTypeArg(required=True):
  choices = {
      'batch': 'Specifies a Batch pipeline.',
      'streaming': 'Specifies a Streaming pipeline.'
  }
  return base.ChoiceArgument(
      '--pipeline-type',
      choices=choices,
      required=required,
      help_str="""Type of the pipeline. One of 'BATCH' or 'STREAMING'.""")


def GetTemplateTypeArg(required=False):
  choices = {
      'flex': 'Specifies a Flex template.',
      'classic': 'Specifies a Classic template'
  }
  return base.ChoiceArgument(
      '--template-type',
      choices=choices,
      required=required,
      default='FLEX',
      help_str="""Type of the template. Defaults to flex template. One of 'FLEX' or 'CLASSIC'"""
  )


def GetScheduleArg(required=False):
  return base.Argument(
      '--schedule',
      required=required,
      default=None,
      help="""Unix-cron format of the schedule for scheduling recurrent jobs."""
  )


def GetTimeZoneArg(required=False):
  return base.Argument(
      '--time-zone',
      required=required,
      default=None,
      help="""Timezone ID. This matches the timezone IDs used by the Cloud Scheduler API."""
  )


def GetTemplateFileGcsLocationArg(required=False):
  return base.Argument(
      '--template-file-gcs-location',
      required=required,
      default=None,
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''),
      help="""Location of the template file or container spec file in Google Cloud Storage."""
  )


def GetParametersArg(required=False):
  return base.Argument(
      '--parameters',
      required=required,
      default=None,
      metavar='PARAMETERS',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help="""User defined parameters for the template.""")


def GetMaxWorkersArg(required=False):
  return base.Argument(
      '--max-workers',
      required=required,
      default=None,
      type=int,
      help="""Maximum number of workers to run by default. Must be between 1 and 1000."""
  )


def GetNumWorkersArg(required=False):
  return base.Argument(
      '--num-workers',
      required=required,
      default=None,
      type=int,
      help="""Initial number of workers to run by default. Must be between 1 and 1000. If not specified here, defaults to server-specified value."""
  )


def GetNetworkArg(required=False):
  return base.Argument(
      '--network',
      required=required,
      default=None,
      help="""Default Compute Engine network for launching instances to run your pipeline. If not specified here, defaults to the network 'default'."""
  )


def GetSubnetworkArg(required=False):
  return base.Argument(
      '--subnetwork',
      required=required,
      default=None,
      help="""Default Compute Engine subnetwork for launching instances to run your pipeline."""
  )


def GetWorkerMachineTypeArg(required=False):
  return base.Argument(
      '--worker-machine-type',
      required=required,
      default=None,
      help="""Default type of machine to use for workers. If not specified here, defaults to server-specified value."""
  )


def GetTempLocationArg(required=False):
  return base.Argument(
      '--temp-location',
      required=required,
      default=None,
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''),
      help="""Default Google Cloud Storage location to stage temporary files. If not set, defaults to the value for staging-location (Must be a URL beginning with 'gs://'.)"""
  )


def GetDataflowKmsKeyArg(required=False):
  return base.Argument(
      '--dataflow-kms-key',
      required=required,
      default=None,
      help="""Default Cloud KMS key to protect the job resources. The key must be in same location as the job."""
  )


def GetDisablePublicIpsArg(required=False):
  return base.Argument(
      '--disable-public-ips',
      required=required,
      default=None,
      action=actions.StoreBooleanProperty(
          properties.VALUES.datapipelines.disable_public_ips),
      help="""Specifies that Cloud Dataflow workers must not use public IP addresses by default."""
  )


def GetDataflowServiceAccountEmailArg(required=False):
  return base.Argument(
      '--dataflow-service-account-email',
      required=required,
      default=None,
      help="""Default service account to run the dataflow workers as.""")


def GetEnableStreamingEngineArg(required=False):
  return base.Argument(
      '--enable-streaming-engine',
      required=required,
      default=None,
      action=actions.StoreBooleanProperty(
          properties.VALUES.datapipelines.enable_streaming_engine),
      help="""Specifies that enabling Streaming Engine for the job by default."""
  )


def GetAdditionalExperimentsArg(required=False):
  return base.Argument(
      '--additional-experiments',
      required=required,
      default=None,
      metavar='ADDITIONAL_EXPERIMENTS',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""Default experiment flags for the job.""")


def GetAdditionalUserLabelsArg(required=False):
  return base.Argument(
      '--additional-user-labels',
      required=required,
      default=None,
      metavar='ADDITIONAL_USER_LABELS',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help="""Default user labels to be specified for the job. Keys and values must follow the restrictions specified in https://cloud.google.com/compute/docs/labeling-resources#restrictions."""
  )


def GetWorkerRegionArgs(required=False):
  """Defines the Streaming Update Args for the Pipeline."""
  worker_region_args = base.ArgumentGroup(required=required, mutex=True)
  worker_region_args.AddArgument(
      base.Argument(
          '--worker-region',
          required=required,
          default=None,
          help="""Default Compute Engine region in which worker processing will occur."""
      ))
  worker_region_args.AddArgument(
      base.Argument(
          '--worker-zone',
          required=required,
          default=None,
          help="""Default Compute Engine zone in which worker processing will occur."""
      ))
  return worker_region_args


def GetFlexRsGoalArg(required=False):
  return base.Argument(
      '--flexrs-goal',
      required=required,
      default=None,
      help="""FlexRS goal for the flex template job.""",
      choices=['COST_OPTIMIZED', 'SPEED_OPTIMIZED'])


def GetStreamingUpdateArgs(required=False):
  """Defines the Streaming Update Args for the Pipeline."""
  streaming_update_args = base.ArgumentGroup(required=required)
  streaming_update_args.AddArgument(
      base.Argument(
          '--update',
          required=required,
          action=arg_parsers.StoreTrueFalseAction,
          help="""Set this to true for streaming update jobs."""))
  streaming_update_args.AddArgument(
      base.Argument(
          '--transform-name-mappings',
          required=required,
          default=None,
          metavar='TRANSFORM_NAME_MAPPINGS',
          type=arg_parsers.ArgDict(),
          action=arg_parsers.UpdateAction,
          help="""Transform name mappings for the streaming update job."""))
  return streaming_update_args
