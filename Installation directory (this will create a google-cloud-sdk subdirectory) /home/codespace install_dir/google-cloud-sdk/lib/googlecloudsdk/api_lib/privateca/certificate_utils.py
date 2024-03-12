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
"""Certificate utilities for Privateca commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import random
import string

from googlecloudsdk.api_lib.privateca import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import times


def GetCertificateBySerialNum(ca_pool_ref, serial_num):
  """Obtains a certificate by serial num by filtering all certs in a CA pool.

  Args:
    ca_pool_ref: The resource reference to the CA pool.
    serial_num: The serial number to lookup the certificate by.

  Returns:
    The certificate message of the corresponding serial number. Ignores
    duplicate certificates.

  Raises:
    exceptions.InvalidArgumentError if there were no certificates with the
    specified CA pool and serial number.
  """
  cert_filter = (
      'certificate_description.subject_description.hex_serial_number:{}'.format(
          serial_num
      )
  )
  client = base.GetClientInstance(api_version='v1')
  messages = base.GetMessagesModule(api_version='v1')

  response = client.projects_locations_caPools_certificates.List(
      messages.PrivatecaProjectsLocationsCaPoolsCertificatesListRequest(
          parent=ca_pool_ref.RelativeName(), filter=cert_filter
      )
  )

  if not response.certificates:
    raise exceptions.InvalidArgumentException(
        '--serial-number',
        'The serial number specified does not exist under the CA pool [{}]]'
        .format(ca_pool_ref.RelativeName()),
    )

  return response.certificates[0]


def GenerateCertId():
  """Generate a certificate id with the date and two length 3 alphanum strings.

  E.G. YYYYMMDD-ABC-DEF.

  Returns:
    The generated certificate id string.
  """
  # Avoid name collisions in certificate id generation. Normal random.choice
  # seeds on system time, which might not be sufficiently random of a seed.
  # SystemRandom uses other sources from the OS to generate the random ID.
  sys_rng = random.SystemRandom()
  alphanum = string.ascii_uppercase + string.digits
  alphanum_rand1 = ''.join(sys_rng.choice(alphanum) for i in range(3))
  alphanum_rand2 = ''.join(sys_rng.choice(alphanum) for i in range(3))
  date_str = times.FormatDateTime(times.Now(), '%Y%m%d')
  return '{}-{}-{}'.format(date_str, alphanum_rand1, alphanum_rand2)
