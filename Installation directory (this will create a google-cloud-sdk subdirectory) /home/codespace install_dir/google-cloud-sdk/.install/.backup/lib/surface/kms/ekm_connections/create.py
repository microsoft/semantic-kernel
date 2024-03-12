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
"""Create a new ekm connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import certs
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps
from googlecloudsdk.command_lib.kms import resource_args


class Create(base.CreateCommand):
  r"""Create a new ekm connection.

  Creates a new connection within the given location.

  ## EXAMPLES

  The following command creates an ekm connection named `laplace` within the
  location `us-central1`:

    $ {command} laplace \
        --location=us-central1 \
        --service-directory-service="foo" \
        --endpoint-filter="foo > bar" \
        --hostname="hostname.foo" \
        --server-certificates-files=foo.pem,bar.pem

  The following command creates an ekm connection named `laplace` within the
  location `us-central1` in `cloud-kms` key management mode with the required
  crypto-space-path :

    $ {command} laplace \
        --location=us-central1 \
        --service-directory-service="foo" \
        --endpoint-filter="foo > bar" \
        --hostname="hostname.foo" \
        --key-management-mode=cloud-kms
        --crypto-space-path="foo"
        --server-certificates-files=foo.pem,bar.pem
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsEkmConnectionResourceArgForKMS(parser, True,
                                                       'ekm_connection')
    flags.AddServiceDirectoryServiceFlag(parser, True)
    flags.AddEndpointFilterFlag(parser)
    flags.AddHostnameFlag(parser, True)
    flags.AddServerCertificatesFilesFlag(parser, True)
    flags.AddKeyManagementModeFlags(parser)
    parser.display_info.AddCacheUpdater(flags.EkmConnectionCompleter)

  def _CreateRequest(self, args):
    messages = cloudkms_base.GetMessagesModule()

    ekm_connection_ref = args.CONCEPTS.ekm_connection.Parse()
    parent_ref = ekm_connection_ref.Parent()

    if args.key_management_mode == 'cloud-kms':
      if not args.crypto_space_path:
        raise exceptions.RequiredArgumentException(
            '--crypto-space-path',
            'Must be supplied when --key-management-mode is cloud-kms.')

    certificate_list = []
    for cert_file in args.server_certificates_files:
      try:
        certificate_list.append(
            messages.Certificate(rawDer=certs.GetDerCertificate(cert_file)))
      except Exception as e:
        raise exceptions.BadArgumentException(
            '--server-certificates-files',
            'Error while attempting to read file {} : {}'.format(cert_file, e))

    req = messages.CloudkmsProjectsLocationsEkmConnectionsCreateRequest(
        parent=parent_ref.RelativeName(),
        ekmConnectionId=ekm_connection_ref.Name(),
        ekmConnection=messages.EkmConnection(
            keyManagementMode=maps.KEY_MANAGEMENT_MODE_MAPPER.GetEnumForChoice(
                args.key_management_mode),
            cryptoSpacePath=args.crypto_space_path,
            serviceResolvers=[
                messages.ServiceResolver(
                    serviceDirectoryService=args.service_directory_service,
                    endpointFilter=args.endpoint_filter,
                    hostname=args.hostname,
                    serverCertificates=certificate_list)
            ]))

    return req

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    return client.projects_locations_ekmConnections.Create(
        self._CreateRequest(args))
