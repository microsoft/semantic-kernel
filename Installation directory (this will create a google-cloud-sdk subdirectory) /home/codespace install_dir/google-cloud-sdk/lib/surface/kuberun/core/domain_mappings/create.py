# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Create a domain mapping for a KubeRun service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core import exceptions

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To map a domain to a service in the default namespace, run:

            $ {command} --service=SERVICE --domain=DOMAIN

        To map a domain to a service in a specific namespace ``NAMESPACE'', run:

            $ {command} --service=SERVICE --domain=DOMAIN --namespace=NAMESPACE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(kuberun_command.KubeRunCommand):
  """Creates a domain mapping."""

  @classmethod
  def Args(cls, parser):
    super(Create, cls).Args(parser)
    parser.add_argument(
        '--service', help='The service to map to a domain.', required=True)
    parser.add_argument(
        '--domain',
        help='The domain mapping to map the service to.',
        required=True)
    parser.display_info.AddFormat("""table(
        name:label=NAME,
        type:label="RECORD TYPE",
        rrdata:label=CONTENTS)""")

  def BuildKubeRunArgs(self, args):
    return ['--service', args.service, '--domain', args.domain] + super(
        Create, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'domain-mappings', 'create']

  def SuccessResult(self, out, args):
    if out:
      mapping = json.loads(out)
      status = mapping.get('status', {})
      records = status.get('resourceRecords', [{}])
      spec = mapping.get('spec', {})
      default_name = spec.get('routeName')
      for r in records:
        r['name'] = r.get('name') or default_name
      return records
    else:
      raise exceptions.Error('Could not map domain [{}] to service [{}]'.format(
          args.domain, args.service))


Create.detailed_help = _DETAILED_HELP
Create.flags = [flags.NamespaceFlag(), flags.ClusterConnectionFlags()]
