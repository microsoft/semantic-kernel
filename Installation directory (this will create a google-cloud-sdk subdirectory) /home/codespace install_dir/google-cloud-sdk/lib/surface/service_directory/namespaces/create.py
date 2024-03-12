# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""`gcloud service-directory namespaces create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.service_directory import namespaces
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.service_directory import flags
from googlecloudsdk.command_lib.service_directory import resource_args
from googlecloudsdk.command_lib.service_directory import util
from googlecloudsdk.core import log

_RESOURCE_TYPE = 'namespace'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Creates a namespace."""

  detailed_help = {
      'EXAMPLES':
          """\
          To create a Service Directory namespace, run:

            $ {command} my-namespace --location=us-east1 --labels=a=b,c=d
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddNamespaceResourceArg(
        parser,
        """to create. The namespace id must be 1-63 characters long and match
        the regular expression `[a-z](?:[-a-z0-9]{0,61}[a-z0-9])?` which means
        the first character must be a lowercase letter, and all following
        characters must be a dash, lowercase letter, or digit, except the last
        character, which cannot be a dash.""")
    flags.AddLabelsFlag(parser, _RESOURCE_TYPE)

  def Run(self, args):
    client = namespaces.NamespacesClient(self.GetReleaseTrack())
    namespace_ref = args.CONCEPTS.namespace.Parse()
    labels = util.ParseLabelsArg(args.labels, self.GetReleaseTrack())

    result = client.Create(namespace_ref, labels)
    log.CreatedResource(namespace_ref.namespacesId, _RESOURCE_TYPE)

    return result

  def GetReleaseTrack(self):
    return base.ReleaseTrack.GA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Creates a namespace."""

  def GetReleaseTrack(self):
    return base.ReleaseTrack.BETA
