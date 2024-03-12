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
"""Custom argument parsers for Certificate Manager commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
import re

from googlecloudsdk.calliope import arg_parsers


class PemCertificatesFile(arg_parsers.FileContents):
  """Reads file from provided path, extracts all PEM certificates from that file, and packs them into a message format appropriate for use in the Trust Store."""
  # Matches to PEM certificates.
  PEM_RE = re.compile(
      r'-----BEGIN CERTIFICATE-----\s*[\r\n|\r|\n]'
      r'[\w\s+/=]+[\r\n|\r|\n]'
      r'-----END CERTIFICATE-----',
      re.DOTALL | re.ASCII,
  )

  def __init__(self):
    super(PemCertificatesFile, self).__init__(binary=False)

  def __call__(self, name):
    file_contents = super(PemCertificatesFile, self).__call__(name)
    certs = self.PEM_RE.findall(file_contents)
    return [{'pemCertificate': cert} for cert in certs]


class PemCertificatesFilesList(arg_parsers.ArgList):
  """Reads PEM certificates from all provided files."""

  def __init__(self, custom_delim_char=';', **kwargs):
    """Initialize the parser.

    Args:
      custom_delim_char: What to split filenames list by.
      **kwargs: Passed verbatim to ArgList.
    """
    super(PemCertificatesFilesList, self).__init__(
        element_type=PemCertificatesFile(),
        custom_delim_char=custom_delim_char,
        **kwargs
    )

  def __call__(self, arg_value):
    value = super(PemCertificatesFilesList, self).__call__(arg_value)
    return list(itertools.chain.from_iterable(value))  # flatten
