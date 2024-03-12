# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""IAM completers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import resources


class IamRolesCompleter(completers.ListCommandCompleter):
  """An IAM role completer for a resource argument.

  The Complete() method override bypasses the completion cache.

  Attributes:
    _resource_dest: The argparse Namespace dest string for the resource
      argument that has the roles.
    _resource_collection: The resource argument collection.
  """

  def __init__(self, resource_dest=None, resource_collection=None, **kwargs):
    super(IamRolesCompleter, self).__init__(**kwargs)
    self._resource_dest = resource_dest
    self._resource_collection = resource_collection

  def GetListCommand(self, parameter_info):
    resource_ref = resources.REGISTRY.Parse(
        parameter_info.GetValue(self._resource_dest),
        collection=self._resource_collection,
        default_resolver=parameter_info.GetValue)
    resource_uri = resource_ref.SelfLink()
    return ['beta', 'iam', 'list-grantable-roles', '--quiet',
            '--flatten=name', '--format=disable', resource_uri]

  def Complete(self, prefix, parameter_info):
    """Bypasses the cache and returns completions matching prefix."""
    command = self.GetListCommand(parameter_info)
    items = self.GetAllItems(command, parameter_info)
    return [
        item for item in items or []
        if item is not None and item.startswith(prefix)
    ]


class IamServiceAccountCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(IamServiceAccountCompleter, self).__init__(
        list_command=('iam service-accounts list --quiet '
                      '--flatten=email --format=disable'),
        **kwargs)
