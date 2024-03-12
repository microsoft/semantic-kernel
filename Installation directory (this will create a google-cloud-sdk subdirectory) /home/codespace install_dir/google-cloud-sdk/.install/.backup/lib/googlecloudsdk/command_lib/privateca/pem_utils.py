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
"""PEM utilities for Privateca commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import exceptions

_PEM_CERT_RE = (
    r'-----BEGIN CERTIFICATE-----\n(?:[a-zA-Z0-9+/=]+\r?\n)+-----END '
    r'CERTIFICATE-----\s*')
_PEM_CHAIN_RE = re.compile(r'^({})+$'.format(_PEM_CERT_RE))


def ValidateAndParsePemChain(pem_chain):
  """Validates and parses a pem_chain string into a list of certs.

  Args:
    pem_chain: The string represting the pem_chain.

  Returns:
    A list of the certificates that make up the chain, in the same order
    as the input.

  Raises:
    exceptions.InvalidArgumentException if the pem_chain is in an unexpected
    format.
  """
  if not re.match(_PEM_CHAIN_RE, pem_chain):
    raise exceptions.InvalidArgumentException(
        'pem-chain', 'The pem_chain you provided was in an unexpected format.')

  certs = re.findall(_PEM_CERT_RE, pem_chain)

  for i in range(len(certs)):
    # Match service-generated certs, which always end with a single newline.
    certs[i] = certs[i].strip() + '\n'
  return certs


def PemChainForOutput(pem_chain):
  """Formats a pem chain for output with exactly 1 newline character between each cert.

  Args:
    pem_chain: The list of certificate strings to output

  Returns:
    The string value of all certificates appended together for output.
  """
  stripped_pem_chain = [cert.strip() for cert in pem_chain]
  return '\n'.join(stripped_pem_chain)
