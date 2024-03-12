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
"""Client certificate authorization supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.calliope import base
from googlecloudsdk.generated_clients.apis import apis_map

IAP_TUNNEL_SERVICE = 'iap_tunnel'
START_IAP_TUNNEL_COMMAND = 'gcloud compute start-iap-tunnel'


def _GenerateMtlsDisallowedServices():
  """Generates a table for services which do NOT support client certificate."""
  disallowlist = []
  for service, versions in apis_map.MAP.items():
    for version, api_def in versions.items():
      if not api_def.enable_mtls:
        disallowlist.append((service, version))

  disallowlist.sort()
  table_out = io.StringIO()

  table_out.write("""
SERVICE | VERSION | NOTES
 --- | --- | ---
 --- | --- | ---
""")
  for service, version in disallowlist:
    table_out.write('{} | {} |\n'.format(service, version))
  table_out.write('--- | --- | ---\n')

  return table_out.getvalue()


class ClientCert(base.TopicCommand):
  """Client certificate authorization supplementary help."""
  detailed_help = {
      'DESCRIPTION':
          """\
Client certificate authorization supplementary help.

Device Certificate Authorization (DCA) enables Context-aware access to
identify devices by their X.509 certificates. DCA for Google Cloud
APIs is the second in a series of releases that provides
administrators the capability to protect access to their Google
Cloud resources with device certificates. This feature builds
on top of the existing Context-aware access suite (Endpoint
Verification, Access Context Manager, and VPC Service Controls) and
ensures that only users on trusted devices with a Google-generated
certificate are able to access Google Cloud APIs. This
provides a stronger signal of device identity (device certificate
verification), and protects users from credential theft to accidental
loss by only granting access when credentials and the original device
certificate are presented.

To use this feature, organizations can follow the instructions below to
install an endpoint verification agent to devices:

  * Automatically deploy endpoint verification (https://support.google.com/a/answer/9007320#)
    * Via Chrome Policy for the extension
    * 3rd party image/software distribution tools for the Native Helper on macOS
      and Windows
  * Let users install endpoint verification themselves from the Chrome Webstore
    (https://support.google.com/a/users/answer/9018161#install)
    * Users would also be prompted to install the Native Helper as well

For a greater level of security, operating system key stores can be used to store client
certificate objects. This feature is enabled by using [enterprise-certificate-proxy](https://github.com/googleapis/enterprise-certificate-proxy).

enterprise-certificate-proxy can be installed by running `$ gcloud components install enterprise-certificate-proxy`.

In order to use enterprise-certificate-proxy it must first be configured. By default the configuration should be written to `~/.config/gcloud/certificate_config.json`.

The enterprise-certificate-proxy schema is documented on the [GitHub project page](https://github.com/googleapis/enterprise-certificate-proxy#certificate-configuration). Each operating system that gcloud supports uses a different key store. The certificate_config may contain multiple OS configurations.

Provisioning the key stores is not in scope for this document.

Run ``$ gcloud config set context_aware/use_client_certificate True''
so that the gcloud CLI will load the certificate and send it to services.
Some services do not support client certificate authorization yet.
When the gcloud CLI sends requests to such services, the client certificate will
be ignored.

The following is the list of services which do NOT support client certificate
authorization in the installed version of the gcloud CLI.

{disallowlist}

See https://cloud.google.com/sdk/gcloud/reference/topic/client-certificate
for the support list for the latest version of the gcloud CLI. Please upgrade
the gcloud command-line tool if necessary.

Note: {iap_tunnel_service} is a special service gcloud CLI uses to create the
IAP tunnel. For example, ``{start_iap_tunnel_command}'' can start a tunnel to
Cloud Identity-Aware Proxy through which another process can create a connection
(e.g. SSH, RDP) to a Google Compute Engine instance. Client certificate
authorization is supported in tunnel creation.""".format(
    disallowlist=_GenerateMtlsDisallowedServices(),
    iap_tunnel_service=IAP_TUNNEL_SERVICE,
    start_iap_tunnel_command=START_IAP_TUNNEL_COMMAND)
  }
