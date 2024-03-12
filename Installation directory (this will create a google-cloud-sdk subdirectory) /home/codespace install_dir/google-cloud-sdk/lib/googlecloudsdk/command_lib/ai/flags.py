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
"""Flag definitions for gcloud ai."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.api_lib.util import apis

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.iam import iam_util as core_iam_util
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

_POLLING_INTERVAL_FLAG = base.Argument(
    '--polling-interval',
    type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
    default=60,
    help=('Number of seconds to wait between efforts to fetch the latest '
          'log messages.'))

_ALLOW_MULTILINE_LOGS = base.Argument(
    '--allow-multiline-logs',
    action='store_true',
    default=False,
    help='Output multiline log messages as single records.')

_TASK_NAME = base.Argument(
    '--task-name',
    required=False,
    default=None,
    help='If set, display only the logs for this particular task.')

NETWORK = base.Argument(
    '--network',
    help=textwrap.dedent("""\
      Full name of the Google Compute Engine network to which the Job
      is peered with. Private services access must already have been configured.
      If unspecified, the Job is not peered with any network.
      """))

PUBLIC_ENDPOINT_ENABLED = base.Argument(
    '--public-endpoint-enabled',
    help=textwrap.dedent("""\
      If true, the deployed index will be accessible through public endpoint.
      """),
)

TRAINING_SERVICE_ACCOUNT = base.Argument(
    '--service-account',
    type=core_iam_util.GetIamAccountFormatValidator(),
    required=False,
    help=textwrap.dedent("""\
      The email address of a service account to use when running the
      training appplication. You must have the `iam.serviceAccounts.actAs`
      permission for the specified service account.
      """))

ENABLE_WEB_ACCESS = base.Argument(
    '--enable-web-access',
    action='store_true',
    required=False,
    default=False,
    help=textwrap.dedent("""\
      Whether you want Vertex AI to enable [interactive shell access](https://cloud.google.com/vertex-ai/docs/training/monitor-debug-interactive-shell)
      to training containers. If set to ``true'', you can access
      interactive shells at the URIs given by CustomJob.web_access_uris or
      Trial.web_access_uris (within HyperparameterTuningJob.trials).
      """))

ENABLE_DASHBOARD_ACCESS = base.Argument(
    '--enable-dashboard-access',
    action='store_true',
    required=False,
    default=False,
    help=textwrap.dedent(
        """\
      Whether you want Vertex AI to enable dashboard built on the training containers. If set to ``true'', you can access
      the dashboard at the URIs given by CustomJob.web_access_uris or
      Trial.web_access_uris (within HyperparameterTuningJob.trials).
      """
    ),
)


def AddStreamLogsFlags(parser):
  _POLLING_INTERVAL_FLAG.AddToParser(parser)
  _TASK_NAME.AddToParser(parser)
  _ALLOW_MULTILINE_LOGS.AddToParser(parser)


def AddUriFlags(parser, collection, api_version=None):
  """Adds `--uri` flag to the parser object for list commands.

  Args:
    parser: The argparse parser.
    collection: str, The resource collection name.
    api_version: str, The API version.
  """

  def _GetResourceUri(resource):
    updated = resources.REGISTRY.ParseRelativeName(
        resource.name, collection=collection, api_version=api_version)
    return updated.SelfLink()

  parser.display_info.AddUriFunc(_GetResourceUri)


def GetModelIdArg(required=True):
  return base.Argument(
      '--model', help='Id of the uploaded model.', required=required)


def GetDeployedModelId(required=True):
  return base.Argument(
      '--deployed-model-id',
      help='Id of the deployed model.',
      required=required)


def GetIndexIdArg(required=True, helper_text='ID of the index.'):
  return base.Argument('--index', help=helper_text, required=required)


def GetIndexEndpointIdArg(required=True,
                          helper_text='ID of the index endpoint.'):
  return base.Argument('--index-endpoint', help=helper_text, required=required)


def GetDeployedIndexId(required=True):
  return base.Argument(
      '--deployed-index-id',
      help='Id of the deployed index.',
      required=required)


def GetDisplayNameArg(noun, required=True):
  return base.Argument(
      '--display-name',
      required=required,
      help='Display name of the {noun}.'.format(noun=noun))


def GetDescriptionArg(noun):
  return base.Argument(
      '--description',
      required=False,
      default=None,
      help='Description of the {noun}.'.format(noun=noun))


def GetUserSpecifiedIdArg(noun):
  return base.Argument(
      '--{noun}-id'.format(noun=noun),
      required=False,
      default=None,
      help='User-specified ID of the {noun}.'.format(noun=noun))


def GetEndpointNetworkArg():
  return base.Argument(
      '--network',
      required=False,
      default=None,
      help="""The full name of the Google Compute Engine network to which the endpoint should be peered."""
  )


def GetEncryptionKmsKeyNameArg():
  return base.Argument(
      '--encryption-kms-key-name',
      required=False,
      default=None,
      help="""\
      The Cloud KMS resource identifier of the customer managed encryption key
      used to protect a resource. Has the form:
      projects/my-project/locations/my-region/keyRings/my-kr/cryptoKeys/my-key.

      The key needs to be in the same region as where the compute resource is
      created.
      """)


def AddPrivateServiceConnectConfig(parser):
  base.Argument('--enable-private-service-connect',
                required=False,
                default=False,
                action='store_true',
                help="""\
If true, expose the index endpoint via private service connect.
""").AddToParser(parser)

  base.Argument('--project-allowlist',
                required=False,
                metavar='PROJECTS',
                type=arg_parsers.ArgList(),
                help="""\
List of projects from which the forwarding rule will target the service
attachment.
""").AddToParser(parser)


def AddPredictInstanceArg(parser, required=True):
  """Add arguments for different types of predict instances."""
  base.Argument(
      '--json-request',
      required=required,
      help="""\
      Path to a local file containing the body of a JSON request.

      An example of a JSON request:

          {
            "instances": [
              {"x": [1, 2], "y": [3, 4]},
              {"x": [-1, -2], "y": [-3, -4]}
            ]
          }

      This flag accepts "-" for stdin.
      """).AddToParser(parser)


def GetRawPredictRequestArg():
  """Adds arguments for raw-predict requests."""
  return base.Argument(
      '--request',
      required=True,
      help="""\
      The request to send to the endpoint.

      If the request starts with the letter '*@*', the rest should be a file
      name to read the request from, or '*@-*' to read from *stdin*. If the
      request body actually starts with '*@*', it must be placed in a file.

      If required, the *Content-Type* header should also be set appropriately,
      particularly for binary data.
      """)


def GetRawPredictHeadersArg():
  """Adds arguments for raw-predict http headers."""
  return base.Argument(
      '--http-headers',
      metavar='HEADER=VALUE',
      type=arg_parsers.ArgDict(value_type=str),
      help="""\
      List of header and value pairs to send as part of the request. For
      example, to set the *Content-Type* and *X-Header*:

        --http-headers=Content-Type="application/json",X-Header=Value
      """)


def GetTrafficSplitArg():
  """Add arguments for traffic split."""
  return base.Argument(
      '--traffic-split',
      metavar='DEPLOYED_MODEL_ID=VALUE',
      type=arg_parsers.ArgDict(value_type=int),
      action=arg_parsers.UpdateAction,
      help=('List of pairs of deployed model id and value to set as traffic '
            'split.'))


def AddTrafficSplitGroupArgs(parser):
  """Add arguments for traffic split."""
  group = parser.add_mutually_exclusive_group(required=False)
  group.add_argument(
      '--traffic-split',
      metavar='DEPLOYED_MODEL_ID=VALUE',
      type=arg_parsers.ArgDict(value_type=int),
      action=arg_parsers.UpdateAction,
      help=('List of pairs of deployed model id and value to set as traffic '
            'split.'))

  group.add_argument(
      '--clear-traffic-split',
      action='store_true',
      help=('Clears the traffic split map. If the map is empty, the endpoint '
            'is to not accept any traffic at the moment.'))


def AddPredictionResourcesArgs(parser, version):
  """Add arguments for prediction resources."""
  base.Argument(
      '--min-replica-count',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      help=("""\
Minimum number of machine replicas for the deployment resources the model will be
deployed on. If specified, the value must be equal to or larger than 1.

If not specified and the uploaded models use dedicated resources, the default
value is 1.
""")).AddToParser(parser)

  base.Argument(
      '--max-replica-count',
      type=int,
      help=("""\
Maximum number of machine replicas for the deployment resources the model will be
deployed on.
""")).AddToParser(parser)

  base.Argument(
      '--machine-type',
      help="""\
The machine resources to be used for each node of this deployment.
For available machine types, see
https://cloud.google.com/ai-platform-unified/docs/predictions/machine-types.
""").AddToParser(parser)

  base.Argument(
      '--accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          }, required_keys=['type']),
      help="""\
Manage the accelerator config for GPU serving. When deploying a model with
Compute Engine Machine Types, a GPU accelerator may also
be selected.

*type*::: The type of the accelerator. Choices are {}.

*count*::: The number of accelerators to attach to each machine running the job.
 This is usually 1. If not specified, the default value is 1.

For example:
`--accelerator=type=nvidia-tesla-k80,count=1`""".format(', '.join([
    "'{}'".format(c) for c in GetAcceleratorTypeMapper(version).choices]))
  ).AddToParser(parser)


def GetAutoscalingMetricSpecsArg():
  """Add arguments for autoscaling metric specs."""
  return base.Argument(
      '--autoscaling-metric-specs',
      metavar='METRIC-NAME=TARGET',
      type=arg_parsers.ArgDict(key_type=str, value_type=int),
      action=arg_parsers.UpdateAction,
      help="""\
Metric specifications that overrides a resource utilization metric's target
value. At most one entry is allowed per metric.

*METRIC-NAME*::: Resource metric name. Choices are {}.

*TARGET*::: Target resource utilization in percentage (1% - 100%) for the
given metric. If the value is set to 60, the target resource utilization is 60%.

For example:
`--autoscaling-metric-specs=cpu-usage=70`
""".format(', '.join([
    "'{}'".format(c)
    for c in sorted(constants.OP_AUTOSCALING_METRIC_NAME_MAPPER.keys())])))


def AddDeploymentResourcesArgs(parser, resource_type):
  """Add arguments for the deployment resources."""
  base.Argument(
      '--min-replica-count',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      help=("""\
Minimum number of machine replicas the {} will be always deployed
on. If specified, the value must be equal to or larger than 1.
""".format(resource_type))).AddToParser(parser)

  base.Argument(
      '--max-replica-count',
      type=int,
      help=('Maximum number of machine replicas the {} will be '
            'always deployed on.'.format(resource_type))).AddToParser(parser)

  base.Argument(
      '--machine-type',
      help=("""\
The machine resources to be used for each node of this deployment.
For available machine types, see
https://cloud.google.com/ai-platform-unified/docs/predictions/machine-types.
""")).AddToParser(parser)


def AddMutateDeploymentResourcesArgs(parser, resource_type):
  """Add arguments for the deployment resources."""
  base.Argument(
      '--min-replica-count',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      help=("""\
Minimum number of machine replicas the {} will be always deployed
on. If specified, the value must be equal to or larger than 1.
""".format(resource_type))).AddToParser(parser)

  base.Argument(
      '--max-replica-count',
      type=int,
      help=('Maximum number of machine replicas the {} will be '
            'always deployed on.'.format(resource_type))).AddToParser(parser)


def AddReservedIpRangesArgs(parser, resource_type):
  """Add arguments for the reserved IP ranges."""
  base.Argument(
      '--reserved-ip-ranges',
      metavar='RESERVED_IP_RANGES',
      type=arg_parsers.ArgList(),
      help=('List of reserved IP ranges {} will be deployed to.'.format(
          resource_type))).AddToParser(parser)


def AddEncryptionSpecArg(parser, resource_type):
  """Add arguments for the encryption spec."""
  base.Argument(
      '--kms-key-name',
      type=str,
      help=("""\
Cloud KMS resource identifier of the customer managed encryption key used to
protect a {}. Has the form:
`projects/my-project/locations/my-region/keyRings/my-kr/cryptoKeys/my-key`.
Key needs to be in the same region as where the compute resource is created
""".format(resource_type))).AddToParser(parser)


def AddDeploymentGroupArg(parser):
  """Add arguments for deployment group."""
  base.Argument(
      '--deployment-group',
      metavar='DEPLOYMENT_GROUP',
      type=str,
      help=("""\
Deployment group can be no longer than 64 characters (eg:`test`, `prod`).
If not set, we will use the `default` deployment group.

Creating deployment_groups with `reserved_ip_ranges` is a recommended practice
when the peered network has multiple peering ranges.This creates your
deployments from predictable IP spaces for easier traffic administration.
""")).AddToParser(parser)


def AddAuthConfigArgs(parser, resource_type):
  """Add arguments for auth provider."""
  base.Argument(
      '--audiences',
      metavar='AUDIENCES',
      type=arg_parsers.ArgList(),
      help=("""\
List of JWT audiences that are allowed to access a {}.

JWT containing any of these audiences
(https://tools.ietf.org/html/draft-ietf-oauth-json-web-token-32#section -4.1.3)
will be accepted.
""").format(resource_type)).AddToParser(parser)

  base.Argument(
      '--allowed-issuers',
      metavar='ALLOWED_ISSUERS',
      type=arg_parsers.ArgList(),
      help=("""\
List of allowed JWT issuers for a {}.

Each entry must be a valid Google service account, in the following format:
`service-account-name@project-id.iam.gserviceaccount.com`
""").format(resource_type)).AddToParser(parser)


def GetEnableAccessLoggingArg():
  return base.Argument(
      '--enable-access-logging',
      action='store_true',
      default=False,
      required=False,
      help="""\
If true, online prediction access logs are sent to Cloud Logging.

These logs are standard server access logs, containing information like
timestamp and latency for each prediction request.
""")


def GetEnableContainerLoggingArg():
  return base.Argument(
      '--enable-container-logging',
      action='store_true',
      default=False,
      required=False,
      help="""\
If true, the container of the deployed model instances will send `stderr` and
`stdout` streams to Cloud Logging.

Currently, only supported for custom-trained Models and AutoML Tabular Models.
""")


def GetDisableContainerLoggingArg():
  return base.Argument(
      '--disable-container-logging',
      action='store_true',
      default=False,
      required=False,
      help="""\
For custom-trained Models and AutoML Tabular Models, the container of the
deployed model instances will send `stderr` and `stdout` streams to
Cloud Logging by default. Please note that the logs incur cost,
which are subject to [Cloud Logging
pricing](https://cloud.google.com/stackdriver/pricing).

User can disable container logging by setting this flag to true.
""")


def GetRequestResponseLoggingTableArg():
  return base.Argument(
      '--request-response-logging-table',
      required=False,
      default=None,
      help="""\
BigQuery table uri for prediction request & response logging.

You can provide table uri that does not exist, it will be created for you.

Value should be provided in format: bq://``PROJECT_ID''/``DATASET''/``TABLE''
""")


def GetRequestResponseLoggingRateArg():
  return base.Argument(
      '--request-response-logging-rate',
      required=False,
      default=None,
      type=float,
      help="""Prediction request & response sampling rate for logging to BigQuery table."""
  )


def GetDisableRequestResponseLoggingArg():
  return base.Argument(
      '--disable-request-response-logging',
      action='store_true',
      required=False,
      default=False,
      help="""Disable prediction request & response logging.""")


def AddRequestResponseLoggingConfigGroupArgs(parser):
  """Adds arguments for request-response logging configuration."""
  logging_config_group = parser.add_group(required=False)
  GetRequestResponseLoggingTableArg().AddToParser(logging_config_group)
  GetRequestResponseLoggingRateArg().AddToParser(logging_config_group)


def AddRequestResponseLoggingConfigUpdateGroupArgs(parser):
  """Adds arguments for update request-response logging configuration."""
  logging_update_group = parser.add_mutually_exclusive_group(required=False)
  GetDisableRequestResponseLoggingArg().AddToParser(logging_update_group)
  AddRequestResponseLoggingConfigGroupArgs(logging_update_group)


def GetServiceAccountArg():
  return base.Argument(
      '--service-account',
      required=False,
      help="""\
Service account that the deployed model's container runs as. Specify the
email address of the service account. If this service account is not
specified, the container runs as a service account that doesn't have access
to the resource project.
""")


def RegionAttributeConfig(prompt_func=region_util.PromptForRegion):
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='Cloud region for the {resource}.',
      fallthroughs=[
          deps.ArgFallthrough('--region'),
          deps.PropertyFallthrough(properties.VALUES.ai.region),
          deps.Fallthrough(
              function=prompt_func,
              hint='choose one from the prompted list of available regions')
      ])


def GetModelResourceSpec(resource_name='model',
                         prompt_func=region_util.PromptForRegion):
  return concepts.ResourceSpec(
      'aiplatform.projects.locations.models',
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(prompt_func=prompt_func),
      disable_auto_completers=False)


def AddRegionResourceArg(parser, verb, prompt_func=region_util.PromptForRegion):
  """Add a resource argument for a Vertex AI region.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    prompt_func: function, the function to prompt a list of available regions
      and return a string of the region that is selected by user.
  """
  region_resource_spec = concepts.ResourceSpec(
      'aiplatform.projects.locations',
      resource_name='region',
      locationsId=RegionAttributeConfig(prompt_func=prompt_func),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)

  concept_parsers.ConceptParser.ForResource(
      '--region',
      region_resource_spec,
      'Cloud region {}.'.format(verb),
      required=True).AddToParser(parser)


def GetDefaultOperationResourceSpec():
  return concepts.ResourceSpec(
      constants.DEFAULT_OPERATION_COLLECTION,
      resource_name='operation',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      disable_auto_completers=False)


def AddOperationResourceArg(parser):
  """Add a resource argument for a Vertex AI operation."""
  resource_name = 'operation'
  concept_parsers.ConceptParser.ForResource(
      resource_name,
      GetDefaultOperationResourceSpec(),
      'The ID of the operation.',
      required=True).AddToParser(parser)


def AddModelResourceArg(parser, verb, prompt_func=region_util.PromptForRegion):
  """Add a resource argument for a Vertex AI model.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    prompt_func: function, the function to prompt for region from list of
      available regions which returns a string for the region selected. Default
      is region_util.PromptForRegion which contains three regions,
      'us-central1', 'europe-west4', and 'asia-east1'.
  """
  name = 'model'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetModelResourceSpec(prompt_func=prompt_func),
      'Model {}.'.format(verb),
      required=True).AddToParser(parser)


def AddModelVersionResourceArg(parser,
                               verb,
                               prompt_func=region_util.PromptForRegion):
  """Add a resource argument for a Vertex AI model version.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    prompt_func: function, the function to prompt for region from list of
      available regions which returns a string for the region selected. Default
      is region_util.PromptForRegion which contains three regions,
      'us-central1', 'europe-west4', and 'asia-east1'.
  """
  name = 'model_version'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetModelResourceSpec(prompt_func=prompt_func),
      'Model version {}.'.format(verb),
      required=True).AddToParser(parser)


def AddUploadModelFlags(parser, prompt_func=region_util.PromptForRegion):
  """Adds flags for UploadModel.

  Args:
    parser: the parser for the command.
    prompt_func: function, the function to prompt for region from list of
      available regions which returns a string for the region selected. Default
      is region_util.PromptForRegion which contains three regions,
      'us-central1', 'europe-west4', and 'asia-east1'.
  """
  AddRegionResourceArg(parser, 'to upload model', prompt_func=prompt_func)
  base.Argument(
      '--display-name', required=True,
      help=('Display name of the model.')).AddToParser(parser)
  base.Argument(
      '--description', required=False,
      help=('Description of the model.')).AddToParser(parser)
  base.Argument(
      '--version-description',
      required=False,
      help=('Description of the model version.')).AddToParser(parser)
  base.Argument(
      '--container-image-uri',
      required=True,
      help=("""\
URI of the Model serving container file in the Container Registry
(e.g. gcr.io/myproject/server:latest).
""")).AddToParser(parser)
  base.Argument(
      '--artifact-uri',
      help=("""\
Path to the directory containing the Model artifact and any of its
supporting files.
""")).AddToParser(parser)
  parser.add_argument(
      '--container-env-vars',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help='List of key-value pairs to set as environment variables.')
  parser.add_argument(
      '--container-command',
      type=arg_parsers.ArgList(),
      metavar='COMMAND',
      action=arg_parsers.UpdateAction,
      help="""\
Entrypoint for the container image. If not specified, the container
image's default entrypoint is run.
""")
  parser.add_argument(
      '--container-args',
      metavar='ARG',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
Comma-separated arguments passed to the command run by the container
image. If not specified and no `--command` is provided, the container
image's default command is used.
""")
  parser.add_argument(
      '--container-ports',
      metavar='PORT',
      type=arg_parsers.ArgList(element_type=arg_parsers.BoundedInt(1, 65535)),
      action=arg_parsers.UpdateAction,
      help="""\
Container ports to receive http requests at. Must be a number between 1 and
65535, inclusive.
""")
  parser.add_argument(
      '--container-grpc-ports',
      metavar='PORT',
      type=arg_parsers.ArgList(element_type=arg_parsers.BoundedInt(1, 65535)),
      action=arg_parsers.UpdateAction,
      help="""\
Container ports to receive grpc requests at. Must be a number between 1 and
65535, inclusive.
""")
  parser.add_argument(
      '--container-predict-route',
      help='HTTP path to send prediction requests to inside the container.')
  parser.add_argument(
      '--container-health-route',
      help='HTTP path to send health checks to inside the container.')
  parser.add_argument(
      '--container-deployment-timeout-seconds',
      type=int,
      help='Deployment timeout in seconds.'
  )
  parser.add_argument(
      '--container-shared-memory-size-mb',
      type=int,
      help="""\
The amount of the VM memory to reserve as the shared memory for the model in
megabytes.
  """)
  parser.add_argument(
      '--container-startup-probe-exec',
      type=arg_parsers.ArgList(),
      metavar='STARTUP_PROBE_EXEC',
      help="""\
Exec specifies the action to take. Used by startup probe. An example of this
argument would be ["cat", "/tmp/healthy"].
  """)
  parser.add_argument(
      '--container-startup-probe-period-seconds',
      type=int,
      help="""\
How often (in seconds) to perform the startup probe. Default to 10 seconds.
Minimum value is 1.
  """)
  parser.add_argument(
      '--container-startup-probe-timeout-seconds',
      type=int,
      help="""\
Number of seconds after which the startup probe times out. Defaults to 1 second.
Minimum value is 1.
  """)
  parser.add_argument(
      '--container-health-probe-exec',
      type=arg_parsers.ArgList(),
      metavar='HEALTH_PROBE_EXEC',
      help="""\
Exec specifies the action to take. Used by health probe. An example of this
argument would be ["cat", "/tmp/healthy"].
  """)
  parser.add_argument(
      '--container-health-probe-period-seconds',
      type=int,
      help="""\
How often (in seconds) to perform the health probe. Default to 10 seconds.
Minimum value is 1.
  """)
  parser.add_argument(
      '--container-health-probe-timeout-seconds',
      type=int,
      help="""\
Number of seconds after which the health probe times out. Defaults to 1 second.
Minimum value is 1.
  """)

  # For Explanation.
  parser.add_argument(
      '--explanation-method',
      help='Method used for explanation. Accepted values are `integrated-gradients`, `xrai` and `sampled-shapley`.'
  )
  parser.add_argument(
      '--explanation-metadata-file',
      help='Path to a local JSON file that contains the metadata describing the Model\'s input and output for explanation.'
  )
  parser.add_argument(
      '--explanation-step-count',
      type=int,
      help='Number of steps to approximate the path integral for explanation.')
  parser.add_argument(
      '--explanation-path-count',
      type=int,
      help='Number of feature permutations to consider when approximating the Shapley values for explanation.'
  )
  parser.add_argument(
      '--smooth-grad-noisy-sample-count',
      type=int,
      help='Number of gradient samples used for approximation at explanation. Only applicable to explanation method `integrated-gradients` or `xrai`.'
  )
  parser.add_argument(
      '--smooth-grad-noise-sigma',
      type=float,
      help='Single float value used to add noise to all the features for explanation. Only applicable to explanation method `integrated-gradients` or `xrai`.'
  )
  parser.add_argument(
      '--smooth-grad-noise-sigma-by-feature',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help='Noise sigma by features for explanation. Noise sigma represents the standard deviation of the gaussian kernel that will be used to add noise to interpolated inputs prior to computing gradients. Only applicable to explanation method `integrated-gradients` or `xrai`.'
  )
  parser.add_argument(
      '--parent-model',
      type=str,
      help="""\
Resource name of the model into which to upload the version. Only specify this field when uploading a new version.

Value should be provided in format: projects/``PROJECT_ID''/locations/``REGION''/models/``PARENT_MODEL_ID''
""")
  parser.add_argument(
      '--model-id',
      type=str,
      help='ID to use for the uploaded Model, which will become the final component of the model resource name.'
  )
  parser.add_argument(
      '--version-aliases',
      metavar='VERSION_ALIASES',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help='Aliases used to reference a model version instead of auto-generated version ID. The aliases mentioned in the flag will replace the aliases set in the model.'
  )
  parser.add_argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help="""\
Labels with user-defined metadata to organize your Models.

Label keys and values can be no longer than 64 characters
(Unicode codepoints), can only contain lowercase letters, numeric
characters, underscores and dashes. International characters are allowed.

See https://goo.gl/xmQnxf for more information and examples of labels.
""")


def AddUploadModelFlagsForSimilarity(parser):
  """Adds flags for example-based explanation for UploadModel.

  Args:
    parser: the parser for the command.
  """
  base.Argument(
      '--uris',
      metavar='URIS',
      type=arg_parsers.ArgList(),
      help=("""\
Cloud Storage bucket paths where training data is stored. Should be used only
when the explanation method is `examples`.
""")).AddToParser(parser)
  parser.add_argument(
      '--explanation-neighbor-count',
      type=int,
      help='The number of items to return when querying for examples. Should be used only when the explanation method is `examples`.'
  )
  parser.add_argument(
      '--explanation-modality',
      type=str,
      default='MODALITY_UNSPECIFIED',
      help='Preset option specifying the modality of the uploaded model, which automatically configures the distance measurement and feature normalization for the underlying example index and queries. Accepted values are `IMAGE`, `TEXT` and `TABULAR`. Should be used only when the explanation method is `examples`.'
  )
  parser.add_argument(
      '--explanation-query',
      type=str,
      default='PRECISE',
      help='Preset option controlling parameters for query speed-precision trade-off. Accepted values are `PRECISE` and `FAST`. Should be used only when the explanation method is `examples`.'
  )
  parser.add_argument(
      '--explanation-nearest-neighbor-search-config-file',
      help="""\
Path to a local JSON file that contains the configuration for the generated index,
the semantics are the same as metadata and should match NearestNeighborSearchConfig.
If you specify this parameter, no need to use `explanation-modality` and `explanation-query` for preset.
Should be used only when the explanation method is `examples`.

An example of a JSON config file:

    {
    "contentsDeltaUri": "",
    "config": {
        "dimensions": 50,
        "approximateNeighborsCount": 10,
        "distanceMeasureType": "SQUARED_L2_DISTANCE",
        "featureNormType": "NONE",
        "algorithmConfig": {
            "treeAhConfig": {
                "leafNodeEmbeddingCount": 1000,
                "leafNodesToSearchPercent": 100
            }
        }
      }
    }
""")


def AddCopyModelFlags(parser, prompt_func=region_util.PromptForRegion):
  """Adds flags for AddCopyModelFlags.

  Args:
    parser: the parser for the command.
    prompt_func: function, the function to prompt a list of available regions
      and return a string of the region that is selected by user.
  """
  AddRegionResourceArg(
      parser, 'to copy the model into', prompt_func=prompt_func)

  base.Argument(
      '--source-model',
      required=True,
      help=("""\
The resource name of the Model to copy. That Model must be in the same Project.
Format: `projects/{project}/locations/{location}/models/{model}`.
""")).AddToParser(parser)

  base.Argument(
      '--kms-key-name',
      help=("""\
The Cloud KMS resource identifier of the customer managed encryption key
used to protect the resource.
Has the form:
`projects/my-project/locations/my-region/keyRings/my-kr/cryptoKeys/my-key`.
The key needs to be in the same region as the destination region of the model to be copied.
""")).AddToParser(parser)

  group = parser.add_mutually_exclusive_group(required=False)
  group.add_argument(
      '--destination-model-id',
      type=str,
      help="""\
Copy source_model into a new Model with this ID. The ID will become the final component of the model resource name.
This value may be up to 63 characters, and valid characters are `[a-z0-9_-]`. The first character cannot be a number or hyphen.
""")
  group.add_argument(
      '--destination-parent-model',
      type=str,
      help="""\
Specify this field to copy source_model into this existing Model as a new version.
Format: `projects/{project}/locations/{location}/models/{model}`.
""")


def GetMetadataFilePathArg(noun, required=False):
  return base.Argument(
      '--metadata-file',
      required=required,
      help='Path to a local JSON file that contains the additional metadata information about the {noun}.'
      .format(noun=noun))


def GetMetadataSchemaUriArg(noun):
  return base.Argument(
      '--metadata-schema-uri',
      required=False,
      help='Points to a YAML file stored on Google Cloud Storage describing additional information about {noun}.'
      .format(noun=noun))


def AddIndexResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI index.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'index', GetIndexResourceSpec(), 'Index {}.'.format(verb),
      required=True).AddToParser(parser)


def GetIndexResourceSpec(resource_name='index'):
  return concepts.ResourceSpec(
      constants.INDEXES_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(
              constants.SUPPORTED_OP_REGIONS)),
      disable_auto_completers=False)


def AddDatapointSourceGroupForStreamUpdate(noun, parser, required=False):
  """Add datapoint source group to the parser for StreamUpdate API."""
  datapoint_source_group = parser.add_mutually_exclusive_group(
      required=required)
  GetDatapointsFilePathArg(noun).AddToParser(datapoint_source_group)
  GetIndexDatapointIdsArg(noun).AddToParser(datapoint_source_group)


def GetDatapointsFilePathArg(noun, required=False):
  return base.Argument(
      '--datapoints-from-file',
      required=required,
      help='Path to a local JSON file that contains the data points that need to be added to the {noun}.'
      .format(noun=noun))


def GetDynamicMetadataUpdateMaskArg(required=False):
  return base.Argument(
      '--update-mask',
      required=required,
      metavar='UPDATE_MASK_PATH',
      type=arg_parsers.ArgList(),
      help="""\
Update mask is used to specify the fields to be
overwritten in the datapoints by the update. The fields specified in the
update_mask are relative to each IndexDatapoint inside datapoints, not
the full request.

Updatable fields:
* Use --update-mask=`all_restricts` to update both `restricts` and `numeric_restricts`.
""")


def GetIndexDatapointIdsArg(noun, required=False):
  return base.Argument(
      '--datapoint-ids',
      required=required,
      metavar='DATAPOINT_IDS',
      type=arg_parsers.ArgList(),
      help='List of index datapoint ids to be removed from the {noun}.'.format(
          noun=noun))


def GetIndexUpdateMethod(required=False):
  return base.Argument(
      '--index-update-method',
      required=required,
      type=str,
      help="""\
The update method to use with this index. Choose `stream_update` or
`batch_update`. If not set, batch update will be used by default.

`batch_update`: can update index with `gcloud ai indexes update` using
datapoints files on Cloud Storage.

`stream update`: can update datapoints with `upsert-datapoints` and
`delete-datapoints` and will be applied nearly real-time.
"""
  )


def GetDeploymentResourcePoolResourceSpec(
    resource_name='deployment_resource_pool',
    prompt_func=region_util.PromptForDeploymentResourcePoolSupportedRegion):
  return concepts.ResourceSpec(
      constants.DEPLOYMENT_RESOURCE_POOLS_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(prompt_func=prompt_func),
      disable_auto_completers=False)


def AddDeploymentResourcePoolArg(
    parser,
    verb,
    prompt_func=region_util.PromptForDeploymentResourcePoolSupportedRegion):
  """Add a resource argument for a Vertex AI deployment resource pool.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    prompt_func: function, the function to prompt for region from list of
      available regions. Default is
      region_util.PromptForDeploymentResourcePoolSupportedRegion
  """
  concept_parsers.ConceptParser.ForResource(
      'deployment_resource_pool',
      GetDeploymentResourcePoolResourceSpec(prompt_func=prompt_func),
      'The deployment resource pool {}.'.format(verb),
      required=True).AddToParser(parser)


def AddSharedResourcesArg(parser, verb):
  concept_parsers.ConceptParser([
      presentation_specs.ResourcePresentationSpec(
          '--shared-resources',
          GetDeploymentResourcePoolResourceSpec(),
          'The deployment resource pool {}.'.format(verb),
          prefixes=True)
  ]).AddToParser(parser)


def GetEndpointId():
  return base.Argument('name', help='The endpoint\'s id.')


def GetEndpointResourceSpec(resource_name='endpoint',
                            prompt_func=region_util.PromptForRegion):
  return concepts.ResourceSpec(
      constants.ENDPOINTS_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(prompt_func=prompt_func),
      disable_auto_completers=False)


def AddEndpointResourceArg(parser,
                           verb,
                           prompt_func=region_util.PromptForRegion):
  """Add a resource argument for a Vertex AI endpoint.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    prompt_func: function, the function to prompt for region from list of
      available regions. Default is region_util.PromptForRegion which contains
      three regions, 'us-central1', 'europe-west4', and 'asia-east1'.
  """
  concept_parsers.ConceptParser.ForResource(
      'endpoint',
      GetEndpointResourceSpec(prompt_func=prompt_func),
      'The endpoint {}.'.format(verb),
      required=True).AddToParser(parser)


def AddIndexEndpointResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI index endpoint.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'index_endpoint',
      GetIndexEndpointResourceSpec(),
      'The index endpoint {}.'.format(verb),
      required=True).AddToParser(parser)


def GetIndexEndpointResourceSpec(resource_name='index_endpoint'):
  return concepts.ResourceSpec(
      constants.INDEX_ENDPOINTS_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(
              constants.SUPPORTED_OP_REGIONS)),
      disable_auto_completers=False,
  )


# TODO(b/357812579): Consider switch to use resource arg.
def GetNetworkArg():
  """Add arguments for VPC network."""
  return base.Argument(
      '--network',
      help="""
      The Google Compute Engine network name to which the IndexEndpoint should be peered.
      """)


def GetPublicEndpointEnabledArg():
  """Add arguments for pubic endpoint enabled."""
  return base.Argument(
      '--public-endpoint-enabled',
      action='store_true',
      required=False,
      default=False,
      help="""
      If true, the deployed index will be accessible through public endpoint.
      """,
  )


def TensorboardRunAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='tensorboard-run-id',
      help_text='ID of the tensorboard run for the {resource}.')


def TensorboardExperimentAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='tensorboard-experiment-id',
      help_text='ID of the tensorboard experiment for the {resource}.')


def TensorboardAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='tensorboard-id',
      help_text='ID of the tensorboard for the {resource}.')


def GetTensorboardTimeSeriesResourceSpec(
    resource_name='tensorboard_time_series'):
  return concepts.ResourceSpec(
      constants.TENSORBOARD_TIME_SERIES_COLLECTION,
      resource_name=resource_name,
      tensorboardsId=TensorboardAttributeConfig(),
      experimentsId=TensorboardExperimentAttributeConfig(),
      runsId=TensorboardRunAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      disable_auto_completers=False)


def GetTensorboardRunResourceSpec(resource_name='tensorboard_run'):
  return concepts.ResourceSpec(
      constants.TENSORBOARD_RUNS_COLLECTION,
      resource_name=resource_name,
      tensorboardsId=TensorboardAttributeConfig(),
      experimentsId=TensorboardExperimentAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      disable_auto_completers=False)


def GetTensorboardExperimentResourceSpec(
    resource_name='tensorboard_experiment'):
  return concepts.ResourceSpec(
      constants.TENSORBOARD_EXPERIMENTS_COLLECTION,
      resource_name=resource_name,
      tensorboardsId=TensorboardAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      disable_auto_completers=False)


def GetTensorboardResourceSpec(resource_name='tensorboard'):
  return concepts.ResourceSpec(
      constants.TENSORBOARDS_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      disable_auto_completers=False)


def AddTensorboardTimeSeriesResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI Tensorboard time series.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'tensorboard_time_series',
      GetTensorboardTimeSeriesResourceSpec(),
      'The Tensorboard time series {}.'.format(verb),
      required=True).AddToParser(parser)


def AddTensorboardRunResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI Tensorboard run.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'tensorboard_run',
      GetTensorboardRunResourceSpec(),
      'The Tensorboard run {}.'.format(verb),
      required=True).AddToParser(parser)


def AddTensorboardExperimentResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI Tensorboard experiment.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'tensorboard_experiment',
      GetTensorboardExperimentResourceSpec(),
      'The Tensorboard experiment {}.'.format(verb),
      required=True).AddToParser(parser)


def AddTensorboardResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI Tensorboard.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'tensorboard',
      GetTensorboardResourceSpec(),
      'The tensorboard {}.'.format(verb),
      required=True).AddToParser(parser)


def GetTensorboardExperimentIdArg(required=True):
  return base.Argument(
      '--tensorboard-experiment-id',
      help='Id of the Tensorboard experiment.',
      required=required)


def GetTensorboardRunIdArg(required=True):
  return base.Argument(
      '--tensorboard-run-id',
      help='ID of the Tensorboard run.',
      required=required)


def GetPluginNameArg(noun):
  return base.Argument(
      '--plugin-name',
      required=False,
      default=None,
      help='Plugin name of the {noun}.'.format(noun=noun))


def GetPluginDataArg(noun):
  return base.Argument(
      '--plugin-data',
      required=False,
      default=None,
      help='Plugin data of the {noun}.'.format(noun=noun))


def AddTensorboardTimeSeriesMaxDataPointsArg():
  return base.Argument(
      '--max-data-points',
      type=int,
      help='Max data points to read from the Tensorboard time series')


def AddFilterArg(noun):
  return base.Argument(
      '--filter', default=None, help='Filter for the {noun}.'.format(noun=noun))


def ParseAcceleratorFlag(accelerator, version):
  """Validates and returns an accelerator config message object."""
  if accelerator is None:
    return None
  types = list(c for c in GetAcceleratorTypeMapper(version).choices)
  raw_type = accelerator.get('type', None)
  if raw_type not in types:
    raise errors.ArgumentError("""\
The type of the accelerator can only be one of the following: {}.
""".format(', '.join(["'{}'".format(c) for c in types])))
  accelerator_count = accelerator.get('count', 1)
  if accelerator_count <= 0:
    raise errors.ArgumentError("""\
The count of the accelerator must be greater than 0.
""")
  if version == constants.BETA_VERSION:
    accelerator_msg = (
        apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                               constants.AI_PLATFORM_API_VERSION[version])
        .GoogleCloudAiplatformV1beta1MachineSpec)
  else:
    accelerator_msg = (
        apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                               constants.AI_PLATFORM_API_VERSION[version])
        .GoogleCloudAiplatformV1MachineSpec)
  accelerator_type = arg_utils.ChoiceToEnum(
      raw_type, accelerator_msg.AcceleratorTypeValueValuesEnum)
  return accelerator_msg(
      acceleratorCount=accelerator_count, acceleratorType=accelerator_type)


def GetAcceleratorTypeMapper(version):
  """Get a mapper for accelerator type to enum value."""
  if version == constants.BETA_VERSION:
    return arg_utils.ChoiceEnumMapper(
        'generic-accelerator',
        apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                               constants.AI_PLATFORM_API_VERSION[version])
        .GoogleCloudAiplatformV1beta1MachineSpec.AcceleratorTypeValueValuesEnum,
        help_str='The available types of accelerators.',
        include_filter=lambda x: x.startswith('NVIDIA'),
        required=False)
  return arg_utils.ChoiceEnumMapper(
      'generic-accelerator',
      apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                             constants.AI_PLATFORM_API_VERSION[version])
      .GoogleCloudAiplatformV1MachineSpec.AcceleratorTypeValueValuesEnum,
      help_str='The available types of accelerators.',
      include_filter=lambda x: x.startswith('NVIDIA'),
      required=False)


def AddKmsKeyResourceArg(parser, resource):
  """Add the --kms-key resource arg to the given parser."""
  permission_info = ("The 'Vertex AI Service Agent' service account must hold"
                     " permission 'Cloud KMS CryptoKey Encrypter/Decrypter'")
  kms_resource_args.AddKmsKeyResourceArg(
      parser, resource, permission_info=permission_info)


def GetEndpointIdArg(required=True):
  return base.Argument(
      '--endpoint', help='Id of the endpoint.', required=required)


def GetEmailsArg(required=True):
  return base.Argument(
      '--emails',
      metavar='EMAILS',
      type=arg_parsers.ArgList(),
      help='Comma-separated email address list. e.g. --emails=a@gmail.com,b@gmail.com',
      required=required)


def GetNotificationChannelsArg(required=True):
  return base.Argument(
      '--notification-channels',
      metavar='NOTIFICATION_CHANNELS',
      type=arg_parsers.ArgList(),
      default=[],
      help=(
          'Comma-separated notification channel list. e.g.'
          ' --notification-channels=projects/fake-project/notificationChannels/123,projects/fake-project/notificationChannels/456'
      ),
      required=required)


def GetPredictionSamplingRateArg(required=True, default=1.0):
  return base.Argument(
      '--prediction-sampling-rate',
      type=float,
      default=default,
      help='Prediction sampling rate.',
      required=required)


def GetMonitoringFrequencyArg(required=False, default=24):
  return base.Argument(
      '--monitoring-frequency',
      type=int,
      default=default,
      help='Monitoring frequency, unit is 1 hour.',
      required=required)


def GetPredictInstanceSchemaArg(required=False):
  return base.Argument(
      '--predict-instance-schema',
      help="""
      YAML schema file uri(Google Cloud Storage) describing the format of a
      single instance, which are given to format this Endpoint's prediction.
      If not set, predict schema will be generated from collected predict requests.
      """,
      required=required)


def GetAnalysisInstanceSchemaArg(required=False, hidden=False):
  return base.Argument(
      '--analysis-instance-schema',
      help="""
      YAML schema file uri(Google Cloud Storage) describing the format of a
      single instance that you want Tensorflow Data Validation (TFDV) to analyze.
      """,
      hidden=hidden,
      required=required)


def GetSamplingPredictRequestArg(required=False):
  return base.Argument(
      '--sample-predict-request',
      help="""\
      Path to a local file containing the body of a JSON object. Same format as
      [PredictRequest.instances][], this can be set as a replacement of predict-instance-schema.
      If not set, predict schema will be generated from collected predict requests.

      An example of a JSON request:

          {"x": [1, 2], "y": [3, 4]}

      """,
      required=required)


def GetMonitoringLogTtlArg(required=False):
  return base.Argument(
      '--log-ttl',
      type=int,
      help="""
TTL of BigQuery tables in user projects which stores logs(Day-based unit).
""",
      required=required)


def GetMonitoringConfigFromFile():
  return base.Argument(
      '--monitoring-config-from-file',
      help=("""
Path to the model monitoring objective config file. This file should be a YAML
document containing a `ModelDeploymentMonitoringJob`(https://cloud.google.com/vertex-ai/docs/reference/rest/v1beta1/projects.locations.modelDeploymentMonitoringJobs#ModelDeploymentMonitoringJob),
but only the ModelDeploymentMonitoringObjectiveConfig needs to be configured.

Note: Only one of --monitoring-config-from-file and other objective config set,
like --feature-thresholds, --feature-attribution-thresholds needs to be set.

Example(YAML):

  modelDeploymentMonitoringObjectiveConfigs:
  - deployedModelId: '5251549009234886656'
    objectiveConfig:
      trainingDataset:
        dataFormat: csv
        gcsSource:
          uris:
          - gs://fake-bucket/training_data.csv
        targetField: price
      trainingPredictionSkewDetectionConfig:
        skewThresholds:
          feat1:
            value: 0.9
          feat2:
            value: 0.8
  - deployedModelId: '2945706000021192704'
    objectiveConfig:
      predictionDriftDetectionConfig:
        driftThresholds:
          feat1:
            value: 0.3
          feat2:
            value: 0.4
"""))


def GetFeatureThresholds():
  return base.Argument(
      '--feature-thresholds',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(allow_key_only=True),
      action=arg_parsers.UpdateAction,
      help=("""
List of feature-threshold value pairs(Apply for all the deployed models under
the endpoint, if you want to specify different thresholds for different deployed
model, please use flag --monitoring-config-from-file or call API directly).
If only feature name is set, the default threshold value would be 0.3.

For example: `--feature-thresholds=feat1=0.1,feat2,feat3=0.2`"""))


def GetFeatureAttributionThresholds():
  return base.Argument(
      '--feature-attribution-thresholds',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(allow_key_only=True),
      action=arg_parsers.UpdateAction,
      help=("""
List of feature-attribution score threshold value pairs(Apply for all the
deployed models under the endpoint, if you want to specify different thresholds
for different deployed model, please use flag --monitoring-config-from-file or
call API directly). If only feature name is set, the default threshold value
would be 0.3.

For example: `feature-attribution-thresholds=feat1=0.1,feat2,feat3=0.2`"""))


def AddObjectiveConfigGroupForUpdate(parser, required=False):
  """Add model monitoring objective config related flags to the parser for Update API.
  """
  objective_config_group = parser.add_mutually_exclusive_group(
      required=required)
  thresholds_group = objective_config_group.add_group(mutex=False)
  GetFeatureThresholds().AddToParser(thresholds_group)
  GetFeatureAttributionThresholds().AddToParser(thresholds_group)
  GetMonitoringConfigFromFile().AddToParser(objective_config_group)


def AddObjectiveConfigGroupForCreate(parser, required=False):
  """Add model monitoring objective config related flags to the parser for Create API..
  """
  objective_config_group = parser.add_mutually_exclusive_group(
      required=required)
  thresholds_group = objective_config_group.add_group(mutex=False)
  GetFeatureThresholds().AddToParser(thresholds_group)
  GetFeatureAttributionThresholds().AddToParser(thresholds_group)
  thresholds_group.add_argument(
      '--training-sampling-rate',
      type=float,
      default=1.0,
      help='Training Dataset sampling rate.')
  thresholds_group.add_argument(
      '--target-field',
      help="""
Target field name the model is to predict. Must be provided if you'd like to
do training-prediction skew detection.
""")
  training_data_group = thresholds_group.add_group(mutex=True)
  training_data_group.add_argument(
      '--dataset', help='Id of Vertex AI Dataset used to train this Model.')
  training_data_group.add_argument(
      '--bigquery-uri',
      help="""
BigQuery table of the unmanaged Dataset used to train this Model.
For example: `bq://projectId.bqDatasetId.bqTableId`.""")
  gcs_data_source_group = training_data_group.add_group(mutex=False)
  gcs_data_source_group.add_argument(
      '--data-format',
      help="""
Data format of the dataset, must be provided if the input is from Google Cloud Storage.
The possible formats are: tf-record, csv""")
  gcs_data_source_group.add_argument(
      '--gcs-uris',
      metavar='GCS_URIS',
      type=arg_parsers.ArgList(),
      help="""
Comma-separated Google Cloud Storage uris of the unmanaged Datasets used to train this Model."""
  )
  GetMonitoringConfigFromFile().AddToParser(objective_config_group)


def GetMonitoringJobResourceSpec(resource_name='monitoring_job'):
  return concepts.ResourceSpec(
      constants.MODEL_MONITORING_JOBS_COLLECTION,
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(
              constants.SUPPORTED_MODEL_MONITORING_JOBS_REGIONS)),
      disable_auto_completers=False)


def AddModelMonitoringJobResourceArg(parser, verb):
  """Add a resource argument for a Vertex AI model deployment monitoring job.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'monitoring_job',
      GetMonitoringJobResourceSpec(),
      'The model deployment monitoring job {}.'.format(verb),
      required=True).AddToParser(parser)


def GetAnomalyCloudLoggingArg(required=False):
  return base.Argument(
      '--anomaly-cloud-logging',
      action=arg_parsers.StoreTrueFalseAction,
      help="""If true, anomaly will be sent to Cloud Logging.""",
      required=required)
