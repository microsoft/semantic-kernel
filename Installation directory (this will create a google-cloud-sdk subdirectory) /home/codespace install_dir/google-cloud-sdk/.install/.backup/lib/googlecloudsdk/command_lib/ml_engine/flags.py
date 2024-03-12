# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Provides common arguments for the AI Platform command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import functools
import itertools
import sys
import textwrap

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam import completers as iam_completers
from googlecloudsdk.command_lib.iam import iam_util as core_iam_util
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.ml_engine import constants
from googlecloudsdk.command_lib.ml_engine import models_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


_JOB_SUMMARY = """\
table[box,title="Job Overview"](
  jobId,
  createTime,
  startTime,
  endTime,
  state,
  {INPUT},
  {OUTPUT})
"""

_JOB_TRAIN_INPUT_SUMMARY_FORMAT = """\
trainingInput:format='table[box,title="Training Input Summary"](
  runtimeVersion:optional,
  region,
  scaleTier:optional,
  pythonModule,
  parameterServerType:optional,
  parameterServerCount:optional,
  masterType:optional,
  workerType:optional,
  workerCount:optional,
  jobDir:optional
)'
"""

_JOB_TRAIN_OUTPUT_SUMMARY_FORMAT = """\
trainingOutput:format='table[box,title="Training Output Summary"](
  completedTrialCount:optional:label=TRIALS,
  consumedMLUnits:label=ML_UNITS)'
  {HP_OUTPUT}
"""

_JOB_TRAIN_OUTPUT_TRIALS_FORMAT = """\
,trainingOutput.trials.sort(trialId):format='table[box,title="Training Output Trials"](
  trialId:label=TRIAL,
  finalMetric.objectiveValue:label=OBJECTIVE_VALUE,
  finalMetric.trainingStep:label=STEP,
  hyperparameters.list(separator="\n"))'
"""

_JOB_PREDICT_INPUT_SUMMARY_FORMAT = """\
predictionInput:format='table[box,title="Predict Input Summary"](
  runtimeVersion:optional,
  region,
  model.basename():optional,
  versionName.basename(),
  outputPath,
  uri:optional,
  dataFormat,
  batchSize:optional
)'
"""

_JOB_PREDICT_OUTPUT_SUMMARY_FORMAT = """\
predictionOutput:format='table[box,title="Predict Output Summary"](
  errorCount,
  nodeHours,
  outputPath,
  predictionCount
  )'
"""


class ArgumentError(exceptions.Error):
  pass


class MlEngineIamRolesCompleter(iam_completers.IamRolesCompleter):

  def __init__(self, **kwargs):
    super(MlEngineIamRolesCompleter, self).__init__(
        resource_collection=models_util.MODELS_COLLECTION,
        resource_dest='model',
        **kwargs)


def GetDescriptionFlag(noun):
  return base.Argument(
      '--description',
      required=False,
      default=None,
      help='Description of the {noun}.'.format(noun=noun))

# Run flags
DISTRIBUTED = base.Argument(
    '--distributed',
    action='store_true',
    default=False,
    help=('Runs the provided code in distributed mode by providing cluster '
          'configurations as environment variables to subprocesses'))
PARAM_SERVERS = base.Argument(
    '--parameter-server-count',
    type=int,
    help=('Number of parameter servers with which to run. '
          'Ignored if --distributed is not specified. Default: 2'))
WORKERS = base.Argument(
    '--worker-count',
    type=int,
    help=('Number of workers with which to run. '
          'Ignored if --distributed is not specified. Default: 2'))
EVALUATORS = base.Argument(
    '--evaluator-count',
    type=int,
    help=('Number of evaluators with which to run. '
          'Ignored if --distributed is not specified. Default: 0'))
START_PORT = base.Argument(
    '--start-port',
    type=int,
    default=27182,
    help="""\
Start of the range of ports reserved by the local cluster. This command will use
a contiguous block of ports equal to parameter-server-count + worker-count + 1.

If --distributed is not specified, this flag is ignored.
""")


OPERATION_NAME = base.Argument('operation', help='Name of the operation.')


CONFIG = base.Argument(
    '--config',
    help="""\
Path to the job configuration file. This file should be a YAML document (JSON
also accepted) containing a Job resource as defined in the API (all fields are
optional): https://cloud.google.com/ml/reference/rest/v1/projects.jobs

EXAMPLES:\n
JSON:

  {
    "jobId": "my_job",
    "labels": {
      "type": "prod",
      "owner": "alice"
    },
    "trainingInput": {
      "scaleTier": "BASIC",
      "packageUris": [
        "gs://my/package/path"
      ],
      "region": "us-east1"
    }
  }

YAML:

  jobId: my_job
  labels:
    type: prod
    owner: alice
  trainingInput:
    scaleTier: BASIC
    packageUris:
    - gs://my/package/path
    region: us-east1



If an option is specified both in the configuration file **and** via command line
arguments, the command line arguments override the configuration file.
""")
JOB_NAME = base.Argument('job', help='Name of the job.')
PACKAGE_PATH = base.Argument(
    '--package-path',
    help="""\
Path to a Python package to build. This should point to a *local* directory
containing the Python source for the job. It will be built using *setuptools*
(which must be installed) using its *parent* directory as context. If the parent
directory contains a `setup.py` file, the build will use that; otherwise,
it will use a simple built-in one.
""")
PACKAGES = base.Argument(
    '--packages',
    default=[],
    type=arg_parsers.ArgList(),
    metavar='PACKAGE',
    help="""\
Path to Python archives used for training. These can be local paths
(absolute or relative), in which case they will be uploaded to the Cloud
Storage bucket given by `--staging-bucket`, or Cloud Storage URLs
('gs://bucket-name/path/to/package.tar.gz').
""")

_REGION_FLAG_HELPTEXT = """\
Google Cloud region of the regional endpoint to use for this command.
If unspecified, the command uses the global endpoint of the AI Platform Training
and Prediction API.

Learn more about regional endpoints and see a list of available regions:
 https://cloud.google.com/ai-platform/prediction/docs/regional-endpoints
"""

_REGION_FLAG_WITH_GLOBAL_HELPTEXT = """\
Google Cloud region of the regional endpoint to use for this command.
For the global endpoint, the region needs to be specified as `global`.

Learn more about regional endpoints and see a list of available regions:
 https://cloud.google.com/ai-platform/prediction/docs/regional-endpoints
"""


def GetRegionArg(include_global=False):
  """Adds --region flag to determine endpoint for models and versions."""
  if include_global:
    return base.Argument(
        '--region',
        choices=constants.SUPPORTED_REGIONS_WITH_GLOBAL,
        help=_REGION_FLAG_WITH_GLOBAL_HELPTEXT)
  return base.Argument(
      '--region',
      choices=constants.SUPPORTED_REGIONS,
      help=_REGION_FLAG_HELPTEXT)


SERVICE_ACCOUNT = base.Argument(
    '--service-account',
    required=False,
    help='Specifies the service account for resource access control.')

NETWORK = base.Argument(
    '--network',
    help="""\
Full name of the Google Compute Engine
network (https://cloud.google.com/vpc/docs) to which the Job
is peered with. For example, ``projects/12345/global/networks/myVPC''. The
format is of the form projects/{project}/global/networks/{network}, where
{project} is a project number, as in '12345', and {network} is network name.
Private services access must already have been configured
(https://cloud.google.com/vpc/docs/configure-private-services-access)
for the network. If unspecified, the Job is not peered with any network.
""")

TRAINING_SERVICE_ACCOUNT = base.Argument(
    '--service-account',
    type=core_iam_util.GetIamAccountFormatValidator(),
    required=False,
    help=textwrap.dedent("""\
      The email address of a service account to use when running the
      training appplication. You must have the `iam.serviceAccounts.actAs`
      permission for the specified service account. In addition, the AI Platform
      Training Google-managed service account must have the
      `roles/iam.serviceAccountAdmin` role for the specified service account.
      [Learn more about configuring a service
      account.](https://cloud.google.com/ai-platform/training/docs/custom-service-account)
      If not specified, the AI Platform Training Google-managed service account
      is used by default.
      """))

ENABLE_WEB_ACCESS = base.Argument(
    '--enable-web-access',
    action='store_true',
    required=False,
    default=False,
    help=textwrap.dedent("""\
      Whether you want AI Platform Training to enable [interactive shell
      access]
      (https://cloud.google.com/ai-platform/training/docs/monitor-debug-interactive-shell)
      to training containers. If set to `true`, you can access interactive
      shells at the URIs given by TrainingOutput.web_access_uris or
      HyperparameterOutput.web_access_uris (within TrainingOutput.trials).
      """))


def GetModuleNameFlag(required=True):
  return base.Argument(
      '--module-name', required=required, help='Name of the module to run.')


def GetJobDirFlag(upload_help=True, allow_local=False):
  """Get base.Argument() for `--job-dir`.

  If allow_local is provided, this Argument gives a str when parsed; otherwise,
  it gives a (possibly empty) ObjectReference.

  Args:
    upload_help: bool, whether to include help text related to object upload.
      Only useful in remote situations (`jobs submit training`).
    allow_local: bool, whether to allow local directories (only useful in local
      situations, like `local train`) or restrict input to directories in Cloud
      Storage.

  Returns:
    base.Argument() for the corresponding `--job-dir` flag.
  """
  help_ = """\
{dir_type} in which to store training outputs and other data
needed for training.

This path will be passed to your TensorFlow program as the `--job-dir` command-line
arg. The benefit of specifying this field is that AI Platform will validate
the path for use in training. However, note that your training program will need
to parse the provided `--job-dir` argument.
""".format(
    dir_type=('Cloud Storage path' +
              (' or local_directory' if allow_local else '')))
  if upload_help:
    help_ += """\

If packages must be uploaded and `--staging-bucket` is not provided, this path
will be used instead.
"""

  if allow_local:
    type_ = str
  else:
    type_ = functools.partial(storage_util.ObjectReference.FromArgument,
                              allow_empty_object=True)
  return base.Argument('--job-dir', type=type_, help=help_)


def GetUserArgs(local=False):
  if local:
    help_text = """\
Additional user arguments to be forwarded to user code. Any relative paths will
be relative to the *parent* directory of `--package-path`.
"""
  else:
    help_text = 'Additional user arguments to be forwarded to user code'
  return base.Argument(
      'user_args',
      nargs=argparse.REMAINDER,
      help=help_text)


VERSION_NAME = base.Argument('version', help='Name of the model version.')

RUNTIME_VERSION = base.Argument(
    '--runtime-version',
    help=(
        'AI Platform runtime version for this job. Must be specified unless '
        '--master-image-uri is specified instead. It is defined in '
        'documentation along with the list of supported versions: '
        'https://cloud.google.com/ai-platform/prediction/docs/runtime-version-list'  # pylint: disable=line-too-long
    ))


POLLING_INTERVAL = base.Argument(
    '--polling-interval',
    type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
    required=False,
    default=60,
    action=actions.StoreProperty(properties.VALUES.ml_engine.polling_interval),
    help='Number of seconds to wait between efforts to fetch the latest '
    'log messages.')
ALLOW_MULTILINE_LOGS = base.Argument(
    '--allow-multiline-logs',
    action='store_true',
    help='Output multiline log messages as single records.')
TASK_NAME = base.Argument(
    '--task-name',
    required=False,
    default=None,
    help='If set, display only the logs for this particular task.')


_FRAMEWORK_CHOICES = {
    'TENSORFLOW': 'tensorflow',
    'SCIKIT_LEARN': 'scikit-learn',
    'XGBOOST': 'xgboost'
}
FRAMEWORK_MAPPER = arg_utils.ChoiceEnumMapper(
    '--framework',
    (versions_api.GetMessagesModule().
     GoogleCloudMlV1Version.FrameworkValueValuesEnum),
    custom_mappings=_FRAMEWORK_CHOICES,
    help_str=('ML framework used to train this version of the model. '
              'If not specified, defaults to \'tensorflow\''))


def AddKmsKeyFlag(parser, resource):
  permission_info = '{} must hold permission {}'.format(
      "The 'AI Platform Service Agent' service account",
      "'Cloud KMS CryptoKey Encrypter/Decrypter'")
  kms_resource_args.AddKmsKeyResourceArg(
      parser, resource, permission_info=permission_info)


def AddPythonVersionFlag(parser, context):
  help_str = """\
      Version of Python used {context}. Choices are 3.7, 3.5, and 2.7.
      However, this value must be compatible with the chosen runtime version
      for the job.

      Must be used with a compatible runtime version:

      * 3.7 is compatible with runtime versions 1.15 and later.
      * 3.5 is compatible with runtime versions 1.4 through 1.14.
      * 2.7 is compatible with runtime versions 1.15 and earlier.
      """.format(context=context)
  version = base.Argument(
      '--python-version',
      help=help_str)
  version.AddToParser(parser)


def GetModelName(positional=True, required=False):
  help_text = 'Name of the model.'
  if positional:
    return base.Argument('model', help=help_text)
  else:
    return base.Argument('--model', help=help_text, required=required)


def ProcessPackages(args):
  """Flatten PACKAGES flag and warn if multiple arguments were used."""
  if args.packages is not None:
    if len(args.packages) > 1:
      log.warning('Use of --packages with space separated values is '
                  'deprecated and will not work in the future. Use comma '
                  'instead.')
    # flatten packages into a single list
    args.packages = list(itertools.chain.from_iterable(args.packages))


STAGING_BUCKET = base.Argument(
    '--staging-bucket',
    type=storage_util.BucketReference.FromArgument,
    help="""\
        Bucket in which to stage training archives.

        Required only if a file upload is necessary (that is, other flags
        include local paths) and no other flags implicitly specify an upload
        path.
        """)

SIGNATURE_NAME = base.Argument(
    '--signature-name',
    required=False,
    type=str,
    help="""\
    Name of the signature defined in the SavedModel to use for
    this job. Defaults to DEFAULT_SERVING_SIGNATURE_DEF_KEY in
    https://www.tensorflow.org/api_docs/python/tf/compat/v1/saved_model/signature_constants,
    which is "serving_default". Only applies to TensorFlow models.
    """)


def GetSummarizeFlag():
  return base.Argument(
      '--summarize',
      action='store_true',
      required=False,
      help="""\
      Summarize job output in a set of human readable tables instead of
      rendering the entire resource as json or yaml. The tables currently rendered
      are:

      * `Job Overview`: Overview of job including, jobId, status and create time.
      * `Training Input Summary`: Summary of input for a training job including
         region, main training python module and scale tier.
      * `Training Output Summary`: Summary of output for a training job including
         the amount of ML units consumed by the job.
      * `Training Output Trials`: Summary of hyperparameter trials run for a
         hyperparameter tuning training job.
      * `Predict Input Summary`: Summary of input for a prediction job including
         region, model verion and output path.
      * `Predict Output Summary`: Summary of output for a prediction job including
         prediction count and output path.

      This flag overrides the `--format` flag. If
      both are present on the command line, a warning is displayed.
      """)


def GetStandardTrainingJobSummary():
  """Get tabular format for standard ml training job."""
  return _JOB_SUMMARY.format(
      INPUT=_JOB_TRAIN_INPUT_SUMMARY_FORMAT,
      OUTPUT=_JOB_TRAIN_OUTPUT_SUMMARY_FORMAT.format(HP_OUTPUT=''))


def GetHPTrainingJobSummary():
  """Get tablular format to HyperParameter tuning ml job."""
  return _JOB_SUMMARY.format(
      INPUT=_JOB_PREDICT_INPUT_SUMMARY_FORMAT,
      OUTPUT=_JOB_TRAIN_OUTPUT_SUMMARY_FORMAT.format(
          HP_OUTPUT=_JOB_TRAIN_OUTPUT_TRIALS_FORMAT))


def GetPredictJobSummary():
  """Get table format for ml prediction job."""
  return _JOB_SUMMARY.format(
      INPUT=_JOB_PREDICT_INPUT_SUMMARY_FORMAT,
      OUTPUT=_JOB_PREDICT_OUTPUT_SUMMARY_FORMAT)


def ModelAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='model',
      help_text='Model for the {resource}.')


def VersionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='version',
      help_text='Version for the {resource}.')


def GetVersionResourceSpec():
  return concepts.ResourceSpec(
      'ml.projects.models.versions',
      resource_name='version',
      versionsId=VersionAttributeConfig(),
      modelsId=ModelAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddVersionResourceArg(parser, verb):
  """Add a resource argument for an AI Platform version."""
  concept_parsers.ConceptParser.ForResource(
      'version',
      GetVersionResourceSpec(),
      'The AI Platform model {}.'.format(verb),
      required=True).AddToParser(parser)


def GetModelResourceSpec(resource_name='model'):
  return concepts.ResourceSpec(
      'ml.projects.models',
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True)


def GetModelResourceArg(positional=True, required=False, verb=''):
  """Add a resource argument for AI Platform model.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    positional: bool, if True, means that the model is a positional rather
    required: bool, if True means that argument is required.
    verb: str, the verb to describe the resource, such as 'to update'.

  Returns:
    An argparse.ArgumentParse object.
  """
  if positional:
    name = 'model'
  else:
    name = '--model'
  return concept_parsers.ConceptParser.ForResource(
      name,
      GetModelResourceSpec(),
      'The AI Platform model {}.'.format(verb),
      required=required)


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'ml.projects.locations',
      resource_name='location',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=True)


def GetLocationResourceArg():
  """Add a resource argument for AI Platform location.

  Returns:
    An argparse.ArgumentParse object.
  """
  return concept_parsers.ConceptParser.ForResource(
      'location',
      GetLocationResourceSpec(),
      'The location you want to show details for.',
      required=True)


def AddUserCodeArgs(parser):
  """Add args that configure user prediction code."""
  user_code_group = base.ArgumentGroup(help="""\
          Configure user code in prediction.

          AI Platform allows a model to have user-provided prediction
          code; these options configure that code.
          """)
  user_code_group.AddArgument(base.Argument(
      '--prediction-class',
      help="""\
          Fully-qualified name of the custom prediction class in the package
          provided for custom prediction.

          For example, `--prediction-class=my_package.SequenceModel`.
          """))
  user_code_group.AddArgument(base.Argument(
      '--package-uris',
      type=arg_parsers.ArgList(),
      metavar='PACKAGE_URI',
      help="""\
          Comma-separated list of Cloud Storage URIs ('gs://...') for
          user-supplied Python packages to use.
          """))
  user_code_group.AddToParser(parser)


def GetAcceleratorFlag():
  return base.Argument(
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
 If not specified, the default value is 1. Your model must be specially designed
to accommodate more than 1 accelerator per machine. To configure how many
replicas your model has, set the `manualScaling` or `autoScaling`
parameters.""".format(', '.join(
    ["'{}'".format(c) for c in _OP_ACCELERATOR_TYPE_MAPPER.choices])))


def ParseAcceleratorFlag(accelerator):
  """Validates and returns a accelerator config message object."""
  types = [c for c in _ACCELERATOR_TYPE_MAPPER.choices]
  if accelerator is None:
    return None
  raw_type = accelerator.get('type', None)
  if raw_type not in types:
    raise ArgumentError("""\
The type of the accelerator can only be one of the following: {}.
""".format(', '.join(["'{}'".format(c) for c in types])))
  accelerator_count = accelerator.get('count', 1)
  if accelerator_count <= 0:
    raise ArgumentError("""\
The count of the accelerator must be greater than 0.
""")
  accelerator_msg = (versions_api.GetMessagesModule().
                     GoogleCloudMlV1AcceleratorConfig)
  accelerator_type = arg_utils.ChoiceToEnum(
      raw_type, accelerator_msg.TypeValueValuesEnum)
  return accelerator_msg(
      count=accelerator_count,
      type=accelerator_type)


def AddExplainabilityFlags(parser):
  """Add args that configure explainability."""
  base.ChoiceArgument(
      '--explanation-method',
      choices=['integrated-gradients', 'sampled-shapley', 'xrai'],
      required=False,
      help_str="""\
          Enable explanations and select the explanation method to use.

          The valid options are:
            integrated-gradients: Use Integrated Gradients.
            sampled-shapley: Use Sampled Shapley.
            xrai: Use XRAI.
      """
  ).AddToParser(parser)
  base.Argument(
      '--num-integral-steps',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      default=50,
      required=False,
      help="""\
          Number of integral steps for Integrated Gradients. Only valid when
          `--explanation-method=integrated-gradients` or
          `--explanation-method=xrai` is specified.
      """
  ).AddToParser(parser)
  base.Argument(
      '--num-paths',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      default=50,
      required=False,
      help="""\
          Number of paths for Sampled Shapley. Only valid when
          `--explanation-method=sampled-shapley` is specified.
      """
  ).AddToParser(parser)


def AddCustomContainerFlags(parser, support_tpu_tf_version=False):
  """Add Custom container flags to parser."""
  GetMasterMachineType().AddToParser(parser)
  GetMasterAccelerator().AddToParser(parser)
  GetMasterImageUri().AddToParser(parser)
  GetParameterServerMachineTypeConfig().AddToParser(parser)
  GetParameterServerAccelerator().AddToParser(parser)
  GetParameterServerImageUri().AddToParser(parser)
  GetWorkerMachineConfig().AddToParser(parser)
  GetWorkerAccelerator().AddToParser(parser)
  GetWorkerImageUri().AddToParser(parser)
  GetUseChiefInTfConfig().AddToParser(parser)
  if support_tpu_tf_version:
    GetTpuTfVersion().AddToParser(parser)

# Custom Container Flags
_ACCELERATOR_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    'generic-accelerator',
    jobs.GetMessagesModule(
    ).GoogleCloudMlV1AcceleratorConfig.TypeValueValuesEnum,
    help_str='Available types of accelerators.',
    include_filter=lambda x: x != 'ACCELERATOR_TYPE_UNSPECIFIED',
    required=False)

_OP_ACCELERATOR_TYPE_MAPPER = arg_utils.ChoiceEnumMapper(
    'generic-accelerator',
    jobs.GetMessagesModule().GoogleCloudMlV1AcceleratorConfig
    .TypeValueValuesEnum,
    help_str='Available types of accelerators.',
    include_filter=lambda x: x.startswith('NVIDIA'),
    required=False)

_OP_AUTOSCALING_METRIC_NAME_MAPPER = arg_utils.ChoiceEnumMapper(
    'autoscaling-metric-name',
    versions_api.GetMessagesModule().GoogleCloudMlV1MetricSpec
    .NameValueValuesEnum,
    help_str='The available metric names.',
    include_filter=lambda x: x != 'METRIC_NAME_UNSPECIFIED',
    required=False)

_ACCELERATOR_TYPE_HELP = """\
   Hardware accelerator config for the {worker_type}. Must specify
   both the accelerator type (TYPE) for each server and the number of
   accelerators to attach to each server (COUNT).
  """


def _ConvertAcceleratorTypeToEnumValue(choice_str):
  return arg_utils.ChoiceToEnum(choice_str, _ACCELERATOR_TYPE_MAPPER.enum,
                                item_type='accelerator',
                                valid_choices=_ACCELERATOR_TYPE_MAPPER.choices)


def _ValidateAcceleratorCount(accelerator_count):
  count = int(accelerator_count)
  if count <= 0:
    raise arg_parsers.ArgumentTypeError(
        'The count of the accelerator must be greater than 0.')
  return count


def _ValidateMetricTargetKey(key):
  """Value validation for Metric target name."""
  names = list(_OP_AUTOSCALING_METRIC_NAME_MAPPER.choices)
  if key not in names:
    raise ArgumentError("""\
The autoscaling metric name can only be one of the following: {}.
""".format(', '.join(["'{}'".format(c) for c in names])))
  return key


def _ValidateMetricTargetValue(value):
  """Value validation for Metric target value."""
  try:
    result = int(value)
  except (TypeError, ValueError):
    raise ArgumentError('Metric target percentage value %s is not an integer.' %
                        value)

  if result < 0 or result > 100:
    raise ArgumentError(
        'Metric target value %s is not between 0 and 100.' % value)
  return result


def _MakeAcceleratorArgConfigArg(arg_name, arg_help, required=False):
  """Creates an ArgDict representing an AcceleratorConfig message."""
  type_help = '*type*::: Type of the accelerator. Choices are {}'.format(
      ','.join(_ACCELERATOR_TYPE_MAPPER.choices))
  count_help = ('*count*::: Number of accelerators to attach to each '
                'machine running the job. Must be greater than 0.')
  arg = base.Argument(
      arg_name,
      required=required,
      type=arg_parsers.ArgDict(spec={
          'type': _ConvertAcceleratorTypeToEnumValue,
          'count': _ValidateAcceleratorCount,
      }, required_keys=['type', 'count']),
      help="""\
{arg_help}

{type_help}

{count_help}

""".format(arg_help=arg_help, type_help=type_help, count_help=count_help))
  return arg


def GetMasterMachineType():
  """Build master-machine-type flag."""
  help_text = """\
  Specifies the type of virtual machine to use for training job's master worker.

  You must set this value when `--scale-tier` is set to `CUSTOM`.
  """
  return base.Argument(
      '--master-machine-type', required=False, help=help_text)


def GetMasterAccelerator():
  """Build master-accelerator flag."""
  help_text = _ACCELERATOR_TYPE_HELP.format(worker_type='master worker')
  return _MakeAcceleratorArgConfigArg(
      '--master-accelerator', arg_help=help_text)


def GetMasterImageUri():
  """Build master-image-uri flag."""
  return base.Argument(
      '--master-image-uri',
      required=False,
      help=('Docker image to run on each master worker. '
            'This image must be in Container Registry. Only one of '
            '`--master-image-uri` and `--runtime-version` must be specified.'))


def GetParameterServerMachineTypeConfig():
  """Build parameter-server machine type config group."""
  machine_type = base.Argument(
      '--parameter-server-machine-type',
      required=True,
      help=('Type of virtual machine to use for training job\'s '
            'parameter servers. This flag must be specified if any of the '
            'other arguments in this group are specified machine to use for '
            'training job\'s parameter servers.'))

  machine_count = base.Argument(
      '--parameter-server-count',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      required=True,
      help=('Number of parameter servers to use for the training job.'))

  machine_type_group = base.ArgumentGroup(
      required=False,
      help='Configure parameter server machine type settings.')
  machine_type_group.AddArgument(machine_type)
  machine_type_group.AddArgument(machine_count)
  return machine_type_group


def GetParameterServerAccelerator():
  """Build parameter-server-accelerator flag."""
  help_text = _ACCELERATOR_TYPE_HELP.format(worker_type='parameter servers')
  return _MakeAcceleratorArgConfigArg(
      '--parameter-server-accelerator', arg_help=help_text)


def GetParameterServerImageUri():
  """Build parameter-server-image-uri flag."""
  return base.Argument(
      '--parameter-server-image-uri',
      required=False,
      help=('Docker image to run on each parameter server. '
            'This image must be in Container Registry. If not '
            'specified, the value of `--master-image-uri` is used.'))


def GetWorkerMachineConfig():
  """Build worker machine type config group."""
  machine_type = base.Argument(
      '--worker-machine-type',
      required=True,
      help=('Type of virtual '
            'machine to use for training '
            'job\'s worker nodes.'))

  machine_count = base.Argument(
      '--worker-count',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      required=True,
      help='Number of worker nodes to use for the training job.')

  machine_type_group = base.ArgumentGroup(
      required=False,
      help='Configure worker node machine type settings.')
  machine_type_group.AddArgument(machine_type)
  machine_type_group.AddArgument(machine_count)
  return machine_type_group


def GetWorkerAccelerator():
  """Build worker-accelerator flag."""
  help_text = _ACCELERATOR_TYPE_HELP.format(worker_type='worker nodes')
  return _MakeAcceleratorArgConfigArg(
      '--worker-accelerator', arg_help=help_text)


def GetWorkerImageUri():
  """Build worker-image-uri flag."""
  return base.Argument(
      '--worker-image-uri',
      required=False,
      help=('Docker image to run on each worker node. '
            'This image must be in Container Registry. If not '
            'specified, the value of `--master-image-uri` is used.'))


def GetTpuTfVersion():
  """Build tpu-tf-version flag."""
  return base.Argument(
      '--tpu-tf-version',
      required=False,
      help=('Runtime version of TensorFlow used by the container. This field '
            'must be specified if a custom container on the TPU worker is '
            'being used.'))


def GetUseChiefInTfConfig():
  """Build use-chief-in-tf-config flag."""
  return base.Argument(
      '--use-chief-in-tf-config',
      required=False,
      type=arg_parsers.ArgBoolean(),
      help=('Use "chief" role in the cluster instead of "master". This is '
            'required for TensorFlow 2.0 and newer versions. Unlike "master" '
            'node, "chief" node does not run evaluation.'))


def AddMachineTypeFlagToParser(parser):
  base.Argument(
      '--machine-type',
      help="""\
Type of machine on which to serve the model. Currently only applies to online prediction. For available machine types,
see https://cloud.google.com/ai-platform/prediction/docs/machine-types-online-prediction#available_machine_types.
""").AddToParser(parser)


def AddContainerFlags(parser):
  """Adds flags related to custom containers to the specified parser."""
  container_group = parser.add_argument_group(
      help='Configure the container to be deployed.')
  container_group.add_argument(
      '--image',
      help="""\
Name of the container image to deploy (e.g. gcr.io/myproject/server:latest).
""")
  container_group.add_argument(
      '--command',
      type=arg_parsers.ArgList(),
      metavar='COMMAND',
      action=arg_parsers.UpdateAction,
      help="""\
Entrypoint for the container image. If not specified, the container
image's default Entrypoint is run.
""")
  container_group.add_argument(
      '--args',
      metavar='ARG',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help="""\
Comma-separated arguments passed to the command run by the container
image. If not specified and no '--command' is provided, the container
image's default Cmd is used.
""")
  container_group.add_argument(
      '--env-vars',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help='List of key-value pairs to set as environment variables.'
  )
  container_group.add_argument(
      '--ports',
      metavar='ARG',
      type=arg_parsers.ArgList(element_type=arg_parsers.BoundedInt(1, 65535)),
      action=arg_parsers.UpdateAction,
      help="""\
Container ports to receive requests at. Must be a number between 1 and 65535,
inclusive.
""")
  route_group = parser.add_argument_group(
      help='Flags to control the paths that requests and health checks are '
      'sent to.')
  route_group.add_argument(
      '--predict-route',
      help='HTTP path to send prediction requests to inside the container.'
  )
  route_group.add_argument(
      '--health-route',
      help='HTTP path to send health checks to inside the container.'
  )


def AddAutoScalingFlags(parser):
  """Adds flags related to autoscaling to the specified parser."""
  autoscaling_group = parser.add_argument_group(
      help='Configure the autoscaling settings to be deployed.')
  autoscaling_group.add_argument(
      '--min-nodes',
      type=int,
      help="""\
The minimum number of nodes to scale this model under load.
""")
  autoscaling_group.add_argument(
      '--max-nodes',
      type=int,
      help="""\
The maximum number of nodes to scale this model under load.
""")
  autoscaling_group.add_argument(
      '--metric-targets',
      metavar='METRIC-NAME=TARGET',
      type=arg_parsers.ArgDict(
          key_type=_ValidateMetricTargetKey, value_type=_ValidateMetricTargetValue),
      action=arg_parsers.UpdateAction,
      default={},
      help="""\
List of key-value pairs to set as metrics' target for autoscaling.
Autoscaling could be based on CPU usage or GPU duty cycle, valid key could be
cpu-usage or gpu-duty-cycle.
""")


def AddRequestLoggingConfigFlags(parser):
  """Adds flags related to request response logging."""
  group = parser.add_argument_group(
      help='Configure request response logging.')
  group.add_argument(
      '--bigquery-table-name',
      type=str,
      help="""\
Fully qualified name (project_id.dataset_name.table_name) of the BigQuery
table where requests and responses are logged.
""")
  group.add_argument(
      '--sampling-percentage',
      type=float,
      help="""\
Percentage of requests to be logged, expressed as a number between 0 and 1.
For example, set this value to 1 in order to log all requests or to 0.1 to log
10% of requests.
""")
