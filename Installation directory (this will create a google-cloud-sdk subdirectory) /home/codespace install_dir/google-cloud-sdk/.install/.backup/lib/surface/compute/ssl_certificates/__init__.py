# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Commands for reading and manipulating SSL certificates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class SslCertificates(base.Group):
  """List, create, and delete Compute Engine SSL certificate resources.

  List, create, and delete Compute Engine SSL certificate resources that you can
  use to encrypt traffic between clients and a load balancer. An SSL
  certificate resource contains both a private key and the SSL certificate
  itself. You refer to the SSL certificate resource in the target SSL proxy or
  the target HTTPS proxy.

  The relevant load balancer types are Proxy Network Load Balancers and
  Application Load Balancers. For more information, see:
  [SSL certificates
  documentation](https://cloud.google.com/load-balancing/docs/ssl-certificates)
  """

SslCertificates.category = base.LOAD_BALANCING_CATEGORY

SslCertificates.detailed_help = {
    'DESCRIPTION': """
        Read and manipulate SSL certificates that encrypt
        traffic between clients and a load balancer. The relevant
        load balancer types are Application Load Balancers and proxy Network Load Balancers.

        For more information about SSL certificates, see the
        [SSL certificates documentation](https://cloud.google.com/load-balancing/docs/ssl-certificates).

        See also: [SSL certificates API](https://cloud.google.com/compute/docs/reference/rest/v1/sslCertificates)
        and [regional SSL certificates API](https://cloud.google.com/compute/docs/reference/rest/v1/regionSslCertificates).
    """,
}


