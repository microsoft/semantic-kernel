# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Delete instance command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete an instance."""

  detailed_help = {
      'EXAMPLES': """\
          To delete an instance, run:

            $ {command} my-instance --region=us-central1
          """,
  }

  @classmethod
  def Args(cls, parser):
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddTimeoutFlag(parser)
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    flags.AddInstanceResourceArg(parser, 'delete', dataproc.api_version)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())

    instance_ref = args.CONCEPTS.instance.Parse()

    request = dataproc.messages.DataprocProjectsRegionsClustersDeleteRequest(
        clusterName=instance_ref.clusterName,
        region=instance_ref.region,
        projectId=instance_ref.projectId,
        requestId=util.GetUniqueId())

    console_io.PromptContinue(
        message="The instance '{0}' will be "
        'deleted.'.format(instance_ref.clusterName),
        cancel_on_no=True,
        cancel_string='Deletion aborted by user.')

    operation = dataproc.client.projects_regions_clusters.Delete(request)

    if args.async_:
      log.status.Print('Deleting [{0}] with operation [{1}].'.format(
          instance_ref, operation.name))
      return operation

    operation = util.WaitForOperation(
        dataproc,
        operation,
        message='Waiting for instance deletion operation',
        timeout_s=args.timeout)

    return operation
