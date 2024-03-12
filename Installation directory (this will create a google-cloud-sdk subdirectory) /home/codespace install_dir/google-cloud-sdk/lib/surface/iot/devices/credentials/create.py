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

"""`gcloud iot devices credentials create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import devices
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Add a new credential to a device.

  A device may have at most 3 credentials.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To add an RSA public key wrapped in an X.509v3 certificate to a device, run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device --path=/path/to/cert.pem --type=rsa-x509-pem

          To add a public key for the ECDSA algorithm to a device, run:

            $ {command} --region=us-central1 --registry=my-registry --device=my-device --path=/path/to/ec_public.pem --type=es256-pem
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddDeviceResourceArg(parser,
                                       'for which to create credentials',
                                       positional=False)
    flags.AddDeviceCredentialFlagsToParser(parser, combine_flags=False)

  def Run(self, args):
    client = devices.DevicesClient()

    device_ref = args.CONCEPTS.device.Parse()
    new_credential = util.ParseCredential(
        args.path, args.type, args.expiration_time, messages=client.messages)

    credentials = client.Get(device_ref).credentials
    if len(credentials) >= util.MAX_PUBLIC_KEY_NUM:
      raise util.InvalidPublicKeySpecificationError(
          'Cannot create a new public key credential for this device; '
          'maximum {} keys are allowed.'.format(util.MAX_PUBLIC_KEY_NUM))
    credentials.append(new_credential)
    response = client.Patch(device_ref, credentials=credentials)
    log.CreatedResource(device_ref.Name(), 'credentials for device')
    return response
