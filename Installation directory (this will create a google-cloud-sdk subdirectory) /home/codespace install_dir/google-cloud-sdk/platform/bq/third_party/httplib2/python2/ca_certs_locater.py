"""Custom locater for CA_CERTS files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

def get():
  """Locate the ca_certs.txt file.

  The httplib2 library will look for local ca_certs_locater module to override
  the default location for the ca_certs.txt file. We override it here to first
  try loading via resources, falling back to the traditional method if
  that fails.

  Returns:
    The file location returned as a string.
  """
  file_path = file_base_name = 'cacerts.txt'
  try:
    ca_certs = resources.GetResourceFilename(file_path)
  except (IOError, AttributeError, NameError):
    ca_certs = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), file_base_name)
  return ca_certs
