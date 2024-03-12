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
"""`gcloud certificate-manager maps list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificate_maps
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util
from googlecloudsdk.core.resource import resource_transform

_FORMAT = """\
table(
    name.scope(certificateMaps),
    gclbTargets.gclbTargetsToString(undefined='-'):label=ENDPOINTS,
    description,
    createTime.date('%Y-%m-%d %H:%M:%S %Oz', undefined='-')
)
"""


def _TransformGclbTargets(targets, undefined=''):
  r"""Transforms GclbTargets to more compact form.

  It uses following format: IP_1:port_1\nIP_2:port_2\n...IP_n:port_n.

  Args:
    targets: GclbTargets API representation.
    undefined: str, value to be returned if no IP:port pair is found.

  Returns:
    String representation to be shown in table view.
  """
  if not targets:
    return undefined
  result = []
  for target in targets:
    ip_configs = resource_transform.GetKeyValue(target, 'ipConfigs', None)
    if ip_configs is None:
      return undefined
    for ip_config in ip_configs:
      ip_address = resource_transform.GetKeyValue(ip_config, 'ipAddress', None)
      ports = resource_transform.GetKeyValue(ip_config, 'ports', None)
      if ip_address is None or ports is None:
        continue
      for port in ports:
        result.append('{}:{}'.format(ip_address, port))
  return '\n'.join(result) if result else undefined


_TRANSFORMS = {
    'gclbTargetsToString': _TransformGclbTargets,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List certificate maps.

  List Certificate Manager maps in the project.

  ## EXAMPLES

  To list all certificate maps in the project, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to list maps for')
    parser.display_info.AddUriFunc(util.CertificateMapUriFunc)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddTransforms(_TRANSFORMS)

  def Run(self, args):
    client = certificate_maps.CertificateMapClient()
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(location_ref, args.limit, args.page_size)
