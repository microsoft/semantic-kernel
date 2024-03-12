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
"""The Secure Source Manager create instance command module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from googlecloudsdk.api_lib.securesourcemanager import instances
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import flags
from googlecloudsdk.command_lib.source_manager import resource_args
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a Secure Source Manager instance.
        """,
    'EXAMPLES':
        """
            To create a Secure Source Manager instance named 'my-instance' in location 'us-central1' asynchronously, run:

            $ {command} my-instance --region=us-central1

            To create a Secure Source Manager instance named 'my-instance' in location 'us-central1' synchronously, and wait a maximum of 30 minutes for it to finish being created, run:

            $ {command} my-instance --region=us-central1 --no-async --max-wait=30m
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a Secure Source Manager instance."""

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'to create')
    flags.AddKmsKey(parser)
    flags.AddCAPool(parser)
    flags.AddIsPrivate(parser)
    flags.AddMaxWait(parser, '60m')  # Default to 60 minutes wait.
    # Create --async flag and set default to be true.
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    is_async = args.async_
    max_wait = datetime.timedelta(seconds=args.max_wait)
    kms_key = args.kms_key
    is_private = args.is_private
    ca_pool = args.ca_pool

    # Get a long-running operation for this creation
    client = instances.InstancesClient()
    instance = args.CONCEPTS.instance.Parse()

    try:
      operation = client.Create(
          instance_ref=instance,
          kms_key=kms_key,
          is_private=is_private,
          ca_pool=ca_pool,
      )
    except exceptions.EnableServicePermissionDeniedException:
      # Display a message indicating the special invitation only status of SSM
      # upon failure to enable the service.
      log.warning(
          'Secure Source Manager API (securesourcemanager.googleapis.com) has'
          ' not been enabled on the project. Secure Source Manager is generally'
          ' available (GA) by invitation only. To use Secure Source Manager,'
          ' contact your Google Account team.'
      )
      raise

    log.status.Print('Create request issued for [{}].'
                     .format(instance.instancesId))

    # Return an in-progress operation if async is requested.
    if is_async:
      # Create operations have no format by default,
      # but here we want the operation metadata to be printed.
      if not args.IsSpecified('format'):
        args.format = 'default'
      return operation

    # Return a progress tracker in synchronous mode
    return client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='Waiting for operation [{}] to complete'
        .format(
            client.GetOperationRef(operation).RelativeName()),
        max_wait=max_wait)


Create.detailed_help = DETAILED_HELP
