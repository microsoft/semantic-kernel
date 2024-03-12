# Copyright 2022 Google Inc.
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

from google.auth import exceptions  # type:ignore


@pytest.fixture(
    params=[
        exceptions.GoogleAuthError,
        exceptions.TransportError,
        exceptions.RefreshError,
        exceptions.UserAccessTokenError,
        exceptions.DefaultCredentialsError,
        exceptions.MutualTLSChannelError,
        exceptions.OAuthError,
        exceptions.ReauthFailError,
        exceptions.ReauthSamlChallengeFailError,
    ]
)
def retryable_exception(request):
    return request.param


@pytest.fixture(params=[exceptions.ClientCertError])
def non_retryable_exception(request):
    return request.param


def test_default_retryable_exceptions(retryable_exception):
    assert not retryable_exception().retryable


@pytest.mark.parametrize("retryable", [True, False])
def test_retryable_exceptions(retryable_exception, retryable):
    retryable_exception = retryable_exception(retryable=retryable)
    assert retryable_exception.retryable == retryable


@pytest.mark.parametrize("retryable", [True, False])
def test_non_retryable_exceptions(non_retryable_exception, retryable):
    non_retryable_exception = non_retryable_exception(retryable=retryable)
    assert not non_retryable_exception.retryable
