# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest  # type: ignore

from google.auth import exceptions
import google.auth.transport._http_client
from tests.transport import compliance


class TestRequestResponse(compliance.RequestResponseTests):
    def make_request(self):
        return google.auth.transport._http_client.Request()

    def test_non_http(self):
        request = self.make_request()
        with pytest.raises(exceptions.TransportError) as excinfo:
            request(url="https://{}".format(compliance.NXDOMAIN), method="GET")

        assert excinfo.match("https")
