# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to submit a specified Batch job."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.protorpclite.messages import DecodeError
from apitools.base.py import encoding
from googlecloudsdk.api_lib.batch import jobs
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.batch import resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: An argparse.ArgumentParser-like object. It is mocked out in order to
      capture some information, but behaves like an ArgumentParser.

  Returns:
    network_group flag groups.
  """
  network_group = parser.add_group()
  network_group.add_argument(
      '--network',
      required=True,
      type=str,
      help="""The URL for the network resource.
        Must specify subnetwork as well if network is specified""",
  )
  network_group.add_argument(
      '--subnetwork',
      required=True,
      type=str,
      help="""The URL for the subnetwork resource.
        Must specify network as well if subnetwork is specified""",
  )
  network_group.add_argument(
      '--no-external-ip-address',
      action='store_true',
      default=False,
      help="""Required if no external public IP address
        is attached to the VM. If no external public IP address,
        additional configuration is required to allow the VM
        to access Google Services.""",
  )

  task_spec_group = parser.add_group(required=True)
  task_spec_group.add_argument(
      '--config',
      type=arg_parsers.FileContents(),
      help="""The file path of the job config file in either JSON or YAML format.
        It also supports direct input from stdin with '-' or HereDoc
        (in shells with HereDoc support like Bash) with '- <<DELIMITER'. """,
  )

  runnable_group = task_spec_group.add_group(
      mutex=True,
      help="""Either specify the config file for the job or
        the first runnable in the task spec. Specify either a script file or
        container arguments for the first runnable in the task spec.""",
  )

  script_group = runnable_group.add_group(
      mutex=True,
      help="""Either specify a path to a script file to run or provide
        inline text to execute directly.""",
  )
  script_group.add_argument(
      '--script-file-path',
      help="""Path to script file to run as first runnable in task spec.
        File path should be a valid path on the instance volume.""",
  )
  script_group.add_argument(
      '--script-text',
      type=str,
      help="""Text to run as first runnable in task spec.""",
  )

  container_group = runnable_group.add_group(
      help="""Options to specify the container arguments for the first
        runnable in the task spec."""
  )
  container_group.add_argument(
      '--container-image-uri',
      help="""The URI to pull the container image from.""",
  )
  container_group.add_argument(
      '--container-entrypoint',
      help="""Overrides the `ENTRYPOINT` specified in the container.""",
  )
  container_group.add_argument(
      '--container-commands-file',
      help="""Overrides the `CMD` specified in the container. If there is an
      ENTRYPOINT (either in the container image or with the entrypoint field
      below) then commands are appended as arguments to the ENTRYPOINT.""",
  )

  parser.add_argument(
      '--priority',
      type=arg_parsers.BoundedInt(0, 99),
      help='Job priority [0-99] 0 is the lowest priority.',
  )
  parser.add_argument(
      '--provisioning-model',
      choices={
          'STANDARD': 'The STANDARD VM provisioning model',
          'SPOT': """The SPOT VM provisioning model. Ideal for fault-tolerant
            workloads that can withstand preemption.""",
      },
      type=arg_utils.ChoiceToEnumName,
      help='Specify the allowed provisioning model for the compute instances',
  )
  parser.add_argument(
      '--machine-type',
      type=str,
      help="""Specify the Compute Engine machine type, for
      example, e2-standard-4. Currently only one machine type is supported.""",
  )
  parser.add_argument(
      '--job-prefix',
      type=str,
      help="""Specify the job prefix. A job ID in the format of
      job prefix + %Y%m%d-%H%M%S will be generated. Note that job prefix
      cannot be specified while JOB ID positional argument is
      specified.""",
  )

  return network_group


def _BuildJobMsg(args, job_msg, batch_msgs, release_track):
  """Build the job API message from the args.

  Args:
    args: the args from the parser.
    job_msg: the output job message.
    batch_msgs: the related version of the batch message.
    release_track: the release track from which _BuildJobMsg was called.
  """

  if job_msg.taskGroups is None:
    job_msg.taskGroups = []
  if not job_msg.taskGroups:
    job_msg.taskGroups.insert(
        0, batch_msgs.TaskGroup(taskSpec=batch_msgs.TaskSpec(runnables=[]))
    )
  if args.script_file_path:
    job_msg.taskGroups[0].taskSpec.runnables.insert(
        0,
        batch_msgs.Runnable(
            script=batch_msgs.Script(path=args.script_file_path)
        ),
    )
  if args.script_text:
    job_msg.taskGroups[0].taskSpec.runnables.insert(
        0, batch_msgs.Runnable(script=batch_msgs.Script(text=args.script_text))
    )
  if (
      args.container_commands_file
      or args.container_image_uri
      or args.container_entrypoint
  ):
    container_cmds = []
    if args.container_commands_file:
      container_cmds = files.ReadFileContents(
          args.container_commands_file
      ).splitlines()
    job_msg.taskGroups[0].taskSpec.runnables.insert(
        0,
        batch_msgs.Runnable(
            container=batch_msgs.Container(
                entrypoint=args.container_entrypoint,
                imageUri=args.container_image_uri,
                commands=container_cmds,
            )
        ),
    )

  if args.priority:
    job_msg.priority = args.priority

  # Add default empty allocation policy if there is no allocation policy.
  # For alpha track, add only if an allocation policy is needed by some other
  # argument.
  if release_track == base.ReleaseTrack.ALPHA:
    if job_msg.allocationPolicy is None and (
        args.machine_type
        or (args.network and args.subnetwork)
        or args.provisioning_model
    ):
      job_msg.allocationPolicy = batch_msgs.AllocationPolicy()
  else:
    if job_msg.allocationPolicy is None:
      job_msg.allocationPolicy = batch_msgs.AllocationPolicy()

  if args.machine_type:
    if job_msg.allocationPolicy.instances is None:
      job_msg.allocationPolicy.instances = []
    if not job_msg.allocationPolicy.instances:
      job_msg.allocationPolicy.instances.insert(
          0, batch_msgs.InstancePolicyOrTemplate()
      )
    if job_msg.allocationPolicy.instances[0].policy is None:
      job_msg.allocationPolicy.instances[0].policy = batch_msgs.InstancePolicy()
    job_msg.allocationPolicy.instances[0].policy.machineType = args.machine_type

  if args.network and args.subnetwork:
    if job_msg.allocationPolicy.network is None:
      job_msg.allocationPolicy.network = batch_msgs.NetworkPolicy(
          networkInterfaces=[]
      )
    job_msg.allocationPolicy.network.networkInterfaces.insert(
        0,
        batch_msgs.NetworkInterface(
            network=args.network,
            subnetwork=args.subnetwork,
            noExternalIpAddress=args.no_external_ip_address,
        ),
    )

  if args.provisioning_model:
    if job_msg.allocationPolicy.instances is None:
      job_msg.allocationPolicy.instances = []
    if not job_msg.allocationPolicy.instances:
      job_msg.allocationPolicy.instances.insert(
          0, batch_msgs.InstancePolicyOrTemplate()
      )
    if job_msg.allocationPolicy.instances[0].policy is None:
      job_msg.allocationPolicy.instances[0].policy = batch_msgs.InstancePolicy()
    job_msg.allocationPolicy.instances[0].policy.provisioningModel = (
        arg_utils.ChoiceToEnum(
            args.provisioning_model,
            batch_msgs.InstancePolicy.ProvisioningModelValueValuesEnum,
        )
    )


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Submit(base.Command):
  """Submit a Batch job.

  This command creates and submits a Batch job. After you create and
  submit the job, Batch automatically queues, schedules, and executes it.

  ## EXAMPLES

  To submit a job with a sample JSON configuration file (config.json) and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=config.json

  To submit a job with a sample YAML configuration file (config.yaml) and
  name projects/foo/locations/us-central1/jobs/bar, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=config.yaml

  To submit a job through stdin with a sample job configuration and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=-

      then input json job config via stdin
      {
        job config
      }

  To submit a job through HereDoc with a sample job configuration and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=- << EOF

      {
        job config
      }
      EOF

  For details about how to define a job's configuration using JSON, see the
  projects.locations.jobs resource in the Batch API Reference.
  If you want to define a job's configuration using YAML, convert the JSON
  syntax to YAML.
  """

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    resource_args.AddSubmitJobResourceArgs(parser)

  @classmethod
  def _CreateJobMessage(cls, batch_msgs, config):
    """Parse into Job message using the config input.

    Args:
         batch_msgs: Batch defined proto message.
         config: The input content being either YAML or JSON or the HEREDOC
           input.

    Returns:
         The Parsed job message.
    """
    try:
      result = encoding.PyValueToMessage(batch_msgs.Job, yaml.load(config))
    except (ValueError, AttributeError, yaml.YAMLParseError):
      try:
        result = encoding.JsonToMessage(batch_msgs.Job, config)
      except (ValueError, DecodeError) as e:
        raise exceptions.Error('Unable to parse config file: {}'.format(e))
    return result

  def Run(self, args):
    job_ref = args.CONCEPTS.job.Parse()
    location_ref = job_ref.Parent()
    job_id = self._GetJobId(job_ref, args)

    release_track = self.ReleaseTrack()

    batch_client = jobs.JobsClient(release_track)
    batch_msgs = batch_client.messages
    job_msg = batch_msgs.Job()

    if args.config:
      job_msg = self._CreateJobMessage(batch_msgs, args.config)

    _BuildJobMsg(args, job_msg, batch_msgs, release_track)

    resp = batch_client.Create(job_id, location_ref, job_msg)
    log.status.Print(
        'Job {jobName} was successfully submitted.'.format(jobName=resp.uid)
    )
    return resp

  def _GetJobId(self, job_ref, args):
    job_id = job_ref.RelativeName().split('/')[-1]

    if job_id != resource_args.INVALIDJOBID and args.job_prefix:
      raise exceptions.Error(
          '--job-prefix cannot be specified when JOB ID positional '
          'argument is specified'
      )
    # Remove the invalid job_id if no job_id being specified,
    # batch_client would create a valid job_id.
    elif args.job_prefix:
      job_id = (
          args.job_prefix
          + '-'
          + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
      )

    # The case that both positional JOB ID and prefix are not specified
    elif job_id == resource_args.INVALIDJOBID:
      job_id = None

    return job_id


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SubmitBeta(Submit):
  """Submit a Batch job.

  This command creates and submits a Batch job. After you create and
  submit the job, Batch automatically queues, schedules, and executes it.

  ## EXAMPLES

  To submit a job with a sample JSON configuration file (config.json) and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=config.json

  To submit a job with a sample YAML configuration file (config.yaml) and
  name projects/foo/locations/us-central1/jobs/bar, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=config.yaml

  To submit a job through stdin with a sample job configuration and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=-

      then input json job config via stdin
      {
        job config
      }

  To submit a job through HereDoc with a sample job configuration and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=- << EOF

      {
        job config
      }
      EOF

  For details about how to define a job's configuration using JSON, see the
  projects.locations.jobs resource in the Batch API Reference.
  If you want to define a job's configuration using YAML, convert the JSON
  syntax to YAML.
  """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SubmitAlpha(SubmitBeta):
  """Submit a Batch job.

  This command creates and submits a Batch job. After you create and
  submit the job, Batch automatically queues, schedules, and executes it.

  ## EXAMPLES

  To submit a job with a sample JSON configuration file (config.json) and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=config.json

  To submit a job with a sample YAML configuration file (config.yaml) and
  name projects/foo/locations/us-central1/jobs/bar, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=config.yaml

  To submit a job through stdin with a sample job configuration and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=-

      then input json job config via stdin
      {
        job config
      }

  To submit a job through HereDoc with a sample job configuration and name
  `projects/foo/locations/us-central1/jobs/bar`, run:

    $ {command} projects/foo/locations/us-central1/jobs/bar --config=- << EOF

      {
        job config
      }
      EOF

  For details about how to define a job's configuration using JSON, see the
  projects.locations.jobs resource in the Batch API Reference.
  If you want to define a job's configuration using YAML, convert the JSON
  syntax to YAML.
  """
