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
"""Command to create an enterprise-certificate configuration file for Linux."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.auth import enterprise_certificate_config
from googlecloudsdk.command_lib.auth.flags import AddCommonEnterpriseCertConfigFlags


class CreateLinuxConfig(base.CreateCommand):
  """Create an enterprise-certificate configuration file for Linux.

  This command creates a configuration file used by gcloud to use the
  enterprise-certificate-proxy component for mTLS.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent(
          """\
          To create a credential configuration run:

            $ {command} --module=$PATH_TO_PKCS11_MODULE --slot=$PKCS11_SLOT_ID --label=$PKCS11_OBJECT_LABEL --user-pin=$PKCS11_USER_PIN
          """
      ),
  }

  @classmethod
  def Args(cls, parser):
    AddCommonEnterpriseCertConfigFlags(parser)
    parser.add_argument(
        '--module',
        help='The full file path to the PKCS #11 module.',
        required=True,
    )

    parser.add_argument(
        '--slot',
        help='The PKCS #11 slot containing the target credentials.',
        required=True,
    )

    parser.add_argument(
        '--label',
        help='The PKCS #11 label for the target credentials. '
        + 'The certificate, public key, and private key MUST have '
        + 'the same label. enterprise-certificate-proxy will use all '
        + 'three objects.',
        required=True,
    )

    parser.add_argument(
        '--user-pin',
        help='The user pin used to login to the PKCS #11 module. '
        + 'If there is no user pin leave this field empty.',
    )

  def Run(self, args):
    enterprise_certificate_config.create_config(
        enterprise_certificate_config.ConfigType.PKCS11, **vars(args)
    )
