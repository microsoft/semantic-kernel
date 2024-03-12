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
"""Validations of the arguments of custom-jobs command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.ai import util as api_util
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.command_lib.ai.custom_jobs import local_util
from googlecloudsdk.command_lib.ai.docker import utils as docker_utils
from googlecloudsdk.core.util import files


def ValidateRegion(region):
  """Validate whether the given region is allowed for specifically custom job."""
  validation.ValidateRegion(
      region, available_regions=constants.SUPPORTED_TRAINING_REGIONS)


def ValidateCreateArgs(args, job_spec_from_config, version):
  """Validate the argument values specified in `create` command."""
  # TODO(b/186082396): Add more validations for other args.
  if args.worker_pool_spec:
    _ValidateWorkerPoolSpecArgs(args.worker_pool_spec, version)
  else:
    _ValidateWorkerPoolSpecsFromConfig(job_spec_from_config)


def _ValidateWorkerPoolSpecArgs(worker_pool_specs, version):
  """Validates the argument values specified via `--worker-pool-spec` flags.

  Args:
    worker_pool_specs: List[dict], a list of worker pool specs specified in
      command line.
    version: str, the API version this command will interact with, either GA or
      BETA.
  """
  if not worker_pool_specs[0]:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        'Empty value is not allowed for the first `--worker-pool-spec` flag.')

  _ValidateHardwareInWorkerPoolSpecArgs(worker_pool_specs, version)
  _ValidateSoftwareInWorkerPoolSpecArgs(worker_pool_specs)


def _ValidateHardwareInWorkerPoolSpecArgs(worker_pool_specs, api_version):
  """Validates the hardware related fields specified in `--worker-pool-spec` flags.

  Args:
    worker_pool_specs: List[dict], a list of worker pool specs specified in
      command line.
    api_version: str, the API version this command will interact with, either GA
      or BETA.
  """
  for spec in worker_pool_specs:
    if spec:
      if 'machine-type' not in spec:
        raise exceptions.InvalidArgumentException(
            '--worker-pool-spec',
            'Key [machine-type] required in dict arg but not provided.')

      if 'accelerator-count' in spec and 'accelerator-type' not in spec:
        raise exceptions.InvalidArgumentException(
            '--worker-pool-spec',
            'Key [accelerator-type] required as [accelerator-count] is specified.'
        )

      accelerator_type = spec.get('accelerator-type', None)
      if accelerator_type:
        type_enum = api_util.GetMessage(
            'MachineSpec', api_version).AcceleratorTypeValueValuesEnum
        valid_types = [
            type for type in type_enum.names()
            if type.startswith('NVIDIA') or type.startswith('TPU')
        ]
        if accelerator_type not in valid_types:
          raise exceptions.InvalidArgumentException(
              '--worker-pool-spec',
              ('Found invalid value of [accelerator-type]: {actual}. '
               'Available values are [{expected}].').format(
                   actual=accelerator_type,
                   expected=', '.join(v for v in sorted(valid_types))))


def _ValidateSoftwareInWorkerPoolSpecArgs(worker_pool_specs):
  """Validates the software fields specified in all `--worker-pool-spec` flags."""
  has_local_package = _ValidateSoftwareInFirstWorkerPoolSpec(
      worker_pool_specs[0])

  if len(worker_pool_specs) > 1:
    _ValidateSoftwareInRestWorkerPoolSpecs(worker_pool_specs[1:],
                                           has_local_package)


def _ValidateSoftwareInFirstWorkerPoolSpec(spec):
  """Validates the software related fields specified in the first `--worker-pool-spec` flags.

  Args:
    spec: dict, the specification of the first worker pool.

  Returns:
    A boolean value whether a local package will be used.
  """
  if 'local-package-path' in spec:
    _ValidateWorkerPoolSoftwareWithLocalPackage(spec)
    return True
  else:
    _ValidateWorkerPoolSoftwareWithoutLocalPackages(spec)
    return False


def _ValidateSoftwareInRestWorkerPoolSpecs(specs,
                                           is_local_package_specified=False):
  """Validates the argument values specified in all but the first `--worker-pool-spec` flags.

  Args:
    specs: List[dict], the list all but the first worker pool specs specified in
      command line.
    is_local_package_specified: bool, whether local package is specified
      in the first worker pool.
  """
  for spec in specs:
    if spec:
      if is_local_package_specified:
        # No more software allowed
        software_fields = {
            'executor-image-uri',
            'container-image-uri',
            'python-module',
            'script',
            'requirements',
            'extra-packages',
            'extra-dirs',
        }
        _RaiseErrorIfUnexpectedKeys(
            unexpected_keys=software_fields.intersection(spec.keys()),
            reason=('A local package has been specified in the first '
                    '`--worker-pool-spec` flag and to be used for all workers, '
                    'do not specify these keys elsewhere.'))
      else:
        if 'local-package-path' in spec:
          raise exceptions.InvalidArgumentException(
              '--worker-pool-spec',
              ('Key [local-package-path] is only allowed in the first '
               '`--worker-pool-spec` flag.'))
        _ValidateWorkerPoolSoftwareWithoutLocalPackages(spec)


def _ValidateWorkerPoolSoftwareWithLocalPackage(spec):
  """Validate the software in a single `--worker-pool-spec` when `local-package-path` is specified."""
  assert 'local-package-path' in spec
  _RaiseErrorIfNotExists(
      spec['local-package-path'], flag_name='--worker-pool-spec')

  if 'executor-image-uri' not in spec:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        'Key [executor-image-uri] is required when `local-package-path` is specified.'
    )

  if ('python-module' in spec) + ('script' in spec) != 1:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        'Exactly one of keys [python-module, script] is required '
        'when `local-package-path` is specified.')

  if 'output-image-uri' in spec:
    output_image = spec['output-image-uri']
    hostname = output_image.split('/')[0]
    container_registries = ['gcr.io', 'eu.gcr.io', 'asia.gcr.io', 'us.gcr.io']
    if hostname not in container_registries and not hostname.endswith(
        '-docker.pkg.dev'):
      raise exceptions.InvalidArgumentException(
          '--worker-pool-spec',
          'The value of `output-image-uri` has to be a valid gcr.io or Artifact Registry image'
      )
    try:
      docker_utils.ValidateRepositoryAndTag(output_image)
    except ValueError as e:
      raise exceptions.InvalidArgumentException(
          '--worker-pool-spec',
          r"'{}' is not a valid container image uri: {}".format(
              output_image, e))


def _ValidateWorkerPoolSoftwareWithoutLocalPackages(spec):
  """Validate the software in a single `--worker-pool-spec` when `local-package-path` is not specified."""

  assert 'local-package-path' not in spec

  has_executor_image = 'executor-image-uri' in spec
  has_container_image = 'container-image-uri' in spec
  has_python_module = 'python-module' in spec

  if (has_executor_image + has_container_image) != 1:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        ('Exactly one of keys [executor-image-uri, container-image-uri] '
         'is required.'))

  if has_container_image and has_python_module:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec',
        ('Key [python-module] is not allowed together with key '
         '[container-image-uri].'))

  if has_executor_image and not has_python_module:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec', 'Key [python-module] is required.')

  local_package_only_keys = {
      'script',
      'requirements',
      'extra-packages',
      'extra-dirs',
  }
  unexpected_keys = local_package_only_keys.intersection(spec.keys())
  _RaiseErrorIfUnexpectedKeys(
      unexpected_keys,
      reason='Only allow to specify together with `local-package-path` in the first `--worker-pool-spec` flag'
  )


def _RaiseErrorIfUnexpectedKeys(unexpected_keys, reason):
  if unexpected_keys:
    raise exceptions.InvalidArgumentException(
        '--worker-pool-spec', 'Keys [{keys}] are not allowed: {reason}.'.format(
            keys=', '.join(sorted(unexpected_keys)), reason=reason))


def _ValidateWorkerPoolSpecsFromConfig(job_spec):
  """Validate WorkerPoolSpec message instances imported from the config file."""
  # TODO(b/186082396): adds more validations for other fields.
  for spec in job_spec.workerPoolSpecs:
    use_python_package = spec.pythonPackageSpec and (
        spec.pythonPackageSpec.executorImageUri or
        spec.pythonPackageSpec.pythonModule)
    use_container = spec.containerSpec and spec.containerSpec.imageUri

    if (use_container and use_python_package) or (not use_container and
                                                  not use_python_package):
      raise exceptions.InvalidArgumentException(
          '--config',
          ('Exactly one of fields [pythonPackageSpec, containerSpec] '
           'is required for a [workerPoolSpecs] in the YAML config file.'))


def _ImageBuildArgSpecified(args):
  """Returns names of all the flags specified only for image building."""
  image_build_args = []
  if args.script:
    image_build_args.append('script')
  if args.python_module:
    image_build_args.append('python-module')
  if args.requirements:
    image_build_args.append('requirements')
  if args.extra_packages:
    image_build_args.append('extra-packages')
  if args.extra_dirs:
    image_build_args.append('extra-dirs')
  if args.output_image_uri:
    image_build_args.append('output-image-uri')

  return image_build_args


def _ValidBuildArgsOfLocalRun(args):
  """Validates the arguments related to image building and normalize them."""
  build_args_specified = _ImageBuildArgSpecified(args)
  if not build_args_specified:
    return

  if not args.script and not args.python_module:
    raise exceptions.MinimumArgumentException(
        ['--script', '--python-module'],
        'They are required to build a training container image. '
        'Otherwise, please remove flags [{}] to directly run the `executor-image-uri`.'
        .format(', '.join(sorted(build_args_specified))))

  # Validate main script's existence:
  if args.script:
    arg_name = '--script'
  else:
    args.script = local_util.ModuleToPath(args.python_module)
    arg_name = '--python-module'

  script_path = os.path.normpath(
      os.path.join(args.local_package_path, args.script))
  if not os.path.exists(script_path) or not os.path.isfile(script_path):
    raise exceptions.InvalidArgumentException(
        arg_name, r"File '{}' is not found under the package: '{}'.".format(
            args.script, args.local_package_path))

  # Validate extra custom packages specified:
  for package in (args.extra_packages or []):
    package_path = os.path.normpath(
        os.path.join(args.local_package_path, package))
    if not os.path.exists(package_path) or not os.path.isfile(package_path):
      raise exceptions.InvalidArgumentException(
          '--extra-packages',
          r"Package file '{}' is not found under the package: '{}'.".format(
              package, args.local_package_path))

  # Validate extra directories specified:
  for directory in (args.extra_dirs or []):
    dir_path = os.path.normpath(
        os.path.join(args.local_package_path, directory))
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
      raise exceptions.InvalidArgumentException(
          '--extra-dirs',
          r"Directory '{}' is not found under the package: '{}'.".format(
              directory, args.local_package_path))

  # Validate output image uri is in valid format
  if args.output_image_uri:
    output_image = args.output_image_uri
    try:
      docker_utils.ValidateRepositoryAndTag(output_image)
    except ValueError as e:
      raise exceptions.InvalidArgumentException(
          '--output-image-uri',
          r"'{}' is not a valid container image uri: {}".format(
              output_image, e))
  else:
    args.output_image_uri = docker_utils.GenerateImageName(
        base_name=args.script)


def ValidateLocalRunArgs(args):
  """Validates the arguments specified in `local-run` command and normalize them."""
  args_local_package_pach = args.local_package_path
  if args_local_package_pach:
    work_dir = os.path.abspath(files.ExpandHomeDir(args_local_package_pach))
    if not os.path.exists(work_dir) or not os.path.isdir(work_dir):
      raise exceptions.InvalidArgumentException(
          '--local-package-path',
          r"Directory '{}' is not found.".format(work_dir))
  else:
    work_dir = files.GetCWD()
  args.local_package_path = work_dir

  _ValidBuildArgsOfLocalRun(args)

  return args


def _RaiseErrorIfNotExists(local_package_path, flag_name):
  """Validate the local package is valid.

  Args:
    local_package_path: str, path of the local directory to check.
    flag_name: str, indicates in which flag the path is specified.
  """
  work_dir = os.path.abspath(files.ExpandHomeDir(local_package_path))
  if not os.path.exists(work_dir) or not os.path.isdir(work_dir):
    raise exceptions.InvalidArgumentException(
        flag_name, r"Directory '{}' is not found.".format(work_dir))
