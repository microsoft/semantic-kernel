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

"""Command for listing testable permissions for a given resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.iam import exceptions
from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import resources


class ListTestablePermissions(base.Command):
  """List IAM testable permissions for a resource.

  Testable permissions mean the permissions that user can add or remove in
  a role at a given resource.
  The resource can be referenced either via the full resource name or via a URI.

  ## EXAMPLES

  List testable permissions for a resource identified via full resource name:

    $ {command} //cloudresourcemanager.googleapis.com/organizations/1234567

  List testable permissions for a resource identified via URI:

    $ {command} https://www.googleapis.com/compute/v1/projects/example-project
  """

  @staticmethod
  def Args(parser):
    flags.GetResourceNameFlag(
        'get the testable permissions for').AddToParser(parser)
    base.FILTER_FLAG.AddToParser(parser)

  def Run(self, args):
    resource = None
    if args.resource.startswith('//'):
      resource = args.resource
    elif args.resource.startswith('http'):
      resource = iam_util.GetFullResourceName(
          resources.REGISTRY.Parse(args.resource))
    if not resource:
      raise exceptions.InvalidResourceException(
          'The given resource is not a valid full resource name or URL.')

    client, messages = util.GetClientAndMessages()
    return list_pager.YieldFromList(
        client.permissions,
        messages.QueryTestablePermissionsRequest(fullResourceName=resource),
        field='permissions',
        method='QueryTestablePermissions',
        batch_size_attribute='pageSize')
