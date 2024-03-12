# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""`gcloud dataproc-gdc instances create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.edge_cloud.container import resource_args as gdce_resource_args
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DATAPROCGDC_API_NAME = 'dataprocgdc'
DATAPROCGDC_API_VERSION = 'v1alpha1'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Dataproc GDC service instance.

  A service instance is a deployment of the Dataproc operator running on a
  Kubernetes cluster. Each cluster may have at most one Dataproc service
  instance deployed. A service instance manages Application Environments
  and Spark Applications that run locally on the cluster.
  """

  detailed_help = {'EXAMPLES': """\
          To create a Dataproc GDC service instance with name `my-instance`
          in location `us-central1` running on a GDCE cluster named
          `my-cluster`, run:

          $ {command} my-instance --location=us-central1 --gdce-cluster=my-cluster

          Note that the GDCE cluster and the Dataproc GDC service instance must
          be in the same project and Cloud location (in this case us-central1).
          """}

  @staticmethod
  def Args(parser):
    concept_parsers.ConceptParser(
        [
            GetInstanceResourcePresentationSpec(),
            GetGdceClusterResourcePresentationSpec(),
        ],
        command_level_fallthroughs={
            # Set the GDCE cluster location to the instance location
            '--gdce-cluster.location': ['instance.location']
        },
    ).AddToParser(parser)
    parser.add_argument(
        '--request-id',
        help="""An optional request ID to identify requests. If the service receives two identical
        instance create requests with the same request_id, the second request is
        ignored and the operation that corresponds to the first request is returned for both.

        The request ID must be a valid UUID with the exception that zero UUID is
        not supported (00000000-0000-0000-0000-000000000000).""",
    )
    parser.add_argument(
        '--display-name',
        help=(
            'Human-readable name for this service instance to be used in user'
            ' interfaces.'
        ),
    )
    parser.add_argument(
        '--annotations',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=(
            'List of annotation KEY=VALUE pairs to add to the service instance.'
        ),
    )
    labels_util.AddCreateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    dataprocgdc_client = apis.GetClientInstance(
        DATAPROCGDC_API_NAME, DATAPROCGDC_API_VERSION
    )
    messages = apis.GetMessagesModule('dataprocgdc', 'v1alpha1')
    instance_ref = args.CONCEPTS.instance.Parse()
    cluster_ref = args.CONCEPTS.gdce_cluster.Parse()

    if args.annotations:
      annotations = encoding.DictToAdditionalPropertyMessage(
          args.annotations,
          messages.ServiceInstance.AnnotationsValue,
          sort_items=True,
      )
    else:
      annotations = None

    create_req = (
        messages.DataprocgdcProjectsLocationsServiceInstancesCreateRequest(
            serviceInstanceId=instance_ref.Name(),
            parent=instance_ref.Parent().RelativeName(),
            requestId=args.request_id,
            serviceInstance=messages.ServiceInstance(
                displayName=args.display_name,
                labels=labels_util.ParseCreateArgs(
                    args, messages.ServiceInstance.LabelsValue
                ),
                annotations=annotations,
                gdceCluster=messages.GdceCluster(
                    gdceCluster=cluster_ref.RelativeName()
                ),
            ),
        )
    )

    create_op = dataprocgdc_client.projects_locations_serviceInstances.Create(
        create_req
    )

    async_ = getattr(args, 'async_', False)
    if not async_:
      # Poll for operation
      operation_ref = resources.REGISTRY.Parse(
          create_op.name, collection='dataprocgdc.projects.locations.operations'
      )
      poller = waiter.CloudOperationPoller(
          dataprocgdc_client.projects_locations_serviceInstances,
          dataprocgdc_client.projects_locations_operations,
      )
      waiter.WaitFor(
          poller,
          operation_ref,
          'Waiting for service instance create operation [{0}]'.format(
              operation_ref.RelativeName()
          ),
      )
      log.CreatedResource(
          instance_ref.Name(),
          details=(
              '- service instance created in [{0}] for cluster [{1}]'.format(
                  instance_ref.Parent().RelativeName(),
                  cluster_ref.RelativeName(),
              )
          ),
      )
      return

    log.status.Print(
        'Create request issued for: [{0}]\nCheck operation [{1}] for status.'
        .format(instance_ref.Name(), create_op.name)
    )


def GetInstanceResourcePresentationSpec():
  instance_data = yaml_data.ResourceYAMLData.FromPath(
      'dataproc_gdc.service_instance'
  )
  resource_spec = concepts.ResourceSpec.FromYaml(instance_data.GetData())
  return presentation_specs.ResourcePresentationSpec(
      name='instance',
      concept_spec=resource_spec,
      group_help='Name of the service instance to create.',
      required=True,
      prefixes=False,
  )


def GetGdceClusterResourcePresentationSpec():
  return presentation_specs.ResourcePresentationSpec(
      name='--gdce-cluster',
      concept_spec=gdce_resource_args.GetClusterResourceSpec(),
      group_help='The GDCE cluster on which to create the service instance.',
      required=True,
      prefixes=True,
      # This hides the location flag for the GDCE cluster resource, since we
      # always enforce that the cluster is the same region as the instance
      flag_name_overrides={'location': ''},
  )
