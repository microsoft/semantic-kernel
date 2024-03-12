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
"""Utilities for AI Platform custom jobs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.ai.custom_jobs import local_util
from googlecloudsdk.command_lib.ai.docker import build as docker_build
from googlecloudsdk.command_lib.ai.docker import utils as docker_utils
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

# TODO(b/191347326): Consider adding tests for the "public" methods in this file
CUSTOM_JOB_COLLECTION = 'aiplatform.projects.locations.customJobs'


def _ConstructSingleWorkerPoolSpec(aiplatform_client,
                                   spec,
                                   python_package_uri=None):
  """Constructs the specification of a single worker pool.

  Args:
    aiplatform_client: The AI Platform API client used.
    spec: A dict whose fields represent a worker pool config.
    python_package_uri: str, The common python package uris that will be used by
      executor image, supposedly derived from the gcloud command flags.

  Returns:
    A WorkerPoolSpec message instance for setting a worker pool in a custom job.
  """
  worker_pool_spec = aiplatform_client.GetMessage('WorkerPoolSpec')()

  machine_spec_msg = aiplatform_client.GetMessage('MachineSpec')
  machine_spec = machine_spec_msg(machineType=spec.get('machine-type'))
  accelerator_type = spec.get('accelerator-type')
  if accelerator_type:
    machine_spec.acceleratorType = arg_utils.ChoiceToEnum(
        accelerator_type, machine_spec_msg.AcceleratorTypeValueValuesEnum)
    machine_spec.acceleratorCount = int(spec.get('accelerator-count', 1))
  worker_pool_spec.machineSpec = machine_spec
  worker_pool_spec.replicaCount = int(spec.get('replica-count', 1))

  container_image_uri = spec.get('container-image-uri')
  executor_image_uri = spec.get('executor-image-uri')
  python_module = spec.get('python-module')

  if container_image_uri:
    container_spec_msg = aiplatform_client.GetMessage('ContainerSpec')
    worker_pool_spec.containerSpec = container_spec_msg(
        imageUri=container_image_uri)
  elif python_package_uri or executor_image_uri or python_module:
    python_package_spec_msg = aiplatform_client.GetMessage('PythonPackageSpec')
    worker_pool_spec.pythonPackageSpec = python_package_spec_msg(
        executorImageUri=executor_image_uri,
        packageUris=(python_package_uri or []),
        pythonModule=python_module)

  return worker_pool_spec


def _ConstructWorkerPoolSpecs(aiplatform_client, specs, **kwargs):
  """Constructs the specification of the worker pools in a CustomJobSpec instance.

  Args:
    aiplatform_client: The AI Platform API client used.
    specs: A list of dict of worker pool specifications, supposedly derived from
      the gcloud command flags.
    **kwargs: The keyword args to pass down to construct each worker pool spec.

  Returns:
    A list of WorkerPoolSpec message instances for creating a custom job.
  """
  worker_pool_specs = []

  for spec in specs:
    if spec:
      worker_pool_specs.append(
          _ConstructSingleWorkerPoolSpec(aiplatform_client, spec, **kwargs))
    else:
      worker_pool_specs.append(aiplatform_client.GetMessage('WorkerPoolSpec')())

  return worker_pool_specs


def _PrepareTrainingImage(project,
                          job_name,
                          base_image,
                          local_package,
                          script,
                          output_image_name,
                          python_module=None,
                          **kwargs):
  """Build a training image from local package and push it to Cloud for later usage."""
  output_image = output_image_name or docker_utils.GenerateImageName(
      base_name=job_name, project=project, is_gcr=True)

  docker_build.BuildImage(
      base_image=base_image,
      host_workdir=files.ExpandHomeDir(local_package),
      main_script=script,
      python_module=python_module,
      output_image_name=output_image,
      **kwargs)
  log.status.Print('\nA custom container image is built locally.\n')

  push_command = ['docker', 'push', output_image]
  docker_utils.ExecuteDockerCommand(push_command)
  log.status.Print(
      '\nCustom container image [{}] is created for your custom job.\n'.format(
          output_image))

  return output_image


def UpdateWorkerPoolSpecsIfLocalPackageRequired(worker_pool_specs, job_name,
                                                project):
  """Update the given worker pool specifications if any contains local packages.

  If any given worker pool spec is specified a local package, this builds
  a Docker image from the local package and update the spec to use it.

  Args:
    worker_pool_specs: list of dict representing the arg value specified via the
      `--worker-pool-spec` flag.
    job_name: str, the display name of the custom job corresponding to the
      worker pool specs.
    project: str, id of the project to which the custom job is submitted.

  Yields:
    All updated worker pool specifications that uses the already built
    packages and are expectedly passed to a custom-jobs create RPC request.
  """

  image_built_for_first_worker = None
  if worker_pool_specs and 'local-package-path' in worker_pool_specs[0]:
    base_image = worker_pool_specs[0].pop('executor-image-uri')
    local_package = worker_pool_specs[0].pop('local-package-path')

    python_module = worker_pool_specs[0].pop('python-module', None)
    if python_module:
      script = local_util.ModuleToPath(python_module)
    else:
      script = worker_pool_specs[0].pop('script')

    output_image = worker_pool_specs[0].pop('output-image-uri', None)
    image_built_for_first_worker = _PrepareTrainingImage(
        project=project,
        job_name=job_name,
        base_image=base_image,
        local_package=local_package,
        script=script,
        output_image_name=output_image,
        python_module=python_module,
        requirements=worker_pool_specs[0].pop('requirements', None),
        extra_packages=worker_pool_specs[0].pop('extra-packages', None),
        extra_dirs=worker_pool_specs[0].pop('extra-dirs', None))

  for spec in worker_pool_specs:
    if image_built_for_first_worker and spec:
      new_spec = spec.copy()
      new_spec['container-image-uri'] = image_built_for_first_worker
      yield new_spec
    else:
      yield spec


def ConstructCustomJobSpec(
    aiplatform_client,
    base_config=None,
    network=None,
    service_account=None,
    enable_web_access=None,
    enable_dashboard_access=None,
    worker_pool_specs=None,
    args=None,
    command=None,
    persistent_resource_id=None,
    **kwargs):
  """Constructs the spec of a custom job to be used in job creation request.

  Args:
    aiplatform_client: The AI Platform API client used.
    base_config: A base CustomJobSpec message instance, e.g. imported from a
      YAML config file, as a template to be overridden.
    network: user network to which the job should be peered with (overrides yaml
      file)
    service_account: A service account (email address string) to use for the
      job.
    enable_web_access: Whether to enable the interactive shell for the job.
    enable_dashboard_access: Whether to enable the access to the dashboard built
      on the job.
    worker_pool_specs: A dict of worker pool specification, usually derived from
      the gcloud command argument values.
    args: A list of arguments to be passed to containers or python packge,
      supposedly derived from the gcloud command flags.
    command: A list of commands to be passed to containers, supposedly derived
      from the gcloud command flags.
    persistent_resource_id: The name of the persistent resource from the same
      project and region on which to run this custom job.
    **kwargs: The keyword args to pass to construct the worker pool specs.

  Returns:
    A CustomJobSpec message instance for creating a custom job.
  """
  job_spec = base_config

  if network is not None:
    job_spec.network = network
  if service_account is not None:
    job_spec.serviceAccount = service_account

  if enable_web_access:
    job_spec.enableWebAccess = enable_web_access
  if enable_dashboard_access:
    job_spec.enableDashboardAccess = enable_dashboard_access

  if worker_pool_specs:
    job_spec.workerPoolSpecs = _ConstructWorkerPoolSpecs(
        aiplatform_client, worker_pool_specs, **kwargs)
  if args:
    for worker_pool_spec in job_spec.workerPoolSpecs:
      if worker_pool_spec.containerSpec:
        worker_pool_spec.containerSpec.args = args
      if worker_pool_spec.pythonPackageSpec:
        worker_pool_spec.pythonPackageSpec.args = args
  if command:
    for worker_pool_spec in job_spec.workerPoolSpecs:
      if worker_pool_spec.containerSpec:
        worker_pool_spec.containerSpec.command = command

  if persistent_resource_id:
    job_spec.persistentResourceId = persistent_resource_id

  return job_spec


def _IsKwargsDefined(key, **kwargs):
  return key in kwargs and bool(kwargs.get(key))
