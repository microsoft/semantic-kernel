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
"""Flags definition specifically for gcloud ai custom-jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import flags as shared_flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.command_lib.ai.custom_jobs import custom_jobs_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

_DISPLAY_NAME = base.Argument(
    '--display-name',
    required=True,
    help=('Display name of the custom job to create.'))

_PYTHON_PACKAGE_URIS = base.Argument(
    '--python-package-uris',
    metavar='PYTHON_PACKAGE_URIS',
    type=arg_parsers.ArgList(),
    help=('The common Python package URIs to be used for training with a '
          'pre-built container image. e.g. `--python-package-uri=path1,path2` '
          'If you are using multiple worker pools and want to specify a '
          'different Python packag fo reach pool, use `--config` instead.'))

_CUSTOM_JOB_CONFIG = base.Argument(
    '--config',
    help=textwrap.dedent("""\
      Path to the job configuration file. This file should be a YAML document
      containing a [`CustomJobSpec`](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/CustomJobSpec).
      If an option is specified both in the configuration file **and** via command-line arguments, the command-line arguments
      override the configuration file. Note that keys with underscore are invalid.

      Example(YAML):

        workerPoolSpecs:
          machineSpec:
            machineType: n1-highmem-2
          replicaCount: 1
          containerSpec:
            imageUri: gcr.io/ucaip-test/ucaip-training-test
            args:
            - port=8500
            command:
            - start"""))

_WORKER_POOL_SPEC = base.Argument(
    '--worker-pool-spec',
    action='append',
    type=arg_parsers.ArgDict(
        spec={
            'replica-count': int,
            'machine-type': str,
            'accelerator-type': str,
            'accelerator-count': int,
            'container-image-uri': str,
            'executor-image-uri': str,
            'output-image-uri': str,
            'python-module': str,
            'script': str,
            'local-package-path': str,
            'requirements': arg_parsers.ArgList(custom_delim_char=';'),
            'extra-dirs': arg_parsers.ArgList(custom_delim_char=';'),
            'extra-packages': arg_parsers.ArgList(custom_delim_char=';'),
        }),
    metavar='WORKER_POOL_SPEC',
    help=textwrap.dedent("""\
      Define the worker pool configuration used by the custom job. You can
      specify multiple worker pool specs in order to create a custom job with
      multiple worker pools.

      The spec can contain the following fields:

      *machine-type*::: (Required): The type of the machine.
        see https://cloud.google.com/vertex-ai/docs/training/configure-compute#machine-types
        for supported types. This is corresponding to the `machineSpec.machineType`
        field in `WorkerPoolSpec` API message.
      *replica-count*::: The number of worker replicas to use for this worker
        pool, by default the value is 1. This is corresponding to the `replicaCount`
        field in `WorkerPoolSpec` API message.
      *accelerator-type*::: The type of GPUs.
        see https://cloud.google.com/vertex-ai/docs/training/configure-compute#specifying_gpus
        for more requirements. This is corresponding to the `machineSpec.acceleratorType`
        field in `WorkerPoolSpec` API message.
      *accelerator-count*::: The number of GPUs for each VM in the worker pool to
        use, by default the value if 1. This is corresponding to the
        `machineSpec.acceleratorCount` field in `WorkerPoolSpec` API message.
      *container-image-uri*::: The URI of a container image to be directly run on
        each worker replica. This is corresponding to the
        `containerSpec.imageUri` field in `WorkerPoolSpec` API message.
      *executor-image-uri*::: The URI of a container image that will run the
        provided package.
      *output-image-uri*::: The URI of a custom container image to be built for
      autopackaged custom jobs.
      *python-module*::: The Python module name to run within the provided
        package.
      *local-package-path*::: The local path of a folder that contains training
        code.
      *script*::: The relative path under the `local-package-path` to a file to
        execute. It can be a Python file or an arbitrary bash script.
      *requirements*::: Python dependencies to be installed from PyPI, separated
        by ";". This is supposed to be used when some public packages are
        required by your training application but not in the base images.
        It has the same effect as editing a "requirements.txt" file under
        `local-package-path`.
      *extra-packages*::: Relative paths of local Python archives to be installed,
        separated by ";". This is supposed to be used when some custom packages
        are required by your training application but not in the base images.
        Every path should be relative to the `local-package-path`.
      *extra-dirs*::: Relative paths of the folders under `local-package-path`
       to be copied into the container, separated by ";". If not specified, only
       the parent directory that contains the main executable (`script` or
       `python-module`) will be copied.


      ::::
      Note that some of these fields are used for different job creation methods
      and are categorized as mutually exclusive groups listed below. Exactly one of
      these groups of fields must be specified:


      `container-image-uri`::::
      Specify this field to use a custom container image for training. Together
      with the `--command` and `--args` flags, this field represents a
      [`WorkerPoolSpec.ContainerSpec`](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/CustomJobSpec?#containerspec)
      message.
      In this case, the `--python-package-uris` flag is disallowed.

      Example:
      --worker-pool-spec=replica-count=1,machine-type=n1-highmem-2,container-image-uri=gcr.io/ucaip-test/ucaip-training-test

      `executor-image-uri, python-module`::::
      Specify these fields to train using a pre-built container and Python
      packages that are already in Cloud Storage. Together with the
      `--python-package-uris` and `--args` flags, these fields represent a
      [`WorkerPoolSpec.PythonPackageSpec`](https://cloud.google.com/vertex-ai/docs/reference/rest/v1/CustomJobSpec#pythonpackagespec)
      message .

      Example:
      --worker-pool-spec=machine-type=e2-standard-4,executor-image-uri=us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-4:latest,python-module=trainer.task

      `output-image-uri`::::
      Specify this field to push the output custom container training image to a specific path in Container Registry or Artifact Registry for an autopackaged custom job.

      Example:
      --worker-pool-spec=machine-type=e2-standard-4,executor-image-uri=us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-4:latest,output-image-uri='eu.gcr.io/projectName/imageName',python-module=trainer.task

      `local-package-path, executor-image-uri, output-image-uri, python-module|script`::::
      Specify these fields, optionally with `requirements`, `extra-packages`, or
      `extra-dirs`, to train using a pre-built container and Python code from a
      local path.
      In this case, the `--python-package-uris` flag is disallowed.

      Example using `python-module`:
      --worker-pool-spec=machine-type=e2-standard-4,replica-count=1,executor-image-uri=us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-4:latest,python-module=trainer.task,local-package-path=/usr/page/application

      Example using `script`:
      --worker-pool-spec=machine-type=e2-standard-4,replica-count=1,executor-image-uri=us-docker.pkg.dev/vertex-ai/training/tf-cpu.2-4:latest,script=my_run.sh,local-package-path=/usr/jeff/application
      """))

_CUSTOM_JOB_COMMAND = base.Argument(
    '--command',
    type=arg_parsers.ArgList(),
    metavar='COMMAND',
    action=arg_parsers.UpdateAction,
    help="""\
    Command to be invoked when containers are started.
    It overrides the entrypoint instruction in Dockerfile when provided.
    """)
_CUSTOM_JOB_ARGS = base.Argument(
    '--args',
    metavar='ARG',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help='Comma-separated arguments passed to containers or python tasks.')

_PERSISTENT_RESOURCE_ID = base.Argument(
    '--persistent-resource-id',
    metavar='PERSISTENT_RESOURCE_ID',
    hidden=True,
    help="""\
    The name of the persistent resource from the same project and region on
    which to run this custom job.

    If this is specified, the job will be run on existing machines held by the
    PersistentResource instead of on-demand short-live machines.
    The network and CMEK configs on the job should be consistent with those on
    the PersistentResource, otherwise, the job will be rejected.
    """)


def AddCreateCustomJobFlags(parser, version):
  """Adds flags related to create a custom job."""
  shared_flags.AddRegionResourceArg(
      parser,
      'to create a custom job',
      prompt_func=region_util.GetPromptForRegionFunc(
          constants.SUPPORTED_TRAINING_REGIONS))
  shared_flags.TRAINING_SERVICE_ACCOUNT.AddToParser(parser)
  shared_flags.NETWORK.AddToParser(parser)
  shared_flags.ENABLE_WEB_ACCESS.AddToParser(parser)
  shared_flags.ENABLE_DASHBOARD_ACCESS.AddToParser(parser)
  shared_flags.AddKmsKeyResourceArg(parser, 'custom job')

  labels_util.AddCreateLabelsFlags(parser)

  _DISPLAY_NAME.AddToParser(parser)
  _PYTHON_PACKAGE_URIS.AddToParser(parser)
  _CUSTOM_JOB_ARGS.AddToParser(parser)
  _CUSTOM_JOB_COMMAND.AddToParser(parser)

  if version == constants.BETA_VERSION:
    _PERSISTENT_RESOURCE_ID.AddToParser(parser)

  worker_pool_spec_group = base.ArgumentGroup(
      help='Worker pool specification.', required=True)
  worker_pool_spec_group.AddArgument(_CUSTOM_JOB_CONFIG)
  worker_pool_spec_group.AddArgument(_WORKER_POOL_SPEC)
  worker_pool_spec_group.AddToParser(parser)


def AddCustomJobResourceArg(parser,
                            verb,
                            regions=constants.SUPPORTED_TRAINING_REGIONS):
  """Add a resource argument for a Vertex AI custom job.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the job resource, such as 'to update'.
    regions: list[str], the list of supported regions.
  """
  job_resource_spec = concepts.ResourceSpec(
      resource_collection=custom_jobs_util.CUSTOM_JOB_COLLECTION,
      resource_name='custom job',
      locationsId=shared_flags.RegionAttributeConfig(
          prompt_func=region_util.GetPromptForRegionFunc(regions)),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False)

  concept_parsers.ConceptParser.ForResource(
      'custom_job',
      job_resource_spec,
      'The custom job {}.'.format(verb),
      required=True).AddToParser(parser)


def AddLocalRunCustomJobFlags(parser):
  """Add local-run related flags to the parser."""

  # Flags for entry point of the training application
  application_group = parser.add_mutually_exclusive_group()
  application_group.add_argument(
      '--python-module',
      metavar='PYTHON_MODULE',
      help=textwrap.dedent("""
      Name of the python module to execute, in 'trainer.train' or 'train'
      format. Its path should be relative to the `work_dir`.
      """))
  application_group.add_argument(
      '--script',
      metavar='SCRIPT',
      help=textwrap.dedent("""
      The relative path of the file to execute. Accepets a Python file or an
      arbitrary bash script. This path should be relative to the `work_dir`.
      """))

  # Flags for working directory.
  parser.add_argument(
      '--local-package-path',
      metavar='LOCAL_PATH',
      suggestion_aliases=['--work-dir'],
      help=textwrap.dedent("""
      local path of the directory where the python-module or script exists.
      If not specified, it use the directory where you run the this command.

      Only the contents of this directory will be accessible to the built
      container image.
      """))

  # Flags for extra directory
  parser.add_argument(
      '--extra-dirs',
      metavar='EXTRA_DIR',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Extra directories under the working directory to include, besides the one
      that contains the main executable.

      By default, only the parent directory of the main script or python module
      is copied to the container.
      For example, if the module is "training.task" or the script is
      "training/task.py", the whole "training" directory, including its
      sub-directories, will always be copied to the container. You may specify
      this flag to also copy other directories if necessary.

      Note: if no parent is specified in 'python_module' or 'scirpt', the whole
      working directory is copied, then you don't need to specify this flag.
      """))

  # Flags for base container image
  parser.add_argument(
      '--executor-image-uri',
      metavar='IMAGE_URI',
      required=True,
      suggestion_aliases=['--base-image'],
      help=textwrap.dedent("""
      URI or ID of the container image in either the Container Registry or local
      that will run the application.
      See https://cloud.google.com/vertex-ai/docs/training/pre-built-containers
      for available pre-built container images provided by Vertex AI for training.
      """))

  # Flags for extra requirements.
  parser.add_argument(
      '--requirements',
      metavar='REQUIREMENTS',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Python dependencies from PyPI to be used when running the application.
      If this is not specified, and there is no "setup.py" or "requirements.txt"
      in the working directory, your application will only have access to what
      exists in the base image with on other dependencies.

      Example:
      'tensorflow-cpu, pandas==1.2.0, matplotlib>=3.0.2'
      """))

  # Flags for extra dependency .
  parser.add_argument(
      '--extra-packages',
      metavar='PACKAGE',
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Local paths to Python archives used as training dependencies in the image
      container.
      These can be absolute or relative paths. However, they have to be under
      the work_dir; Otherwise, this tool will not be able to access it.

      Example:
      'dep1.tar.gz, ./downloads/dep2.whl'
      """))

  # Flags for the output image
  parser.add_argument(
      '--output-image-uri',
      metavar='OUTPUT_IMAGE',
      help=textwrap.dedent("""
      Uri of the custom container image to be built with the your application
      packed in.
      """))

  # Flaga for GPU support
  parser.add_argument(
      '--gpu', action='store_true', default=False, help='Enable to use GPU.')

  # Flags for docker run
  parser.add_argument(
      '--docker-run-options',
      metavar='DOCKER_RUN_OPTIONS',
      hidden=True,
      type=arg_parsers.ArgList(),
      help=textwrap.dedent("""
      Custom Docker run options to pass to image during execution.
      For example, '--no-healthcheck, -a stdin'.

      See https://docs.docker.com/engine/reference/commandline/run/#options for
      more details.
      """))

  # Flags for service account
  parser.add_argument(
      '--service-account-key-file',
      metavar='ACCOUNT_KEY_FILE',
      help=textwrap.dedent("""
      The JSON file of a Google Cloud service account private key.
      When specified, the corresponding service account will be used to
      authenticate the local container to access Google Cloud services.
      Note that the key file won't be copied to the container, it will be
      mounted during running time.
      """))

  # User custom flags.
  parser.add_argument(
      'args',
      nargs=argparse.REMAINDER,
      default=[],
      help="""Additional user arguments to be forwarded to your application.""",
      example=('$ {command} --script=my_run.sh --base-image=gcr.io/my/image '
               '-- --my-arg bar --enable_foo'))
