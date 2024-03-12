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
"""Resource flags and helpers for the deploy command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def DeliveryPipelineAttributeConfig():
  """Creates the delivery pipeline resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='delivery-pipeline',
      fallthroughs=[
          deps.PropertyFallthrough(
              properties.FromString('deploy/delivery_pipeline')
          )
      ],
      help_text=(
          'The delivery pipeline associated with the {resource}. '
          ' Alternatively, set the property [deploy/delivery-pipeline].'
      ),
  )


def AddReleaseResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Add --release resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Release.'

  concept_parsers.ConceptParser.ForResource(
      'release' if positional else '--release',
      GetReleaseResourceSpec(),
      help_text,
      required=required,
      plural=False).AddToParser(parser)


def GetReleaseResourceSpec():
  """Constructs and returns the Resource specification for Delivery Pipeline."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deliveryPipelines.releases',
      resource_name='release',
      deliveryPipelinesId=DeliveryPipelineAttributeConfig(),
      releasesId=ReleaseAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False)


def ReleaseAttributeConfig():
  """Creates the release resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='release', help_text='The release associated with the {resource}.')


def LocationAttributeConfig():
  """Creates the location resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      parameter_name='locationsId',
      fallthroughs=[
          deps.PropertyFallthrough(properties.FromString('deploy/region'))
      ],
      help_text=(
          'The Cloud region for the {resource}. '
          ' Alternatively, set the property [deploy/region].'
      ),
  )


def AddLocationResourceArg(parser):
  """Adds a resource argument for a cloud deploy region.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
  """
  concept_parsers.ConceptParser.ForResource(
      '--region',
      GetLocationResourceSpec(),
      'The Cloud region of {resource}.',
      required=True).AddToParser(parser)


def GetLocationResourceSpec():
  """Constructs and returns the Resource specification for location."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
  )


def TargetAttributeConfig():
  """Creates the target resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='target', help_text='The target associated with the {resource}.')


def GetTargetResourceSpec():
  """Constructs and returns the target specification for Target."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.targets',
      resource_name='target',
      targetsId=TargetAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False)


def AddTargetResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Add target resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Target.'

  concept_parsers.ConceptParser.ForResource(
      'target' if positional else '--target',
      GetTargetResourceSpec(),
      help_text,
      required=required,
      plural=False).AddToParser(parser)


def AddDeliveryPipelineResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Adds --delivery-pipeline resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Delivery Pipeline.'

  concept_parsers.ConceptParser.ForResource(
      'delivery_pipeline' if positional else '--delivery-pipeline',
      GetDeliveryPipelineResourceSpec(),
      help_text,
      required=required,
      plural=False).AddToParser(parser)


def GetDeliveryPipelineResourceSpec():
  """Constructs and returns the Resource specification for Delivery Pipeline."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deliveryPipelines',
      resource_name='delivery_pipeline',
      deliveryPipelinesId=DeliveryPipelineAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False)


def RolloutAttributeConfig():
  """Creates the rollout resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='rollout', help_text='The rollout associated with the {resource}.')


def GetRolloutResourceSpec():
  """Constructs and returns the resource specification for Rollout."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
      resource_name='rollout',
      deliveryPipelinesId=DeliveryPipelineAttributeConfig(),
      releasesId=ReleaseAttributeConfig(),
      rolloutsId=RolloutAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False)


def AddRolloutResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Add --rollout resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Rollout.'

  concept_parsers.ConceptParser.ForResource(
      'rollout' if positional else '--rollout',
      GetRolloutResourceSpec(),
      help_text,
      required=required,
      plural=False).AddToParser(parser)


def GetJobRunResourceSpec():
  """Constructs and returns the Resource specification for Job Run."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deliveryPipelines.releases.rollouts.jobRuns',
      resource_name='job_run',
      deliveryPipelinesId=DeliveryPipelineAttributeConfig(),
      releasesId=ReleaseAttributeConfig(),
      rolloutsId=RolloutAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False,
  )


def AddJobRunResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Add --job-run resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Job Run.'

  concept_parsers.ConceptParser.ForResource(
      'job_run' if positional else '--job-run',
      GetJobRunResourceSpec(),
      help_text,
      required=required,
      plural=False,
  ).AddToParser(parser)


def AddAutomationRunResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Add --automation-run resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the AutomationRun.'

  concept_parsers.ConceptParser.ForResource(
      'automation_run' if positional else '--automation-run',
      GetAutomationRunResourceSpec(),
      help_text,
      required=required,
      plural=False,
  ).AddToParser(parser)


def AddAutomationResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Add --automation resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Automation.'

  concept_parsers.ConceptParser.ForResource(
      'automation' if positional else '--automation',
      GetAutomationResourceSpec(),
      help_text,
      required=required,
      plural=False,
  ).AddToParser(parser)


def GetAutomationRunResourceSpec():
  """Constructs and returns the Resource specification for AutomationRun."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deliveryPipelines.automationRuns',
      resource_name='automation_run',
      deliveryPipelinesId=DeliveryPipelineAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False,
  )


def GetAutomationResourceSpec():
  """Constructs and returns the Resource specification for Automation."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deliveryPipelines.automations',
      resource_name='automation',
      deliveryPipelinesId=DeliveryPipelineAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False,
  )


def CustomTargetTypeAttributeConfig():
  """Creates the Custom Target Type resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='custom_target_type',
      help_text='The Custom Target Type associated with the {resource}.',
  )


def GetCustomTargetTypeResourceSpec():
  """Constructs and returns the Resource specification for Custom Target Type."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.customTargetTypes',
      resource_name='custom_target_type',
      customTargetTypesId=CustomTargetTypeAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False,
  )


def AddCustomTargetTypeResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Adds --custom-target-type resource argument to the parser.

  Args:
    parser: argparse.ArgumentPArser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Custom Target Type.'

  concept_parsers.ConceptParser.ForResource(
      'custom_target_type' if positional else '--custom-target-type',
      GetCustomTargetTypeResourceSpec(),
      help_text,
      required=required,
      plural=False,
  ).AddToParser(parser)


def DeployPolicyAttributeConfig():
  """Creates the Deploy Policy resource attribute."""
  return concepts.ResourceParameterAttributeConfig(
      name='deploy_policy',
      help_text='The Deploy Policy associated with the {resource}.',
  )


def GetDeployPolicyResourceSpec():
  """Constructs and returns the Resource specification for Deploy Policy."""
  return concepts.ResourceSpec(
      'clouddeploy.projects.locations.deployPolicies',
      resource_name='deploy_policy',
      deployPoliciesId=DeployPolicyAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False,
  )


def AddDeployPolicyResourceArg(
    parser, help_text=None, positional=False, required=True
):
  """Adds --deploy-policy resource argument to the parser.

  Args:
    parser: argparse.ArgumentParser, the parser for the command.
    help_text: help text for this flag.
    positional: if it is a positional flag.
    required: if it is required.
  """
  help_text = help_text or 'The name of the Deploy Policy.'

  concept_parsers.ConceptParser.ForResource(
      'deploy_policy' if positional else '--deploy_policy',
      GetDeployPolicyResourceSpec(),
      help_text,
      required=required,
      plural=False,
  ).AddToParser(parser)
