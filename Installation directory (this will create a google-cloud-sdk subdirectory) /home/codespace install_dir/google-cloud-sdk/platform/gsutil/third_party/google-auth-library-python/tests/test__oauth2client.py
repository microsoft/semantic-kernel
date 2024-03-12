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

import datetime
import os
import sys

import mock
import pytest  # type: ignore
from six.moves import reload_module

try:
    import oauth2client.client  # type: ignore
    import oauth2client.contrib.gce  # type: ignore
    import oauth2client.service_account  # type: ignore
except ImportError:  # pragma: NO COVER
    pytest.skip(
        "Skipping oauth2client tests since oauth2client is not installed.",
        allow_module_level=True,
    )

from google.auth import _oauth2client


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SERVICE_ACCOUNT_JSON_FILE = os.path.join(DATA_DIR, "service_account.json")


def test__convert_oauth2_credentials():
    old_credentials = oauth2client.client.OAuth2Credentials(
        "access_token",
        "client_id",
        "client_secret",
        "refresh_token",
        datetime.datetime.min,
        "token_uri",
        "user_agent",
        scopes="one two",
    )

    new_credentials = _oauth2client._convert_oauth2_credentials(old_credentials)

    assert new_credentials.token == old_credentials.access_token
    assert new_credentials._refresh_token == old_credentials.refresh_token
    assert new_credentials._client_id == old_credentials.client_id
    assert new_credentials._client_secret == old_credentials.client_secret
    assert new_credentials._token_uri == old_credentials.token_uri
    assert new_credentials.scopes == old_credentials.scopes


def test__convert_service_account_credentials():
    old_class = oauth2client.service_account.ServiceAccountCredentials
    old_credentials = old_class.from_json_keyfile_name(SERVICE_ACCOUNT_JSON_FILE)

    new_credentials = _oauth2client._convert_service_account_credentials(
        old_credentials
    )

    assert (
        new_credentials.service_account_email == old_credentials.service_account_email
    )
    assert new_credentials._signer.key_id == old_credentials._private_key_id
    assert new_credentials._token_uri == old_credentials.token_uri


def test__convert_service_account_credentials_with_jwt():
    old_class = oauth2client.service_account._JWTAccessCredentials
    old_credentials = old_class.from_json_keyfile_name(SERVICE_ACCOUNT_JSON_FILE)

    new_credentials = _oauth2client._convert_service_account_credentials(
        old_credentials
    )

    assert (
        new_credentials.service_account_email == old_credentials.service_account_email
    )
    assert new_credentials._signer.key_id == old_credentials._private_key_id
    assert new_credentials._token_uri == old_credentials.token_uri


def test__convert_gce_app_assertion_credentials():
    old_credentials = oauth2client.contrib.gce.AppAssertionCredentials(
        email="some_email"
    )

    new_credentials = _oauth2client._convert_gce_app_assertion_credentials(
        old_credentials
    )

    assert (
        new_credentials.service_account_email == old_credentials.service_account_email
    )


@pytest.fixture
def mock_oauth2client_gae_imports(mock_non_existent_module):
    mock_non_existent_module("google.appengine.api.app_identity")
    mock_non_existent_module("google.appengine.ext.ndb")
    mock_non_existent_module("google.appengine.ext.webapp.util")
    mock_non_existent_module("webapp2")


@mock.patch("google.auth.app_engine.app_identity")
def test__convert_appengine_app_assertion_credentials(
    app_identity, mock_oauth2client_gae_imports
):

    import oauth2client.contrib.appengine  # type: ignore

    service_account_id = "service_account_id"
    old_credentials = oauth2client.contrib.appengine.AppAssertionCredentials(
        scope="one two", service_account_id=service_account_id
    )

    new_credentials = _oauth2client._convert_appengine_app_assertion_credentials(
        old_credentials
    )

    assert new_credentials.scopes == ["one", "two"]
    assert new_credentials._service_account_id == old_credentials.service_account_id


class FakeCredentials(object):
    pass


def test_convert_success():
    convert_function = mock.Mock(spec=["__call__"])
    conversion_map_patch = mock.patch.object(
        _oauth2client, "_CLASS_CONVERSION_MAP", {FakeCredentials: convert_function}
    )
    credentials = FakeCredentials()

    with conversion_map_patch:
        result = _oauth2client.convert(credentials)

    convert_function.assert_called_once_with(credentials)
    assert result == convert_function.return_value


def test_convert_not_found():
    with pytest.raises(ValueError) as excinfo:
        _oauth2client.convert("a string is not a real credentials class")

    assert excinfo.match("Unable to convert")


@pytest.fixture
def reset__oauth2client_module():
    """Reloads the _oauth2client module after a test."""
    reload_module(_oauth2client)


def test_import_has_app_engine(
    mock_oauth2client_gae_imports, reset__oauth2client_module
):
    reload_module(_oauth2client)
    assert _oauth2client._HAS_APPENGINE


def test_import_without_oauth2client(monkeypatch, reset__oauth2client_module):
    monkeypatch.setitem(sys.modules, "oauth2client", None)
    with pytest.raises(ImportError) as excinfo:
        reload_module(_oauth2client)

    assert excinfo.match("oauth2client")
