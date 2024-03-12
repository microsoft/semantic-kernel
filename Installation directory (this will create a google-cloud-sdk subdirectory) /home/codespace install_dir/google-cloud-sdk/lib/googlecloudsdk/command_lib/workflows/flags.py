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
"""Shared flags for Cloud Workflows commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files

_KEY_NAME_PATTERN = (
    r'^projects/[^/]+/locations/[^/]+/keyRings/[a-zA-Z0-9_-]+'
    '/cryptoKeys/[a-zA-Z0-9_-]+$'
)
_KEY_NAME_ERROR = (
    'KMS key name should match projects/{project}/locations/{location}'
    '/keyRings/{keyring}/cryptoKeys/{cryptokey} and only contain characters '
    'from the valid character set for a KMS key.'
)
USER_ENV_VARS_LIMIT = 20
CLEAR_ENVIRONMENT = object()


def LocationAttributeConfig():
  """Builds an AttributeConfig for the location resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=[
          deps.PropertyFallthrough(properties.FromString('workflows/location'))
      ],
      help_text=(
          'Cloud location for the {resource}. '
          ' Alternatively, set the property [workflows/location].'
      ),
  )


def WorkflowAttributeConfig():
  """Builds an AttributeConfig for the workflow resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='workflow', help_text='Workflow for the {resource}.'
  )


def ExecutionAttributeConfig():
  """Builds an AttributeConfig for the execution resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='execution', help_text='Execution for the {resource}.'
  )


def GetWorkflowResourceSpec():
  """Builds a ResourceSpec for the workflow resource."""
  return concepts.ResourceSpec(
      'workflows.projects.locations.workflows',
      resource_name='workflow',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      workflowsId=WorkflowAttributeConfig(),
  )


def GetExecutionResourceSpec():
  """Builds a ResourceSpec for the execution resource."""
  return concepts.ResourceSpec(
      'workflowexecutions.projects.locations.workflows.executions',
      resource_name='execution',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      workflowsId=WorkflowAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      executionsId=ExecutionAttributeConfig(),
  )


def AddWorkflowResourceArg(parser, verb):
  """Add a resource argument for a Cloud Workflows workflow.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'workflow',
      GetWorkflowResourceSpec(),
      'Name of the workflow {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddExecutionResourceArg(parser, verb):
  """Add a resource argument for a Cloud Workflows execution.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'execution',
      GetExecutionResourceSpec(),
      'Name of the execution {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddSourceArg(parser):
  """Adds argument for specifying source for the workflow."""
  parser.add_argument(
      '--source',
      help=(
          'Location of a workflow source code to deploy. Required on first '
          'deployment. Location needs to be defined as a path to a local file '
          'with the source code.'
      ),
  )


def AddDescriptionArg(parser):
  """Adds argument for specifying description of the workflow."""
  parser.add_argument(
      '--description', help='The description of the workflow to deploy.'
  )


def AddServiceAccountArg(parser):
  """Adds argument for specifying service account used by the workflow."""
  parser.add_argument(
      '--service-account',
      help=(
          'The service account that should be used as the workflow identity.'
          ' "projects/PROJECT_ID/serviceAccounts/" prefix may be skipped from'
          ' the full resource name, in that case "projects/-/serviceAccounts/"'
          ' is prepended to the service account ID.'
      ),
  )


def AddDataArg(parser):
  """Adds argument for specifying the data that will be passed to the workflow."""
  parser.add_argument(
      '--data',
      help=(
          'JSON string with data that will be passed to the workflow '
          'as an argument.'
      ),
  )


def AddLoggingArg(parser):
  """Adds argument for specifying the logging level for an execution."""
  log_level = base.ChoiceArgument(
      '--call-log-level',
      choices={
          'none': 'No logging level specified.',
          'log-all-calls': (
              'Log all calls to subworkflows or library functions and their'
              ' results.'
          ),
          'log-errors-only': 'Log when a call is stopped due to an exception.',
          'log-none': 'Perform no call logging.',
      },
      help_str='Level of call logging to apply during execution.',
      default='none',
  )
  log_level.AddToParser(parser)


def AddDisableOverflowBufferArg(parser):
  """Adds an argument for determining whether to backlog the execution."""
  parser.add_argument(
      '--disable-concurrency-quota-overflow-buffering',
      action='store_true',
      default=False,
      help=(
          'If set, the execution will not be backlogged when the concurrency '
          'quota is exhausted. Backlogged executions start when the '
          'concurrency quota becomes available.'
      ),
  )


def AddBetaLoggingArg(parser):
  """Adds argument for specifying the logging level for an execution."""
  log_level = base.ChoiceArgument(
      '--call-log-level',
      choices={
          'none': 'Perform no call logging.',
          'log-all-calls': (
              'Log all calls to subworkflows or library functions and their'
              ' results.'
          ),
          'log-errors-only': 'Log when a call is stopped due to an exception.',
      },
      help_str='Level of call logging to apply during execution.',
      default='none',
  )
  log_level.AddToParser(parser)


def AddWorkflowLoggingArg(parser):
  """Adds argument for specifying the logging level for a workflow."""
  log_level = base.ChoiceArgument(
      '--call-log-level',
      choices={
          'none': 'No logging level specified.',
          'log-all-calls': (
              'Log all calls to subworkflows or library functions and their'
              ' results.'
          ),
          'log-errors-only': 'Log when a call is stopped due to an exception.',
          'log-none': 'Perform no call logging.',
      },
      help_str='Level of call logging to apply by default for the workflow.',
      default='none',
  )
  log_level.AddToParser(parser)


def SetWorkflowLoggingArg(loglevel, workflow, updated_fields):
  """Sets --call-log-level for the workflow based on the arguments.

  Also updates updated_fields accordingly.

  Args:
    loglevel: Parsed callLogLevel to be set on the workflow.
    workflow: The workflow in which to set the call-log-level.
    updated_fields: A list to which the call-log-level field will be added if
      needed.
  """
  if loglevel is not None:
    workflow.callLogLevel = loglevel
    updated_fields.append('callLogLevel')


# Flags for CMEK
def AddKmsKeyFlags(parser):
  """Adds flags for configuring the CMEK key.

  Args:
    parser: The flag parser used for the specified command.
  """
  kmskey_group = parser.add_group(mutex=True, hidden=True)
  kmskey_group.add_argument(
      '--kms-key',
      type=arg_parsers.RegexpValidator(_KEY_NAME_PATTERN, _KEY_NAME_ERROR),
      help="""\
        Sets the user managed KMS crypto key used to encrypt the new Workflow
        Revision and the Executions associated with it.

        The KMS crypto key name should match the pattern
        `projects/${PROJECT}/locations/${LOCATION}/keyRings/${KEYRING}/cryptoKeys/${CRYPTOKEY}`
        where ${PROJECT} is the project, ${LOCATION} is the location of the key
        ring, and ${KEYRING} is the key ring that contains the ${CRYPTOKEY}
        crypto key.
      """,
  )
  kmskey_group.add_argument(
      '--clear-kms-key',
      action='store_true',
      help="""\
        Creates the new Workflow Revision and its associated Executions without
        the KMS key specified on the previous revision.
      """,
  )


def SetKmsKey(args, workflow, updated_fields):
  """Sets KMS key for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    args: Args passed to the command.
    workflow: The workflow in which to set the KMS key.
    updated_fields: A list to which the KMS key field will be added if needed.
  """
  if args.IsSpecified('kms_key') or args.IsSpecified('clear_kms_key'):
    workflow.cryptoKeyName = None if args.clear_kms_key else args.kms_key
    updated_fields.append('cryptoKeyName')


def AddUserEnvVarsFlags(parser):
  """Adds flags for configuring user-defined environment variables."""
  userenvvars_group = parser.add_group(mutex=True, hidden=True)
  userenvvars_group.add_argument(
      '--set-env-vars',
      type=arg_parsers.ArgDict(
          key_type=str,
          value_type=str,
          max_length=USER_ENV_VARS_LIMIT,
      ),
      action=arg_parsers.UpdateAction,
      metavar='KEY=VALUE',
      help="""\
        Sets customer-defined environment variables used in the new workflow
        revision.

        This flag takes a comma-separated list of key value pairs.
        Example:
        gcloud workflows deploy ${workflow_name} --set-env-vars foo=bar,hey=hi...
      """,
  )

  map_util.AddMapSetFileFlag(
      userenvvars_group,
      'env-vars',
      'environment variables',
      key_type=str,
      value_type=str,
  )

  userenvvars_group.add_argument(
      '--clear-env-vars',
      action='store_true',
      help="""\
        Clears customer-defined environment variables used in the new workflow
        revision.

        Example:
        gcloud workflows deploy ${workflow_name} --clear-env-vars
      """,
  )

  userenvvars_group.add_argument(
      '--remove-env-vars',
      metavar='KEY',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgList(element_type=str),
      help="""\
        Removes customer-defined environment variables used in the new workflow
        revision.
        It takes a list of environment variables keys to be removed.

        Example:
        gcloud workflows deploy ${workflow_name} --remove-env-vars foo,hey...
      """,
  )

  userenvvars_group.add_argument(
      '--update-env-vars',
      type=arg_parsers.ArgDict(key_type=str, value_type=str),
      action=arg_parsers.UpdateAction,
      metavar='KEY=VALUE',
      help="""\
        Updates existing or adds new customer-defined environment variables used
        in the new workflow revision.

        This flag takes a comma-separated list of key value pairs.
        Example:
        gcloud workflows deploy ${workflow_name} --update-env-vars foo=bar,hey=hi
      """,
  )


def ParseExecution(args):
  """Get and validate execution from the args."""
  return args.CONCEPTS.execution.Parse()


def ParseExecutionLabels(args):
  """Get and validate execution labels from the args."""
  messages = apis.GetClientInstance('workflowexecutions', 'v1').MESSAGES_MODULE
  return labels_util.ParseCreateArgs(args, messages.Execution.LabelsValue)


def ParseWorkflow(args):
  """Get and validate workflow from the args."""
  return args.CONCEPTS.workflow.Parse()


def SetSource(args, workflow, updated_fields):
  """Set source for the workflow based on the arguments.

  Also update updated_fields accordingly.
  Currently only local source file is supported.

  Args:
    args: Args passed to the command.
    workflow: The workflow in which to set the source configuration.
    updated_fields: A list to which an appropriate source field will be added.
  """
  if args.source:
    try:
      workflow.sourceContents = files.ReadFileContents(args.source)
    except files.MissingFileError:
      raise exceptions.BadArgumentException(
          '--source', 'specified file does not exist.'
      )
    updated_fields.append('sourceContents')


def SetDescription(args, workflow, updated_fields):
  """Set description for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    args: Args passed to the command.
    workflow: The workflow in which to set the description.
    updated_fields: A list to which a description field will be added if needed.
  """
  if args.description is not None:
    workflow.description = args.description
    updated_fields.append('description')


def SetServiceAccount(args, workflow, updated_fields):
  """Set service account for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    args: Args passed to the command.
    workflow: The workflow in which to set the service account.
    updated_fields: A list to which a service_account field will be added if
      needed.
  """
  if args.service_account is not None:
    prefix = ''
    if not args.service_account.startswith('projects/'):
      prefix = 'projects/-/serviceAccounts/'
    workflow.serviceAccount = prefix + args.service_account
    updated_fields.append('serviceAccount')


def SetLabels(labels, workflow, updated_fields):
  """Set labels for the workflow based on the arguments.

  Also update updated_fields accordingly.

  Args:
    labels: Labels parsed as string to be set on the workflow, or None in case
      the field shouldn't be set.
    workflow: The workflow in which to set the labels.
    updated_fields: A list to which a labels field will be added if needed.
  """
  if labels is not None:
    workflow.labels = labels
    updated_fields.append('labels')


def SetUserEnvVars(env_vars, workflow, updated_fields):
  """Sets user-defined environment variables.

  Also updates updated_fields accordingly.

  Args:
    env_vars: Parsed environment variables to be set on the workflow.
    workflow: The workflow in which to set the User Envrionment Variables.
    updated_fields: A list to which the userEnvVars field will be added if
      needed.
  """
  if env_vars is None:
    return
  workflow.userEnvVars = None if env_vars is CLEAR_ENVIRONMENT else env_vars
  updated_fields.append('userEnvVars')


def UpdateUserEnvVars(env_vars, workflow, updated_fields):
  """Updates user-defined environment variables.

  Also updates updated_fields accordingly.

  Args:
    env_vars: Parsed environment variables to be set on the workflow.
    workflow: The workflow in which to set the User Envrionment Variables.
    updated_fields: A list to which the userEnvVars field will be added if
      needed.
  """
  if env_vars is None:
    return
  env_vars_cls = apis.GetClientInstance(
      'workflows',
      'v1',
  ).MESSAGES_MODULE.Workflow.UserEnvVarsValue
  workflow.userEnvVars = env_vars_cls(
      additionalProperties=[
          env_vars_cls.AdditionalProperty(key=key, value=value)
          for key, value in sorted(env_vars.items())
      ]
  )
  updated_fields.append('userEnvVars')
