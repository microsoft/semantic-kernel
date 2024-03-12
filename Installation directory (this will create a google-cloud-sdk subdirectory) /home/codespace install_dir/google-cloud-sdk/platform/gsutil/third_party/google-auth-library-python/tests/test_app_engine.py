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

import mock
import pytest  # type: ignore

from google.auth import app_engine


class _AppIdentityModule(object):
    """The interface of the App Idenity app engine module.
    See https://cloud.google.com/appengine/docs/standard/python/refdocs
    /google.appengine.api.app_identity.app_identity
    """

    def get_application_id(self):
        raise NotImplementedError()

    def sign_blob(self, bytes_to_sign, deadline=None):
        raise NotImplementedError()

    def get_service_account_name(self, deadline=None):
        raise NotImplementedError()

    def get_access_token(self, scopes, service_account_id=None):
        raise NotImplementedError()


@pytest.fixture
def app_identity(monkeypatch):
    """Mocks the app_identity module for google.auth.app_engine."""
    app_identity_module = mock.create_autospec(_AppIdentityModule, instance=True)
    monkeypatch.setattr(app_engine, "app_identity", app_identity_module)
    yield app_identity_module


def test_get_project_id(app_identity):
    app_identity.get_application_id.return_value = mock.sentinel.project
    assert app_engine.get_project_id() == mock.sentinel.project


@mock.patch.object(app_engine, "app_identity", new=None)
def test_get_project_id_missing_apis():
    with pytest.raises(EnvironmentError) as excinfo:
        assert app_engine.get_project_id()

    assert excinfo.match(r"App Engine APIs are not available")


class TestSigner(object):
    def test_key_id(self, app_identity):
        app_identity.sign_blob.return_value = (
            mock.sentinel.key_id,
            mock.sentinel.signature,
        )

        signer = app_engine.Signer()

        assert signer.key_id is None

    def test_sign(self, app_identity):
        app_identity.sign_blob.return_value = (
            mock.sentinel.key_id,
            mock.sentinel.signature,
        )

        signer = app_engine.Signer()
        to_sign = b"123"

        signature = signer.sign(to_sign)

        assert signature == mock.sentinel.signature
        app_identity.sign_blob.assert_called_with(to_sign)


class TestCredentials(object):
    @mock.patch.object(app_engine, "app_identity", new=None)
    def test_missing_apis(self):
        with pytest.raises(EnvironmentError) as excinfo:
            app_engine.Credentials()

        assert excinfo.match(r"App Engine APIs are not available")

    def test_default_state(self, app_identity):
        credentials = app_engine.Credentials()

        # Not token acquired yet
        assert not credentials.valid
        # Expiration hasn't been set yet
        assert not credentials.expired
        # Scopes are required
        assert not credentials.scopes
        assert not credentials.default_scopes
        assert credentials.requires_scopes
        assert not credentials.quota_project_id

    def test_with_scopes(self, app_identity):
        credentials = app_engine.Credentials()

        assert not credentials.scopes
        assert credentials.requires_scopes

        scoped_credentials = credentials.with_scopes(["email"])

        assert scoped_credentials.has_scopes(["email"])
        assert not scoped_credentials.requires_scopes

    def test_with_default_scopes(self, app_identity):
        credentials = app_engine.Credentials()

        assert not credentials.scopes
        assert not credentials.default_scopes
        assert credentials.requires_scopes

        scoped_credentials = credentials.with_scopes(
            scopes=None, default_scopes=["email"]
        )

        assert scoped_credentials.has_scopes(["email"])
        assert not scoped_credentials.requires_scopes

    def test_with_quota_project(self, app_identity):
        credentials = app_engine.Credentials()

        assert not credentials.scopes
        assert not credentials.quota_project_id

        quota_project_creds = credentials.with_quota_project("project-foo")

        assert quota_project_creds.quota_project_id == "project-foo"

    def test_service_account_email_implicit(self, app_identity):
        app_identity.get_service_account_name.return_value = (
            mock.sentinel.service_account_email
        )
        credentials = app_engine.Credentials()

        assert credentials.service_account_email == mock.sentinel.service_account_email
        assert app_identity.get_service_account_name.called

    def test_service_account_email_explicit(self, app_identity):
        credentials = app_engine.Credentials(
            service_account_id=mock.sentinel.service_account_email
        )

        assert credentials.service_account_email == mock.sentinel.service_account_email
        assert not app_identity.get_service_account_name.called

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh(self, utcnow, app_identity):
        token = "token"
        ttl = 643942923
        app_identity.get_access_token.return_value = token, ttl
        credentials = app_engine.Credentials(
            scopes=["email"], default_scopes=["profile"]
        )

        credentials.refresh(None)

        app_identity.get_access_token.assert_called_with(
            credentials.scopes, credentials._service_account_id
        )
        assert credentials.token == token
        assert credentials.expiry == datetime.datetime(1990, 5, 29, 1, 2, 3)
        assert credentials.valid
        assert not credentials.expired

    @mock.patch("google.auth._helpers.utcnow", return_value=datetime.datetime.min)
    def test_refresh_with_default_scopes(self, utcnow, app_identity):
        token = "token"
        ttl = 643942923
        app_identity.get_access_token.return_value = token, ttl
        credentials = app_engine.Credentials(default_scopes=["email"])

        credentials.refresh(None)

        app_identity.get_access_token.assert_called_with(
            credentials.default_scopes, credentials._service_account_id
        )
        assert credentials.token == token
        assert credentials.expiry == datetime.datetime(1990, 5, 29, 1, 2, 3)
        assert credentials.valid
        assert not credentials.expired

    def test_sign_bytes(self, app_identity):
        app_identity.sign_blob.return_value = (
            mock.sentinel.key_id,
            mock.sentinel.signature,
        )
        credentials = app_engine.Credentials()
        to_sign = b"123"

        signature = credentials.sign_bytes(to_sign)

        assert signature == mock.sentinel.signature
        app_identity.sign_blob.assert_called_with(to_sign)

    def test_signer(self, app_identity):
        credentials = app_engine.Credentials()
        assert isinstance(credentials.signer, app_engine.Signer)

    def test_signer_email(self, app_identity):
        credentials = app_engine.Credentials()
        assert credentials.signer_email == credentials.service_account_email
