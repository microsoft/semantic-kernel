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

# Prerequisites:
# Make sure to run the setup in scripts/setup_external_accounts.sh
# and copy the logged constant strings (_AUDIENCE_OIDC, _AUDIENCE_AWS)
# into this file before running this test suite.
# Once that is done, this test can be run indefinitely.
#
# The only requirement for this test suite to run is to set the environment
# variable GOOGLE_APPLICATION_CREDENTIALS to point to the expected service
# account keys whose email is referred to in the setup script.
#
# This script follows the following logic.
# OIDC provider (file-sourced and url-sourced credentials):
# Use the service account keys to generate a Google ID token using the
# iamcredentials generateIdToken API, using the default STS audience.
# This will use the service account client ID as the sub field of the token.
# This OIDC token will be used as the external subject token to be exchanged
# for a Google access token via GCP STS endpoint and then to impersonate the
# original service account key.


import datetime
import json
import os
import socket
from tempfile import NamedTemporaryFile
import threading
import time

import sys
import google.auth
from google.auth import _helpers
from googleapiclient import discovery
from six.moves import BaseHTTPServer
from google.oauth2 import service_account
import pytest
from mock import patch

# Populate values from the output of scripts/setup_external_accounts.sh.
_AUDIENCE_OIDC = "//iam.googleapis.com/projects/79992041559/locations/global/workloadIdentityPools/pool-73wslmxn/providers/oidc-73wslmxn"
_AUDIENCE_AWS = "//iam.googleapis.com/projects/79992041559/locations/global/workloadIdentityPools/pool-73wslmxn/providers/aws-73wslmxn"
_ROLE_AWS = "arn:aws:iam::077071391996:role/ci-python-test"


def dns_access_direct(request, project_id):
    # First, get the default credentials.
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform.read-only"],
        request=request,
    )

    # Apply the default credentials to the headers to make the request.
    headers = {}
    credentials.apply(headers)
    response = request(
        url="https://dns.googleapis.com/dns/v1/projects/{}".format(project_id),
        headers=headers,
    )

    if response.status == 200:
        return response.data


def dns_access_client_library(_, project_id):
    service = discovery.build("dns", "v1")
    request = service.projects().get(project=project_id)
    return request.execute()


@pytest.fixture(params=[dns_access_direct, dns_access_client_library])
def dns_access(request, http_request, service_account_info):
    # Fill in the fixtures on the functions,
    # so that we don't have to fill in the parameters manually.
    def wrapper():
        return request.param(http_request, service_account_info["project_id"])

    yield wrapper


@pytest.fixture
def oidc_credentials(service_account_file, http_request):
    result = service_account.IDTokenCredentials.from_service_account_file(
        service_account_file, target_audience=_AUDIENCE_OIDC
    )
    result.refresh(http_request)
    yield result


@pytest.fixture
def service_account_info(service_account_file):
    with open(service_account_file) as f:
        yield json.load(f)


@pytest.fixture
def aws_oidc_credentials(
    service_account_file, service_account_info, authenticated_request
):
    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    result = authenticated_request(credentials)(
        url="https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateIdToken".format(
            service_account_info["client_email"]
        ),
        method="POST",
        body=json.dumps(
            {"audience": service_account_info["client_id"], "includeEmail": True}
        ),
    )
    assert result.status == 200

    yield json.loads(result.data)["token"]


# Our external accounts tests involve setting up some preconditions, setting a
# credential file, and then making sure that our client libraries can work with
# the set credentials.
def get_project_dns(dns_access, credential_data):
    with NamedTemporaryFile() as credfile:
        credfile.write(json.dumps(credential_data).encode("utf-8"))
        credfile.flush()

        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": credfile.name}):
            # If our setup and credential file are correct,
            # discovery.build should be able to establish these as the default credentials.
            return dns_access()


def get_xml_value_by_tagname(data, tagname):
    startIndex = data.index("<{}>".format(tagname))
    if startIndex >= 0:
        endIndex = data.index("</{}>".format(tagname), startIndex)
        if endIndex > startIndex:
            return data[startIndex + len(tagname) + 2 : endIndex]


# This test makes sure that setting an accesible credential file
# works to allow access to Google resources.
def test_file_based_external_account(oidc_credentials, dns_access):
    with NamedTemporaryFile() as tmpfile:
        tmpfile.write(oidc_credentials.token.encode("utf-8"))
        tmpfile.flush()

        assert get_project_dns(
            dns_access,
            {
                "type": "external_account",
                "audience": _AUDIENCE_OIDC,
                "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
                "token_url": "https://sts.googleapis.com/v1/token",
                "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
                    oidc_credentials.service_account_email
                ),
                "credential_source": {
                    "file": tmpfile.name,
                },
            },
        )


# This test makes sure that setting a token lifetime works
# for service account impersonation.
def test_file_based_external_account_with_configure_token_lifetime(
    oidc_credentials, dns_access
):
    with NamedTemporaryFile() as tmpfile:
        tmpfile.write(oidc_credentials.token.encode("utf-8"))
        tmpfile.flush()

        assert get_project_dns(
            dns_access,
            {
                "type": "external_account",
                "audience": _AUDIENCE_OIDC,
                "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
                "token_url": "https://sts.googleapis.com/v1/token",
                "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
                    oidc_credentials.service_account_email
                ),
                "service_account_impersonation": {
                    "token_lifetime_seconds": 2800,
                },
                "credential_source": {
                    "file": tmpfile.name,
                },
            },
        )


def test_configurable_token_lifespan(oidc_credentials, http_request):
    TOKEN_LIFETIME_SECONDS = 2800
    BUFFER_SECONDS = 5

    def check_impersonation_expiration():
        # First, get the default credentials.
        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform.read-only"],
            request=http_request,
        )

        utcmax = _helpers.utcnow() + datetime.timedelta(seconds=TOKEN_LIFETIME_SECONDS)
        utcmin = utcmax - datetime.timedelta(seconds=BUFFER_SECONDS)
        assert utcmin < credentials._impersonated_credentials.expiry <= utcmax

        return True

    with NamedTemporaryFile() as tmpfile:
        tmpfile.write(oidc_credentials.token.encode("utf-8"))
        tmpfile.flush()

        assert get_project_dns(
            check_impersonation_expiration,
            {
                "type": "external_account",
                "audience": _AUDIENCE_OIDC,
                "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
                "token_url": "https://sts.googleapis.com/v1/token",
                "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
                    oidc_credentials.service_account_email
                ),
                "service_account_impersonation": {
                    "token_lifetime_seconds": TOKEN_LIFETIME_SECONDS,
                },
                "credential_source": {
                    "file": tmpfile.name,
                },
            },
        )


# This test makes sure that setting up an http server to provide credentials
# works to allow access to Google resources.
def test_url_based_external_account(dns_access, oidc_credentials, service_account_info):
    class TestResponseHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers["my-header"] != "expected-value":
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "missing header"}).encode("utf-8")
                )
            elif self.path != "/token":
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "incorrect token path"}).encode("utf-8")
                )
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"access_token": oidc_credentials.token}).encode("utf-8")
                )

    class TestHTTPServer(BaseHTTPServer.HTTPServer, object):
        def __init__(self):
            self.port = self._find_open_port()
            super(TestHTTPServer, self).__init__(("", self.port), TestResponseHandler)

        @staticmethod
        def _find_open_port():
            s = socket.socket()
            s.bind(("", 0))
            return s.getsockname()[1]

        # This makes sure that the server gets shut down when this variable leaves its "with" block
        # The python3 HttpServer has __enter__ and __exit__ methods, but python2 does not.
        # By redefining the __enter__ and __exit__ methods, we ensure that python2 and python3 act similarly
        def __exit__(self, *args):
            self.shutdown()

        def __enter__(self):
            return self

    with TestHTTPServer() as server:
        threading.Thread(target=server.serve_forever).start()

        assert get_project_dns(
            dns_access,
            {
                "type": "external_account",
                "audience": _AUDIENCE_OIDC,
                "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
                "token_url": "https://sts.googleapis.com/v1/token",
                "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
                    oidc_credentials.service_account_email
                ),
                "credential_source": {
                    "url": "http://localhost:{}/token".format(server.port),
                    "headers": {"my-header": "expected-value"},
                    "format": {
                        "type": "json",
                        "subject_token_field_name": "access_token",
                    },
                },
            },
        )


# AWS provider tests for AWS credentials
# The test suite will also run tests for AWS credentials. This works as
# follows. (Note prequisite setup is needed. This is documented in
# setup_external_accounts.sh).
# - iamcredentials:generateIdToken is used to generate a Google ID token using
#   the service account access token. The service account client_id is used as
#   audience.
# - AWS STS AssumeRoleWithWebIdentity API is used to exchange this token for
#   temporary AWS security credentials for a specified AWS ARN role.
# - AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY and AWS_SESSION_TOKEN
#   environment variables are set using these credentials before the test is
#   run simulating an AWS VM.
# - The test can now be run.
def test_aws_based_external_account(
    aws_oidc_credentials, service_account_info, dns_access, http_request
):

    response = http_request(
        url=(
            "https://sts.amazonaws.com/"
            "?Action=AssumeRoleWithWebIdentity"
            "&Version=2011-06-15"
            "&DurationSeconds=3600"
            "&RoleSessionName=python-test"
            "&RoleArn={}"
            "&WebIdentityToken={}"
        ).format(_ROLE_AWS, aws_oidc_credentials)
    )
    assert response.status == 200

    # The returned data is in XML, but loading an XML parser would be overkill.
    # Searching the return text manually for the start and finish tag.
    data = response.data.decode("utf-8")

    with patch.dict(
        os.environ,
        {
            "AWS_REGION": "us-east-2",
            "AWS_ACCESS_KEY_ID": get_xml_value_by_tagname(data, "AccessKeyId"),
            "AWS_SECRET_ACCESS_KEY": get_xml_value_by_tagname(data, "SecretAccessKey"),
            "AWS_SESSION_TOKEN": get_xml_value_by_tagname(data, "SessionToken"),
        },
    ):
        assert get_project_dns(
            dns_access,
            {
                "type": "external_account",
                "audience": _AUDIENCE_AWS,
                "subject_token_type": "urn:ietf:params:aws:token-type:aws4_request",
                "token_url": "https://sts.googleapis.com/v1/token",
                "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
                    service_account_info["client_email"]
                ),
                "credential_source": {
                    "environment_id": "aws1",
                    "regional_cred_verification_url": "https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
                },
            },
        )


# This test makes sure that setting up an executable to provide credentials
# works to allow access to Google resources.
def test_pluggable_external_account(oidc_credentials, service_account_info, dns_access):
    now = datetime.datetime.now()
    unix_seconds = time.mktime(now.timetuple())
    expiration_time = (unix_seconds + 1 * 60 * 60) * 1000
    credential = {
        "success": True,
        "version": 1,
        "expiration_time": expiration_time,
        "token_type": "urn:ietf:params:oauth:token-type:jwt",
        "id_token": oidc_credentials.token,
    }

    tmpfile = NamedTemporaryFile(delete=True)
    with open(tmpfile.name, "w") as f:
        f.write("#!/bin/bash\n")
        f.write('echo "{}"\n'.format(json.dumps(credential).replace('"', '\\"')))
    tmpfile.file.close()

    os.chmod(tmpfile.name, 0o777)
    assert get_project_dns(
        dns_access,
        {
            "type": "external_account",
            "audience": _AUDIENCE_OIDC,
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "token_url": "https://sts.googleapis.com/v1/token",
            "service_account_impersonation_url": "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
                oidc_credentials.service_account_email
            ),
            "credential_source": {
                "executable": {
                    "command": tmpfile.name,
                }
            },
        },
    )
