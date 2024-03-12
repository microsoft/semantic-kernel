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
"""Functions required to interact with Docker to run a container."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.ai.docker import utils
from googlecloudsdk.core import config

_DEFAULT_CONTAINER_CRED_KEY_PATH = "/tmp/keys/cred_key.json"


def _DockerRunOptions(enable_gpu=False,
                      service_account_key=None,
                      cred_mount_path=_DEFAULT_CONTAINER_CRED_KEY_PATH,
                      extra_run_opts=None):
  """Returns a list of 'docker run' options.

  Args:
    enable_gpu: (bool) using GPU or not.
    service_account_key: (bool) path of the service account key to use in host.
    cred_mount_path: (str) path in the container to mount the credential key.
    extra_run_opts: (List[str]) other custom docker run options.
  """
  if extra_run_opts is None:
    extra_run_opts = []

  runtime = ["--runtime", "nvidia"] if enable_gpu else []

  if service_account_key:
    mount = ["-v", "{}:{}".format(service_account_key, cred_mount_path)]
  else:
    # Calls Application Default Credential (ADC),
    adc_file_path = config.ADCEnvVariable() or config.ADCFilePath()
    mount = ["-v", "{}:{}".format(adc_file_path, cred_mount_path)]
  env_var = ["-e", "GOOGLE_APPLICATION_CREDENTIALS={}".format(cred_mount_path)]

  return ["--rm"] + runtime + mount + env_var + ["--ipc", "host"
                                                ] + extra_run_opts


def RunContainer(image_name,
                 enable_gpu=False,
                 service_account_key=None,
                 run_args=None,
                 user_args=None):
  """Calls `docker run` on a given image with specified arguments.

  Args:
    image_name: (str) Name or ID of Docker image to run.
    enable_gpu: (bool) Whether to use GPU
    service_account_key: (str) Json file of a service account key  auth.
    run_args: (List[str]) Extra custom options to apply to `docker run` after
      our defaults.
    user_args: (List[str]) Extra user defined arguments to supply to the
      entrypoint.
  """
  # TODO(b/177787660): add interactive mode option

  if run_args is None:
    run_args = []

  if user_args is None:
    user_args = []

  run_opts = _DockerRunOptions(
      enable_gpu=enable_gpu,
      service_account_key=service_account_key,
      extra_run_opts=run_args)

  command = ["docker", "run"] + run_opts + [image_name] + user_args

  utils.ExecuteDockerCommand(command)
