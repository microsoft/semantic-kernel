# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Context managers for patching libraries for use in PAR files."""



import os
import pkgutil
import shutil
import tempfile

import httplib2



def _monkey_patch_httplib2(extract_dir):
  """Patch things so that httplib2 works properly in a PAR.

  Manually extract certificates to file to make OpenSSL happy and avoid error:
     ssl.SSLError: [Errno 185090050] _ssl.c:344: error:0B084002:x509 ...

  Args:
    extract_dir: the directory into which we extract the necessary files.
  """
  if os.path.isfile(httplib2.CA_CERTS):
    # Not inside of a PAR file, so don't bother.
    return
  cacerts_contents = pkgutil.get_data('httplib2', 'cacerts.txt')
  cacerts_filename = os.path.join(extract_dir, 'cacerts.txt')
  with open(cacerts_filename, 'wb') as f:
    f.write(cacerts_contents)
  httplib2.CA_CERTS = cacerts_filename


class Httplib2(object):

  def __init__(self):
    self._tmpdir = tempfile.mkdtemp()

  # __enter__ and __exit__ allow use as a context manager.
  def __enter__(self):
    _monkey_patch_httplib2(self._tmpdir)
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    shutil.rmtree(self._tmpdir)
