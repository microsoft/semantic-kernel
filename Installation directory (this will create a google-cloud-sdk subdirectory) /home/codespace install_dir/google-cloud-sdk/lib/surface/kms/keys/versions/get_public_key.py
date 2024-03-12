# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Get the PEM-format public key for a given version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log


class GetPublicKey(base.DescribeCommand):
  r"""Get the public key for a given version.

  Returns the PEM-format public key for the specified asymmetric key version.

  The optional flag `output-file` indicates the path to store PEM. If not
  specified. PEM will be printed to stdout.


  ## EXAMPLES

  The following command saves the public key for CryptoKey `frodo` Version 2
  to '/tmp/my/pem.file':

    $ {command} 2 \
    --key=frodo \
    --keyring=fellowship \
    --location=us-east1 \
    --output-file=/tmp/my/pem.file
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyVersionResourceArgument(parser, 'to get public key')
    flags.AddOutputFileFlag(parser, 'to store PEM')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    version_ref = flags.ParseCryptoKeyVersionName(args)
    if not version_ref.Name():
      raise exceptions.InvalidArgumentException('version',
                                                'version id must be non-empty.')

    resp = client.projects_locations_keyRings_cryptoKeys_cryptoKeyVersions.GetPublicKey(  # pylint: disable=line-too-long
        messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCryptoKeyVersionsGetPublicKeyRequest(  # pylint: disable=line-too-long
            name=version_ref.RelativeName()))

    log.WriteToFileOrStdout(
        args.output_file if args.output_file else '-',
        resp.pem,
        overwrite=True,
        binary=False,
        private=True)
