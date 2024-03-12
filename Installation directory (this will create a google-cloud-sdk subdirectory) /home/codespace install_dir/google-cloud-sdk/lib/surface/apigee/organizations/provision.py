# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command to provision an Apigee SaaS organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Provision(base.DescribeCommand):
  """Provision an Apigee SaaS organization."""

  detailed_help = {
      "DESCRIPTION":
          """\
  {description}

  `{command}` creates an Apigee organization and populates it with the
  necessary child resources to be immediately useable.

  This is a long running operation and could take anywhere from 10 minutes to 1
  hour to complete.

  At the moment, only trial organizations are supported.
  """,
      "EXAMPLES":
          """
          To provision an organization for the active Cloud Platform project,
          attached to a network named ``default'' run:

              $ {command} --authorized-network=default

          To provision an organization asynchronously and print only the name of
          the launched operation, run:

              $ {command} --authorized-network=default --async --format="value(name)"

          To provision an organization for the project named ``my-proj'', with
          analytics and runtimes located in ``us-central1'', run:

              $ {command} --authorized-network=default --project=my-proj --analytics-region=us-central1 --runtime-location=us-central1-a
          """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        "--authorized-network",
        required=True,
        help="""\
  Name of the network to which the provisioned organization should be attached.
  This must be a VPC network peered through Service Networking. To get a list
  of existing networks, run:

      $ gcloud compute networks list

  To check whether a network is peered through Service Networking, run:

      $ gcloud services vpc-peerings list --network=NETWORK_NAME --service=servicenetworking.googleapis.com

  To create a new network suitable for Apigee provisioning, choose a name for
  the network and address range, and run:

      $ gcloud compute networks create NETWORK_NAME --bgp-routing-mode=global --description='network for an Apigee trial'
      $ gcloud compute addresses create ADDRESS_RANGE_NAME --global --prefix-length=16 --description="peering range for an Apigee trial" --network=NETWORK_NAME --purpose=vpc_peering
      $ gcloud services vpc-peerings connect --service=servicenetworking.googleapis.com --network=NETWORK_NAME --ranges=ADDRESS_RANGE_NAME"""
    )
    parser.add_argument(
        "--analytics-region",
        help=("Primary Cloud Platform region for analytics data storage. For "
              "valid values, see: "
              "https://docs.apigee.com/hybrid/latest/precog-provision.\n\n"
              "If unspecified, the default is ``us-west1''"))
    parser.add_argument(
        "--runtime-location",
        help=("Cloud Platform location for the runtime instance. For trial "
              "organizations, this is a compute zone. To get a list of valid "
              "zones, run `gcloud compute zones list`. If unspecified, the "
              "default is ``us-west1-a''."))
    parser.add_argument(
        "--async",
        action="store_true",
        dest="async_",
        help=("If set, returns immediately and outputs a description of the "
              "long running operation that was launched. Else, `{command}` "
              "will block until the organization has been provisioned.\n\n"
              "To monitor the operation once it's been launched, run "
              "`{grandparent_command} operations describe OPERATION_NAME`."))

  def Run(self, args):
    """Run the provision command."""
    org_info = {"authorizedNetwork": args.authorized_network}
    if args.analytics_region:
      org_info["analyticsRegion"] = args.analytics_region
    if args.runtime_location:
      org_info["runtimeLocation"] = args.runtime_location

    project = properties.VALUES.core.project.Get()
    if project is None:
      exceptions.RequiredArgumentException(
          "--project",
          "Must provide a GCP project in which to provision the organization.")

    operation = apigee.ProjectsClient.ProvisionOrganization(project, org_info)
    apigee.OperationsClient.SplitName(operation)
    if args.async_:
      return operation

    log.info("Started provisioning operation %s", operation["name"])

    return waiter.WaitFor(
        apigee.LROPoller(operation["organization"]),
        operation["uuid"],
        "Provisioning organization",
        max_wait_ms=60 * 60 * 1000)
