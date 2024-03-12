# Copyright 2018 Google Inc. All Rights Reserved.
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
"""An httplib2.Http extending and composing an inner httplib2.Http transport.
"""


import httplib2


class NestedTransport(httplib2.Http):
  """Extends and composes an inner httplib2.Http transport."""

  def __init__(self, source_transport):
    self.source_transport = source_transport

  def __getstate__(self):
    raise NotImplementedError()

  def __setstate__(self, state):
    # Don't want to bother reflectivley instantiating the source_transport.
    # Don't serialize your transports.
    raise NotImplementedError()

  def add_credentials(self, *args, **kwargs):
    self.source_transport.add_credentials(*args, **kwargs)

  def add_certificate(self, *args, **kwargs):
    self.source_transport.add_certificate(*args, **kwargs)

  def clear_credentials(self):
    self.source_transport.clear_credentials()

  def request(self, *args, **kwargs):
    return self.source_transport.request(*args, **kwargs)
