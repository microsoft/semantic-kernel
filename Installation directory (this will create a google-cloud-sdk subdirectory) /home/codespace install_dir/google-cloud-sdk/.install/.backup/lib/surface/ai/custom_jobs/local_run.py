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
"""Command to run a training application locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai.custom_jobs import flags
from googlecloudsdk.command_lib.ai.custom_jobs import local_util
from googlecloudsdk.command_lib.ai.custom_jobs import validation
from googlecloudsdk.command_lib.ai.docker import build as docker_builder
from googlecloudsdk.command_lib.ai.docker import run as docker_runner
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Run a custom training locally.

  Packages your training code into a Docker image and executes it locally.
  """
  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""\
          {description}

          You should execute this command in the top folder which includes all
          the code and resources you want to pack and run, or specify the
          'work-dir' flag to point to it. Any other path you specified via flags
          should be a relative path to the work-dir and under it; otherwise it
          will be unaccessible.

          Supposing your directories are like the following structures:

            /root
              - my_project
                  - my_training
                      - task.py
                      - util.py
                      - setup.py
                  - other_modules
                      - some_module.py
                  - dataset
                      - small.dat
                      - large.dat
                  - config
                  - dep
                      - foo.tar.gz
                  - bar.whl
                  - requirements.txt
              - another_project
                  - something

          If you set 'my_project' as the package, then you should
          execute the task.py by specifying "--script=my_training/task.py" or
          "--python-module=my_training.task", the 'requirements.txt' will be
          processed. And you will also be able to install extra packages by,
          e.g. specifying "--extra-packages=dep/foo.tar.gz,bar.whl" or include
          extra directories, e.g. specifying "--extra-dirs=dataset,config".

          If you set 'my_training' as the package, then you should
          execute the task.py by specifying "--script=task.py" or
          "--python-module=task", the 'setup.py' will be processed. However, you
          won't be able to access any other files or directories that are not in
          'my_training' folder.

          See more details in the HELP info of the corresponding flags.
          """),
      'EXAMPLES':
          """\
          To execute an python module with required dependencies, run:

            $ {command} --python-module=my_training.task --executor-image-uri=gcr.io/my/image --requirements=pandas,scipy>=1.3.0

          To execute a python script using local GPU, run:

            $ {command} --script=my_training/task.py --executor-image-uri=gcr.io/my/image --gpu

          To execute an arbitrary script with custom arguments, run:

            $ {command} --script=my_run.sh --executor-image-uri=gcr.io/my/image -- --my-arg bar --enable_foo

          To run an existing container training without building new image, run:

            $ {command} --executor-image-uri=gcr.io/my/custom-training-image
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddLocalRunCustomJobFlags(parser)

  def Run(self, args):
    args = validation.ValidateLocalRunArgs(args)

    with files.ChDir(args.local_package_path):
      log.status.Print('Package is set to {}.'.format(args.local_package_path))
      executable_image = args.executor_image_uri or args.base_image

      if args.script:
        # TODO(b/176214485): Consider including the image id in build result.
        built_image = docker_builder.BuildImage(
            base_image=executable_image,
            host_workdir=args.local_package_path,
            main_script=args.script,
            python_module=args.python_module,
            requirements=args.requirements,
            extra_packages=args.extra_packages,
            extra_dirs=args.extra_dirs,
            output_image_name=args.output_image_uri)
        executable_image = built_image.name
        log.status.Print('A training image is built.')

      log.status.Print('Starting to run ...')
      docker_runner.RunContainer(
          image_name=executable_image,
          enable_gpu=args.gpu,
          service_account_key=args.service_account_key_file,
          user_args=args.args)

      log.out.Print(
          'A local run is finished successfully using custom image: {}.'.format(
              executable_image))

      # Clean generated cache
      cache_dir, _ = os.path.split(
          os.path.join(args.local_package_path, args.script or ''))
      if local_util.ClearPyCache(cache_dir):
        log.status.Print(
            'Cleaned Python cache from directory: {}'.format(cache_dir))
