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
"""`gcloud certificate-manager certificates list` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificates
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util

_FORMAT = """\
table(
    name.scope(certificates),
    san_dnsnames.sansToString(undefined=''):label=SUBJECT_ALTERNATIVE_NAMES,
    description,
    scope,
    expireTime.date('%Y-%m-%d %H:%M:%S %Oz', undefined=''),
    createTime.date('%Y-%m-%d %H:%M:%S %Oz', undefined=''),
    updateTime.date('%Y-%m-%d %H:%M:%S %Oz', undefined='')
)
"""


def _TransformSANs(sans, undefined=''):
  r"""Joins list of SANs with \n as separator..

  Args:
    sans: list of SANs.
    undefined: str, value to be returned if no SANs are found.

  Returns:
    String representation to be shown in table view.
  """
  return '\n'.join(sans) if sans else undefined


_TRANSFORMS = {
    'sansToString': _TransformSANs,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List certificates.

  List Certificate Manager certificates in the project.

  ## EXAMPLES

  To list all certificates in the project, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to list certificates for')
    parser.display_info.AddUriFunc(util.CertificateUriFunc)
    parser.display_info.AddFormat(_FORMAT)
    parser.display_info.AddTransforms(_TRANSFORMS)

  def Run(self, args):
    client = certificates.CertificateClient()
    location_ref = args.CONCEPTS.location.Parse()
    return client.List(location_ref, args.limit, args.page_size)
