# Copyright 2020 Google LLC
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
import pytest

from google.auth import jwt
import google.oauth2.id_token


def test_fetch_id_token(http_request):
    audience = "https://pubsub.googleapis.com"
    token = google.oauth2.id_token.fetch_id_token(http_request, audience)

    _, payload, _, _ = jwt._unverified_decode(token)
    assert payload["aud"] == audience
