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
"""`gcloud certificate-manager maps entries list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.certificate_manager import certificate_map_entries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util

_FORMAT = """\
table(
    name.scope(certificateMapEntries),
    description,
    hostname,
    matcher,
    certificates.certNamesToIDs(undefined=''),
    state,
    createTime.date('%Y-%m-%d %H:%M:%S %Oz', undefined='')
)
"""

_CERT_NAME_REGEX = 'projects/([a-z0-9-]{1,63})/locations/([a-z0-9-]{1,63})/certificates/([a-z0-9-]{1,63})'


def _TransformCertificateNames(cert_names, undefined=''):
  """Transforms fully qualified cert names to their IDs."""
  if not cert_names:
    return undefined
  result = []
  for name in cert_names:
    match = re.match(_CERT_NAME_REGEX, name)
    result.append(match.group(3) if match else name)
  return '\n'.join(result) if result else undefined


_TRANSFORMS = {
    'certNamesToIDs': _TransformCertificateNames,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List certificate map entries.

  List Certificate Manager certificate map entries in the certificate map.

  ## EXAMPLES

  To list all certificate map entries in the certificate map, run:

    $ {command} --map=simple-map
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateMapResourceArg(
        parser, 'to list map entries for', positional=False)
    parser.display_info.AddUriFunc(util.CertificateMapEntryUriFunc)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddTransforms(_TRANSFORMS)

  def Run(self, args):
    client = certificate_map_entries.CertificateMapEntryClient()
    map_ref = args.CONCEPTS.map.Parse()
    return client.List(map_ref, args.limit, args.page_size)
