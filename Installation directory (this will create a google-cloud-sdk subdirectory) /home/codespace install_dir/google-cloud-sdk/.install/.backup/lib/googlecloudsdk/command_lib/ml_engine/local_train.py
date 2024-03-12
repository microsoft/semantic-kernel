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
"""Utilities for running training jobs locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import atexit
import json
import os
import subprocess

from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from six.moves import range


def GetPrimaryNodeName():
  """Get the primary node name.

  Returns:
    str, the name of the primary node. If running in tensorflow 1.x,
    return 'master'. If running in tensorflow 2.x, return 'chief'.
    If tensorflow is not installed in local envrionment, it will return
    the default name 'chief'.
  Raises:
    ValueError: if there is no python executable on the user system thrown by
      execution_utils.GetPythonExecutable.
  """
  exe_override = properties.VALUES.ml_engine.local_python.Get()
  python_executable = (
      exe_override or files.FindExecutableOnPath('python') or
      execution_utils.GetPythonExecutable())
  cmd = [python_executable,
         '-c',
         'import tensorflow as tf; print(tf.version.VERSION)']
  with files.FileWriter(os.devnull) as f:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=f)
  return_code = proc.wait()
  if return_code != 0:
    log.warning('''
    Cannot import tensorflow under path {}. Using "chief" for cluster setting.
    If this is not intended, Please check if tensorflow is installed. Please also
    verify if the python path used is correct. If not, to change the python path:
    use `gcloud config set ml_engine/local_python $python_path`
    Eg: gcloud config set ml_engine/local_python /usr/bin/python3'''.format(
        python_executable))
    return 'chief'

  tf_version = proc.stdout.read()
  if 'decode' in dir(tf_version):
    tf_version = tf_version.decode('utf-8')
  if tf_version.startswith('1.'):
    return 'master'
  elif tf_version.startswith('2.'):
    return 'chief'
  log.warning(
      'Unexpected tensorflow version {}, using the default primary'
      ' node name, aka "chief" for cluster settings'.format(tf_version))
  return 'chief'


def MakeProcess(module_name,
                package_root,
                args=None,
                cluster=None,
                task_type=None,
                index=None,
                **extra_popen_args):
  """Make a Popen object that runs the module, with the correct env.

  If task_type is primary instead replaces the current process with the
  subprocess via execution_utils.Exec
  Args:
    module_name: str. Name of the module to run, e.g. trainer.task
    package_root: str. Absolute path to the package root for the module.
      used as CWD for the subprocess.
    args: [str]. Additional user args. Any relative paths will not work.
    cluster: dict. Cluster configuration dictionary. Suitable for passing to
      tf.train.ClusterSpec.
    task_type: str. Task type of this process. Only relevant if cluster is
      specified.
    index: int. Task index of this process.
    **extra_popen_args: extra args passed to Popen. Used for testing.
  Returns:
    a subprocess.Popen object corresponding to the subprocesses or an int
    corresponding to the return value of the subprocess
    (if task_type is primary)
  Raises:
    ValueError: if there is no python executable on the user system thrown by
      execution_utils.GetPythonExecutable.
  """
  if args is None:
    args = []
  exe_override = properties.VALUES.ml_engine.local_python.Get()
  python_executable = (
      exe_override or files.FindExecutableOnPath('python') or
      execution_utils.GetPythonExecutable())
  cmd = [python_executable, '-m', module_name] + args
  config = {
      'job': {'job_name': module_name, 'args': args},
      'task': {'type': task_type, 'index': index} if cluster else {},
      'cluster': cluster or {},
      'environment': 'cloud'
  }
  log.info(('launching training process:\n'
            'command: {cmd}\n config: {config}').format(
                cmd=' '.join(cmd),
                config=json.dumps(config, indent=2, sort_keys=True)))

  env = os.environ.copy()
  # the tf_config environment variable is used to pass the tensorflow
  # configuration options to the training module. the module specific
  # arguments are passed as command line arguments.
  env['TF_CONFIG'] = json.dumps(config)
  if task_type == GetPrimaryNodeName():
    return execution_utils.Exec(
        cmd, env=env, no_exit=True, cwd=package_root, **extra_popen_args)
  else:
    env = encoding.EncodeEnv(env)
    task = subprocess.Popen(
        cmd,
        env=env,
        cwd=package_root,
        **extra_popen_args
    )
    atexit.register(execution_utils.KillSubprocess, task)
    return task


def RunDistributed(module_name,
                   package_root,
                   num_ps,
                   num_workers,
                   num_evaluators,
                   start_port,
                   user_args=None):
  """Create a cluster configuration and start processes for the cluster.

  Args:
    module_name: str. Python module to use as the task.
    package_root: str. Absolute path to the package root of the module.
    num_ps: int. Number of parameter servers
    num_workers: int. Number of workers.
    num_evaluators: int. Number of evaluators.
    start_port: int. First port for the contiguous block of ports used
      by the cluster.
    user_args: [str]. Additional user args for the task. Any relative paths will
      not work.
  Returns:
    int. the retval of primary subprocess
  """
  ports = list(range(start_port, start_port + num_ps + num_workers + 1))
  cluster = {
      GetPrimaryNodeName(): ['localhost:{port}'.format(port=ports[0])],
      'ps': ['localhost:{port}'.format(port=p)
             for p in ports[1:num_ps + 1]],
      'worker': ['localhost:{port}'.format(port=p)
                 for p in ports[num_ps + 1:]]
  }
  for task_type, addresses in cluster.items():
    if task_type != GetPrimaryNodeName():
      for i in range(len(addresses)):
        MakeProcess(module_name,
                    package_root,
                    args=user_args,
                    task_type=task_type,
                    index=i,
                    cluster=cluster)
  for i in range(num_evaluators):
    MakeProcess(module_name,
                package_root,
                args=user_args,
                task_type='evaluator',
                index=i,
                cluster=cluster)
  return MakeProcess(module_name,
                     package_root,
                     args=user_args,
                     task_type=GetPrimaryNodeName(),
                     index=0,
                     cluster=cluster)
