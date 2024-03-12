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
"""Exports a Gcloud Deploy delivery pipeline resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.clouddeploy import delivery_pipeline
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import export_util
from googlecloudsdk.command_lib.deploy import manifest_util
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.export import util as core_export_util

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        textwrap.dedent("""\

      To return the .yaml definition of the delivery pipeline 'test-pipeline', in region 'us-central1', run:

        $ {command} test-pipeline --region=us-central1

      """)
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Export(base.ExportCommand):
  """Returns the .yaml definition of the specified delivery pipeline.

  The exported yaml definition can be applied by 'deploy apply' command.
  """
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddDeliveryPipelineResourceArg(parser, positional=True)
    core_export_util.AddExportFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    """Entry point of the export command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
    """
    pipeline_ref = args.CONCEPTS.delivery_pipeline.Parse()
    pipeline = delivery_pipeline.DeliveryPipelinesClient().Get(
        pipeline_ref.RelativeName()
    )

    manifest = manifest_util.ProtoToManifest(
        pipeline, pipeline_ref, manifest_util.DELIVERY_PIPELINE_KIND_V1BETA1)

    export_util.Export(manifest, args)
