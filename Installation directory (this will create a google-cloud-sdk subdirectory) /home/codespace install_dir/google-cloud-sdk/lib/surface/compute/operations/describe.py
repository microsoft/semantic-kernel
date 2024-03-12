# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for describing operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.operations import flags
from googlecloudsdk.core import resources


class Describe(base.DescribeCommand):
  """Describe a Compute Engine operation."""

  def __init__(self, *args, **kwargs):
    super(Describe, self).__init__(*args, **kwargs)

  @staticmethod
  def Args(parser):
    flags.COMPUTE_OPERATION_ARG.AddArgument(parser, operation_type='describe')

  @property
  def service(self):
    return self._service

  def _RaiseWrongResourceCollectionException(self, got, path):
    expected_collections = [
        'compute.instances',
        'compute.globalOperations',
        'compute.regionOperations',
        'compute.zoneOperations',
    ]
    raise resources.WrongResourceCollectionException(
        expected=','.join(expected_collections),
        got=got,
        path=path)

  def CreateReference(self, args, compute_holder):
    try:
      ref = flags.COMPUTE_OPERATION_ARG.ResolveAsResource(
          args,
          compute_holder.resources,
          default_scope=compute_scope.ScopeEnum.GLOBAL,
          scope_lister=compute_flags.GetDefaultScopeLister(
              compute_holder.client))
    except resources.WrongResourceCollectionException as ex:
      self._RaiseWrongResourceCollectionException(ex.got, ex.path)

    if ref.Collection() == 'compute.globalOperations':
      self._service = compute_holder.client.apitools_client.globalOperations
    elif ref.Collection() == 'compute.regionOperations':
      self._service = compute_holder.client.apitools_client.regionOperations
    else:
      self._service = compute_holder.client.apitools_client.zoneOperations
    return ref

  def ScopeRequest(self, ref, request):
    if ref.Collection() == 'compute.regionOperations':
      request.region = ref.region
    elif ref.Collection() == 'compute.zoneOperations':
      request.zone = ref.zone

  def Run(self, args):
    compute_holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    operation_ref = self.CreateReference(args, compute_holder)

    request_type = self.service.GetRequestType('Get')
    request = request_type(**operation_ref.AsDict())

    return compute_holder.client.MakeRequests([(self.service, 'Get',
                                                request)])[0]


def DetailedHelp():
  """Construct help text based on the command release track."""
  detailed_help = {
      'brief': 'Describe a Compute Engine operation',
      'DESCRIPTION': """
        *{command}* displays all data associated with a Compute Engine
        operation in a project.
        """,
      'EXAMPLES': """
        To get details about a global operation (e.g. operation-111-222-333-444), run:

          $ {command} operation-111-222-333-444 --global

        To get details about a regional operation, run:

          $ {command} operation-111-222-333-444 --region=us-central1

        To get details about a zonal operation, run:

          $ {command} operation-111-222-333-444 --zone=us-central1-a
        """,
  }
  return detailed_help

Describe.detailed_help = DetailedHelp()
