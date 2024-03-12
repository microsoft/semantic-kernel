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
"""Command to create a fleet namespace."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.util.args import labels_util


class Create(base.CreateCommand):
  """Create a fleet namespace.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The project has a fleet namespace with the same name.
  * The caller does not have permission to access the given project.

  ## EXAMPLES

  To create a fleet namespace with name `NAMESPACE` in the active project, run:

    $ {command} NAMESPACE

  To create a fleet namespace in fleet scope `SCOPE` in project `PROJECT_ID`
  with name
  `NAMESPACE`, run:

    $ {command} NAMESPACE --scope=SCOPE --project=PROJECT_ID
  """

  @classmethod
  def Args(cls, parser):
    resources.AddScopeNamespaceResourceArg(
        parser,
        api_version=util.VERSION_MAP[cls.ReleaseTrack()],
        namespace_help=(
            'Name of the fleet namespace to be created. Must comply with'
            " RFC 1123 (up to 63 characters, alphanumeric and '-')"
        ),
        required=True,
    )
    labels_util.AddCreateLabelsFlags(parser)
    resources.AddCreateNamespaceLabelsFlags(parser)

  def Run(self, args):
    namespace_arg = args.CONCEPTS.namespace.Parse()
    name = namespace_arg.Name()
    namespace_path = namespace_arg.RelativeName()
    parent_path = namespace_arg.Parent().RelativeName()
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    labels_diff = labels_util.Diff(additions=args.labels)
    labels = labels_diff.Apply(
        fleetclient.messages.Namespace.LabelsValue, None
    ).GetOrNone()
    ns_labels_diff = labels_util.Diff(additions=args.namespace_labels)
    ns_labels = ns_labels_diff.Apply(
        fleetclient.messages.Namespace.NamespaceLabelsValue, None
    ).GetOrNone()
    return fleetclient.CreateScopeNamespace(
        name,
        namespace_path,
        parent_path,
        labels=labels,
        namespace_labels=ns_labels,
    )
