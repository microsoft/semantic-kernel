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
"""Command group for Namespace."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import deprecation_utils


@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='447.0.0',
    remove=True,
    alt_command='gcloud fleet scopes namespaces',
)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Namespace(base.Group):
  """Fleet namespaces are the fleet equivalent of k8s cluster namespaces.

  This command group allows for manipulation of fleet namespaces.

  ## EXAMPLES

  Manage fleet namespaces:

    $ {command} --help

  Manage RBAC RoleBindings in a fleet namespace:

    $ {command} rbacrolebindings --help

  """

  category = base.COMPUTE_CATEGORY
