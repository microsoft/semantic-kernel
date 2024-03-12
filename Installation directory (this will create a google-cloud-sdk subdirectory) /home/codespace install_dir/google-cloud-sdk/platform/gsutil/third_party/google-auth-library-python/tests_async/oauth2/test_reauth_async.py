# Copyright 2021 Google LLC
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

import copy

import mock
import pytest  # type: ignore

from google.auth import exceptions
from google.oauth2 import _reauth_async
from google.oauth2 import reauth


MOCK_REQUEST = mock.AsyncMock(spec=["transport.Request"])
CHALLENGES_RESPONSE_TEMPLATE = {
    "status": "CHALLENGE_REQUIRED",
    "sessionId": "123",
    "challenges": [
        {
            "status": "READY",
            "challengeId": 1,
            "challengeType": "PASSWORD",
            "securityKey": {},
        }
    ],
}
CHALLENGES_RESPONSE_AUTHENTICATED = {
    "status": "AUTHENTICATED",
    "sessionId": "123",
    "encodedProofOfReauthToken": "new_rapt_token",
}


class MockChallenge(object):
    def __init__(self, name, locally_eligible, challenge_input):
        self.name = name
        self.is_locally_eligible = locally_eligible
        self.challenge_input = challenge_input

    def obtain_challenge_input(self, metadata):
        return self.challenge_input


@pytest.mark.asyncio
async def test__get_challenges():
    with mock.patch(
        "google.oauth2._client_async._token_endpoint_request"
    ) as mock_token_endpoint_request:
        await _reauth_async._get_challenges(MOCK_REQUEST, ["SAML"], "token")
        mock_token_endpoint_request.assert_called_with(
            MOCK_REQUEST,
            reauth._REAUTH_API + ":start",
            {"supportedChallengeTypes": ["SAML"]},
            access_token="token",
            use_json=True,
        )


@pytest.mark.asyncio
async def test__get_challenges_with_scopes():
    with mock.patch(
        "google.oauth2._client_async._token_endpoint_request"
    ) as mock_token_endpoint_request:
        await _reauth_async._get_challenges(
            MOCK_REQUEST, ["SAML"], "token", requested_scopes=["scope"]
        )
        mock_token_endpoint_request.assert_called_with(
            MOCK_REQUEST,
            reauth._REAUTH_API + ":start",
            {
                "supportedChallengeTypes": ["SAML"],
                "oauthScopesForDomainPolicyLookup": ["scope"],
            },
            access_token="token",
            use_json=True,
        )


@pytest.mark.asyncio
async def test__send_challenge_result():
    with mock.patch(
        "google.oauth2._client_async._token_endpoint_request"
    ) as mock_token_endpoint_request:
        await _reauth_async._send_challenge_result(
            MOCK_REQUEST, "123", "1", {"credential": "password"}, "token"
        )
        mock_token_endpoint_request.assert_called_with(
            MOCK_REQUEST,
            reauth._REAUTH_API + "/123:continue",
            {
                "sessionId": "123",
                "challengeId": "1",
                "action": "RESPOND",
                "proposalResponse": {"credential": "password"},
            },
            access_token="token",
            use_json=True,
        )


@pytest.mark.asyncio
async def test__run_next_challenge_not_ready():
    challenges_response = copy.deepcopy(CHALLENGES_RESPONSE_TEMPLATE)
    challenges_response["challenges"][0]["status"] = "STATUS_UNSPECIFIED"
    assert (
        await _reauth_async._run_next_challenge(
            challenges_response, MOCK_REQUEST, "token"
        )
        is None
    )


@pytest.mark.asyncio
async def test__run_next_challenge_not_supported():
    challenges_response = copy.deepcopy(CHALLENGES_RESPONSE_TEMPLATE)
    challenges_response["challenges"][0]["challengeType"] = "CHALLENGE_TYPE_UNSPECIFIED"
    with pytest.raises(exceptions.ReauthFailError) as excinfo:
        await _reauth_async._run_next_challenge(
            challenges_response, MOCK_REQUEST, "token"
        )
    assert excinfo.match(r"Unsupported challenge type CHALLENGE_TYPE_UNSPECIFIED")


@pytest.mark.asyncio
async def test__run_next_challenge_not_locally_eligible():
    mock_challenge = MockChallenge("PASSWORD", False, "challenge_input")
    with mock.patch(
        "google.oauth2.challenges.AVAILABLE_CHALLENGES", {"PASSWORD": mock_challenge}
    ):
        with pytest.raises(exceptions.ReauthFailError) as excinfo:
            await _reauth_async._run_next_challenge(
                CHALLENGES_RESPONSE_TEMPLATE, MOCK_REQUEST, "token"
            )
        assert excinfo.match(r"Challenge PASSWORD is not locally eligible")


@pytest.mark.asyncio
async def test__run_next_challenge_no_challenge_input():
    mock_challenge = MockChallenge("PASSWORD", True, None)
    with mock.patch(
        "google.oauth2.challenges.AVAILABLE_CHALLENGES", {"PASSWORD": mock_challenge}
    ):
        assert (
            await _reauth_async._run_next_challenge(
                CHALLENGES_RESPONSE_TEMPLATE, MOCK_REQUEST, "token"
            )
            is None
        )


@pytest.mark.asyncio
async def test__run_next_challenge_success():
    mock_challenge = MockChallenge("PASSWORD", True, {"credential": "password"})
    with mock.patch(
        "google.oauth2.challenges.AVAILABLE_CHALLENGES", {"PASSWORD": mock_challenge}
    ):
        with mock.patch(
            "google.oauth2._reauth_async._send_challenge_result"
        ) as mock_send_challenge_result:
            await _reauth_async._run_next_challenge(
                CHALLENGES_RESPONSE_TEMPLATE, MOCK_REQUEST, "token"
            )
            mock_send_challenge_result.assert_called_with(
                MOCK_REQUEST, "123", 1, {"credential": "password"}, "token"
            )


@pytest.mark.asyncio
async def test__obtain_rapt_authenticated():
    with mock.patch(
        "google.oauth2._reauth_async._get_challenges",
        return_value=CHALLENGES_RESPONSE_AUTHENTICATED,
    ):
        new_rapt_token = await _reauth_async._obtain_rapt(MOCK_REQUEST, "token", None)
        assert new_rapt_token == "new_rapt_token"


@pytest.mark.asyncio
async def test__obtain_rapt_authenticated_after_run_next_challenge():
    with mock.patch(
        "google.oauth2._reauth_async._get_challenges",
        return_value=CHALLENGES_RESPONSE_TEMPLATE,
    ):
        with mock.patch(
            "google.oauth2._reauth_async._run_next_challenge",
            side_effect=[
                CHALLENGES_RESPONSE_TEMPLATE,
                CHALLENGES_RESPONSE_AUTHENTICATED,
            ],
        ):
            with mock.patch("google.oauth2.reauth.is_interactive", return_value=True):
                assert (
                    await _reauth_async._obtain_rapt(MOCK_REQUEST, "token", None)
                    == "new_rapt_token"
                )


@pytest.mark.asyncio
async def test__obtain_rapt_unsupported_status():
    challenges_response = copy.deepcopy(CHALLENGES_RESPONSE_TEMPLATE)
    challenges_response["status"] = "STATUS_UNSPECIFIED"
    with mock.patch(
        "google.oauth2._reauth_async._get_challenges", return_value=challenges_response
    ):
        with pytest.raises(exceptions.ReauthFailError) as excinfo:
            await _reauth_async._obtain_rapt(MOCK_REQUEST, "token", None)
        assert excinfo.match(r"API error: STATUS_UNSPECIFIED")


@pytest.mark.asyncio
async def test__obtain_rapt_not_interactive():
    with mock.patch(
        "google.oauth2._reauth_async._get_challenges",
        return_value=CHALLENGES_RESPONSE_TEMPLATE,
    ):
        with mock.patch("google.oauth2.reauth.is_interactive", return_value=False):
            with pytest.raises(exceptions.ReauthFailError) as excinfo:
                await _reauth_async._obtain_rapt(MOCK_REQUEST, "token", None)
            assert excinfo.match(r"not in an interactive session")


@pytest.mark.asyncio
async def test__obtain_rapt_not_authenticated():
    with mock.patch(
        "google.oauth2._reauth_async._get_challenges",
        return_value=CHALLENGES_RESPONSE_TEMPLATE,
    ):
        with mock.patch("google.oauth2.reauth.RUN_CHALLENGE_RETRY_LIMIT", 0):
            with pytest.raises(exceptions.ReauthFailError) as excinfo:
                await _reauth_async._obtain_rapt(MOCK_REQUEST, "token", None)
            assert excinfo.match(r"Reauthentication failed")


@pytest.mark.asyncio
async def test_get_rapt_token():
    with mock.patch(
        "google.oauth2._client_async.refresh_grant",
        return_value=("token", None, None, None),
    ) as mock_refresh_grant:
        with mock.patch(
            "google.oauth2._reauth_async._obtain_rapt", return_value="new_rapt_token"
        ) as mock_obtain_rapt:
            assert (
                await _reauth_async.get_rapt_token(
                    MOCK_REQUEST,
                    "client_id",
                    "client_secret",
                    "refresh_token",
                    "token_uri",
                )
                == "new_rapt_token"
            )
            mock_refresh_grant.assert_called_with(
                request=MOCK_REQUEST,
                client_id="client_id",
                client_secret="client_secret",
                refresh_token="refresh_token",
                token_uri="token_uri",
                scopes=[reauth._REAUTH_SCOPE],
            )
            mock_obtain_rapt.assert_called_with(
                MOCK_REQUEST, "token", requested_scopes=None
            )


@pytest.mark.asyncio
async def test_refresh_grant_failed():
    with mock.patch(
        "google.oauth2._client_async._token_endpoint_request_no_throw"
    ) as mock_token_request:
        mock_token_request.return_value = (False, {"error": "Bad request"}, True)
        with pytest.raises(exceptions.RefreshError) as excinfo:
            await _reauth_async.refresh_grant(
                MOCK_REQUEST,
                "token_uri",
                "refresh_token",
                "client_id",
                "client_secret",
                scopes=["foo", "bar"],
                rapt_token="rapt_token",
            )
        assert excinfo.match(r"Bad request")
        assert excinfo.value.retryable
        mock_token_request.assert_called_with(
            MOCK_REQUEST,
            "token_uri",
            {
                "grant_type": "refresh_token",
                "client_id": "client_id",
                "client_secret": "client_secret",
                "refresh_token": "refresh_token",
                "scope": "foo bar",
                "rapt": "rapt_token",
            },
        )


@pytest.mark.asyncio
async def test_refresh_grant_success():
    with mock.patch(
        "google.oauth2._client_async._token_endpoint_request_no_throw"
    ) as mock_token_request:
        mock_token_request.side_effect = [
            (False, {"error": "invalid_grant", "error_subtype": "rapt_required"}, True),
            (True, {"access_token": "access_token"}, None),
        ]
        with mock.patch(
            "google.oauth2._reauth_async.get_rapt_token", return_value="new_rapt_token"
        ):
            assert await _reauth_async.refresh_grant(
                MOCK_REQUEST,
                "token_uri",
                "refresh_token",
                "client_id",
                "client_secret",
                enable_reauth_refresh=True,
            ) == (
                "access_token",
                "refresh_token",
                None,
                {"access_token": "access_token"},
                "new_rapt_token",
            )


@pytest.mark.asyncio
async def test_refresh_grant_reauth_refresh_disabled():
    with mock.patch(
        "google.oauth2._client_async._token_endpoint_request_no_throw"
    ) as mock_token_request:
        mock_token_request.side_effect = [
            (
                False,
                {"error": "invalid_grant", "error_subtype": "rapt_required"},
                False,
            ),
            (True, {"access_token": "access_token"}, None),
        ]
        with pytest.raises(exceptions.RefreshError) as excinfo:
            assert await _reauth_async.refresh_grant(
                MOCK_REQUEST, "token_uri", "refresh_token", "client_id", "client_secret"
            )
        assert excinfo.match(r"Reauthentication is needed")
        assert not excinfo.value.retryable
