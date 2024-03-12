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

import datetime
import json
import os

import mock
import pytest  # type: ignore
from six.moves import http_client
from six.moves import urllib

from google.auth import _helpers
from google.auth import aws
from google.auth import environment_vars
from google.auth import exceptions
from google.auth import transport


CLIENT_ID = "username"
CLIENT_SECRET = "password"
# Base64 encoding of "username:password".
BASIC_AUTH_ENCODING = "dXNlcm5hbWU6cGFzc3dvcmQ="
SERVICE_ACCOUNT_EMAIL = "service-1234@service-name.iam.gserviceaccount.com"
SERVICE_ACCOUNT_IMPERSONATION_URL_BASE = (
    "https://us-east1-iamcredentials.googleapis.com"
)
SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE = "/v1/projects/-/serviceAccounts/{}:generateAccessToken".format(
    SERVICE_ACCOUNT_EMAIL
)
SERVICE_ACCOUNT_IMPERSONATION_URL = (
    SERVICE_ACCOUNT_IMPERSONATION_URL_BASE + SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE
)
QUOTA_PROJECT_ID = "QUOTA_PROJECT_ID"
SCOPES = ["scope1", "scope2"]
TOKEN_URL = "https://sts.googleapis.com/v1/token"
TOKEN_INFO_URL = "https://sts.googleapis.com/v1/introspect"
SUBJECT_TOKEN_TYPE = "urn:ietf:params:aws:token-type:aws4_request"
AUDIENCE = "//iam.googleapis.com/projects/123456/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID"
REGION_URL = "http://169.254.169.254/latest/meta-data/placement/availability-zone"
IMDSV2_SESSION_TOKEN_URL = "http://169.254.169.254/latest/api/token"
SECURITY_CREDS_URL = "http://169.254.169.254/latest/meta-data/iam/security-credentials"
REGION_URL_IPV6 = "http://[fd00:ec2::254]/latest/meta-data/placement/availability-zone"
IMDSV2_SESSION_TOKEN_URL_IPV6 = "http://[fd00:ec2::254]/latest/api/token"
SECURITY_CREDS_URL_IPV6 = (
    "http://[fd00:ec2::254]/latest/meta-data/iam/security-credentials"
)
CRED_VERIFICATION_URL = (
    "https://sts.{region}.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15"
)
# Sample AWS security credentials to be used with tests that require a session token.
ACCESS_KEY_ID = "ASIARD4OQDT6A77FR3CL"
SECRET_ACCESS_KEY = "Y8AfSaucF37G4PpvfguKZ3/l7Id4uocLXxX0+VTx"
TOKEN = "IQoJb3JpZ2luX2VjEIz//////////wEaCXVzLWVhc3QtMiJGMEQCIH7MHX/Oy/OB8OlLQa9GrqU1B914+iMikqWQW7vPCKlgAiA/Lsv8Jcafn14owfxXn95FURZNKaaphj0ykpmS+Ki+CSq0AwhlEAAaDDA3NzA3MTM5MTk5NiIMx9sAeP1ovlMTMKLjKpEDwuJQg41/QUKx0laTZYjPlQvjwSqS3OB9P1KAXPWSLkliVMMqaHqelvMF/WO/glv3KwuTfQsavRNs3v5pcSEm4SPO3l7mCs7KrQUHwGP0neZhIKxEXy+Ls//1C/Bqt53NL+LSbaGv6RPHaX82laz2qElphg95aVLdYgIFY6JWV5fzyjgnhz0DQmy62/Vi8pNcM2/VnxeCQ8CC8dRDSt52ry2v+nc77vstuI9xV5k8mPtnaPoJDRANh0bjwY5Sdwkbp+mGRUJBAQRlNgHUJusefXQgVKBCiyJY4w3Csd8Bgj9IyDV+Azuy1jQqfFZWgP68LSz5bURyIjlWDQunO82stZ0BgplKKAa/KJHBPCp8Qi6i99uy7qh76FQAqgVTsnDuU6fGpHDcsDSGoCls2HgZjZFPeOj8mmRhFk1Xqvkbjuz8V1cJk54d3gIJvQt8gD2D6yJQZecnuGWd5K2e2HohvCc8Fc9kBl1300nUJPV+k4tr/A5R/0QfEKOZL1/k5lf1g9CREnrM8LVkGxCgdYMxLQow1uTL+QU67AHRRSp5PhhGX4Rek+01vdYSnJCMaPhSEgcLqDlQkhk6MPsyT91QMXcWmyO+cAZwUPwnRamFepuP4K8k2KVXs/LIJHLELwAZ0ekyaS7CptgOqS7uaSTFG3U+vzFZLEnGvWQ7y9IPNQZ+Dffgh4p3vF4J68y9049sI6Sr5d5wbKkcbm8hdCDHZcv4lnqohquPirLiFQ3q7B17V9krMPu3mz1cg4Ekgcrn/E09NTsxAqD8NcZ7C7ECom9r+X3zkDOxaajW6hu3Az8hGlyylDaMiFfRbBJpTIlxp7jfa7CxikNgNtEKLH9iCzvuSg2vhA=="
# To avoid json.dumps() differing behavior from one version to other,
# the JSON payload is hardcoded.
REQUEST_PARAMS = '{"KeySchema":[{"KeyType":"HASH","AttributeName":"Id"}],"TableName":"TestTable","AttributeDefinitions":[{"AttributeName":"Id","AttributeType":"S"}],"ProvisionedThroughput":{"WriteCapacityUnits":5,"ReadCapacityUnits":5}}'
# Each tuple contains the following entries:
# region, time, credentials, original_request, signed_request

VALID_TOKEN_URLS = [
    "https://sts.googleapis.com",
    "https://us-east-1.sts.googleapis.com",
    "https://US-EAST-1.sts.googleapis.com",
    "https://sts.us-east-1.googleapis.com",
    "https://sts.US-WEST-1.googleapis.com",
    "https://us-east-1-sts.googleapis.com",
    "https://US-WEST-1-sts.googleapis.com",
    "https://us-west-1-sts.googleapis.com/path?query",
    "https://sts-us-east-1.p.googleapis.com",
]
INVALID_TOKEN_URLS = [
    "https://iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "https://",
    "http://sts.googleapis.com",
    "https://st.s.googleapis.com",
    "https://us-eas\t-1.sts.googleapis.com",
    "https:/us-east-1.sts.googleapis.com",
    "https://US-WE/ST-1-sts.googleapis.com",
    "https://sts-us-east-1.googleapis.com",
    "https://sts-US-WEST-1.googleapis.com",
    "testhttps://us-east-1.sts.googleapis.com",
    "https://us-east-1.sts.googleapis.comevil.com",
    "https://us-east-1.us-east-1.sts.googleapis.com",
    "https://us-ea.s.t.sts.googleapis.com",
    "https://sts.googleapis.comevil.com",
    "hhttps://us-east-1.sts.googleapis.com",
    "https://us- -1.sts.googleapis.com",
    "https://-sts.googleapis.com",
    "https://us-east-1.sts.googleapis.com.evil.com",
    "https://sts.pgoogleapis.com",
    "https://p.googleapis.com",
    "https://sts.p.com",
    "http://sts.p.googleapis.com",
    "https://xyz-sts.p.googleapis.com",
    "https://sts-xyz.123.p.googleapis.com",
    "https://sts-xyz.p1.googleapis.com",
    "https://sts-xyz.p.foo.com",
    "https://sts-xyz.p.foo.googleapis.com",
]
VALID_SERVICE_ACCOUNT_IMPERSONATION_URLS = [
    "https://iamcredentials.googleapis.com",
    "https://us-east-1.iamcredentials.googleapis.com",
    "https://US-EAST-1.iamcredentials.googleapis.com",
    "https://iamcredentials.us-east-1.googleapis.com",
    "https://iamcredentials.US-WEST-1.googleapis.com",
    "https://us-east-1-iamcredentials.googleapis.com",
    "https://US-WEST-1-iamcredentials.googleapis.com",
    "https://us-west-1-iamcredentials.googleapis.com/path?query",
    "https://iamcredentials-us-east-1.p.googleapis.com",
]
INVALID_SERVICE_ACCOUNT_IMPERSONATION_URLS = [
    "https://sts.googleapis.com",
    "iamcredentials.googleapis.com",
    "https://",
    "http://iamcredentials.googleapis.com",
    "https://iamcre.dentials.googleapis.com",
    "https://us-eas\t-1.iamcredentials.googleapis.com",
    "https:/us-east-1.iamcredentials.googleapis.com",
    "https://US-WE/ST-1-iamcredentials.googleapis.com",
    "https://iamcredentials-us-east-1.googleapis.com",
    "https://iamcredentials-US-WEST-1.googleapis.com",
    "testhttps://us-east-1.iamcredentials.googleapis.com",
    "https://us-east-1.iamcredentials.googleapis.comevil.com",
    "https://us-east-1.us-east-1.iamcredentials.googleapis.com",
    "https://us-ea.s.t.iamcredentials.googleapis.com",
    "https://iamcredentials.googleapis.comevil.com",
    "hhttps://us-east-1.iamcredentials.googleapis.com",
    "https://us- -1.iamcredentials.googleapis.com",
    "https://-iamcredentials.googleapis.com",
    "https://us-east-1.iamcredentials.googleapis.com.evil.com",
    "https://iamcredentials.pgoogleapis.com",
    "https://p.googleapis.com",
    "https://iamcredentials.p.com",
    "http://iamcredentials.p.googleapis.com",
    "https://xyz-iamcredentials.p.googleapis.com",
    "https://iamcredentials-xyz.123.p.googleapis.com",
    "https://iamcredentials-xyz.p1.googleapis.com",
    "https://iamcredentials-xyz.p.foo.com",
    "https://iamcredentials-xyz.p.foo.googleapis.com",
]
TEST_FIXTURES = [
    # GET request (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=b27ccfbfa7df52a200ff74193ca6e32d4b48b8856fab7ebf1c595d0670a7e470",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with relative path (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-relative-relative.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-relative-relative.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/foo/bar/../..",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/foo/bar/../..",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=b27ccfbfa7df52a200ff74193ca6e32d4b48b8856fab7ebf1c595d0670a7e470",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with /./ path (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-slash-dot-slash.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-slash-dot-slash.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/./",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/./",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=b27ccfbfa7df52a200ff74193ca6e32d4b48b8856fab7ebf1c595d0670a7e470",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with pointless dot path (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-slash-pointless-dot.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-slash-pointless-dot.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/./foo",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/./foo",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=910e4d6c9abafaf87898e1eb4c929135782ea25bb0279703146455745391e63a",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with utf8 path (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-utf8.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-utf8.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/%E1%88%B4",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/%E1%88%B4",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=8d6634c189aa8c75c2e51e106b6b5121bed103fdb351f7d7d4381c738823af74",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with duplicate query key (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla-query-order-key-case.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla-query-order-key-case.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/?foo=Zoo&foo=aha",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/?foo=Zoo&foo=aha",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=be7148d34ebccdc6423b19085378aa0bee970bdc61d144bd1a8c48c33079ab09",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with duplicate out of order query key (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla-query-order-value.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla-query-order-value.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/?foo=b&foo=a",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/?foo=b&foo=a",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=feb926e49e382bec75c9d7dcb2a1b6dc8aa50ca43c25d2bc51143768c0875acc",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with utf8 query (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla-ut8-query.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-vanilla-ut8-query.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "GET",
            "url": "https://host.foo.com/?{}=bar".format(
                urllib.parse.unquote("%E1%88%B4")
            ),
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/?{}=bar".format(
                urllib.parse.unquote("%E1%88%B4")
            ),
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=6fb359e9a05394cc7074e0feb42573a2601abc0c869a953e8c5c12e4e01f1a8c",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # POST request with sorted headers (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-header-key-sort.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-header-key-sort.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "POST",
            "url": "https://host.foo.com/",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT", "ZOO": "zoobar"},
        },
        {
            "url": "https://host.foo.com/",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host;zoo, Signature=b7a95a52518abbca0964a999a880429ab734f35ebbf1235bd79a5de87756dc4a",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
                "ZOO": "zoobar",
            },
        },
    ),
    # POST request with upper case header value from AWS Python test harness.
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-header-value-case.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-header-value-case.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "POST",
            "url": "https://host.foo.com/",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT", "zoo": "ZOOBAR"},
        },
        {
            "url": "https://host.foo.com/",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host;zoo, Signature=273313af9d0c265c531e11db70bbd653f3ba074c1009239e8559d3987039cad7",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
                "zoo": "ZOOBAR",
            },
        },
    ),
    # POST request with header and no body (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-header-value-trim.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/get-header-value-trim.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "POST",
            "url": "https://host.foo.com/",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT", "p": "phfft"},
        },
        {
            "url": "https://host.foo.com/",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host;p, Signature=debf546796015d6f6ded8626f5ce98597c33b47b9164cf6b17b4642036fcb592",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
                "p": "phfft",
            },
        },
    ),
    # POST request with body and no header (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-x-www-form-urlencoded.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-x-www-form-urlencoded.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "POST",
            "url": "https://host.foo.com/",
            "headers": {
                "Content-Type": "application/x-www-form-urlencoded",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
            "data": "foo=bar",
        },
        {
            "url": "https://host.foo.com/",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=content-type;date;host, Signature=5a15b22cf462f047318703b92e6f4f38884e4a7ab7b1d6426ca46a8bd1c26cbc",
                "host": "host.foo.com",
                "Content-Type": "application/x-www-form-urlencoded",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
            "data": "foo=bar",
        },
    ),
    # POST request with querystring (AWS botocore tests).
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-vanilla-query.req
    # https://github.com/boto/botocore/blob/879f8440a4e9ace5d3cf145ce8b3d5e5ffb892ef/tests/unit/auth/aws4_testsuite/post-vanilla-query.sreq
    (
        "us-east-1",
        "2011-09-09T23:36:00Z",
        {
            "access_key_id": "AKIDEXAMPLE",
            "secret_access_key": "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY",
        },
        {
            "method": "POST",
            "url": "https://host.foo.com/?foo=bar",
            "headers": {"date": "Mon, 09 Sep 2011 23:36:00 GMT"},
        },
        {
            "url": "https://host.foo.com/?foo=bar",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20110909/us-east-1/host/aws4_request, SignedHeaders=date;host, Signature=b6e3b79003ce0743a491606ba1035a804593b0efb1e20a11cba83f8c25a57a92",
                "host": "host.foo.com",
                "date": "Mon, 09 Sep 2011 23:36:00 GMT",
            },
        },
    ),
    # GET request with session token credentials.
    (
        "us-east-2",
        "2020-08-11T06:55:22Z",
        {
            "access_key_id": ACCESS_KEY_ID,
            "secret_access_key": SECRET_ACCESS_KEY,
            "security_token": TOKEN,
        },
        {
            "method": "GET",
            "url": "https://ec2.us-east-2.amazonaws.com?Action=DescribeRegions&Version=2013-10-15",
        },
        {
            "url": "https://ec2.us-east-2.amazonaws.com?Action=DescribeRegions&Version=2013-10-15",
            "method": "GET",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential="
                + ACCESS_KEY_ID
                + "/20200811/us-east-2/ec2/aws4_request, SignedHeaders=host;x-amz-date;x-amz-security-token, Signature=631ea80cddfaa545fdadb120dc92c9f18166e38a5c47b50fab9fce476e022855",
                "host": "ec2.us-east-2.amazonaws.com",
                "x-amz-date": "20200811T065522Z",
                "x-amz-security-token": TOKEN,
            },
        },
    ),
    # POST request with session token credentials.
    (
        "us-east-2",
        "2020-08-11T06:55:22Z",
        {
            "access_key_id": ACCESS_KEY_ID,
            "secret_access_key": SECRET_ACCESS_KEY,
            "security_token": TOKEN,
        },
        {
            "method": "POST",
            "url": "https://sts.us-east-2.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
        },
        {
            "url": "https://sts.us-east-2.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential="
                + ACCESS_KEY_ID
                + "/20200811/us-east-2/sts/aws4_request, SignedHeaders=host;x-amz-date;x-amz-security-token, Signature=73452984e4a880ffdc5c392355733ec3f5ba310d5e0609a89244440cadfe7a7a",
                "host": "sts.us-east-2.amazonaws.com",
                "x-amz-date": "20200811T065522Z",
                "x-amz-security-token": TOKEN,
            },
        },
    ),
    # POST request with computed x-amz-date and no data.
    (
        "us-east-2",
        "2020-08-11T06:55:22Z",
        {"access_key_id": ACCESS_KEY_ID, "secret_access_key": SECRET_ACCESS_KEY},
        {
            "method": "POST",
            "url": "https://sts.us-east-2.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
        },
        {
            "url": "https://sts.us-east-2.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential="
                + ACCESS_KEY_ID
                + "/20200811/us-east-2/sts/aws4_request, SignedHeaders=host;x-amz-date, Signature=d095ba304919cd0d5570ba8a3787884ee78b860f268ed040ba23831d55536d56",
                "host": "sts.us-east-2.amazonaws.com",
                "x-amz-date": "20200811T065522Z",
            },
        },
    ),
    # POST request with session token and additional headers/data.
    (
        "us-east-2",
        "2020-08-11T06:55:22Z",
        {
            "access_key_id": ACCESS_KEY_ID,
            "secret_access_key": SECRET_ACCESS_KEY,
            "security_token": TOKEN,
        },
        {
            "method": "POST",
            "url": "https://dynamodb.us-east-2.amazonaws.com/",
            "headers": {
                "Content-Type": "application/x-amz-json-1.0",
                "x-amz-target": "DynamoDB_20120810.CreateTable",
            },
            "data": REQUEST_PARAMS,
        },
        {
            "url": "https://dynamodb.us-east-2.amazonaws.com/",
            "method": "POST",
            "headers": {
                "Authorization": "AWS4-HMAC-SHA256 Credential="
                + ACCESS_KEY_ID
                + "/20200811/us-east-2/dynamodb/aws4_request, SignedHeaders=content-type;host;x-amz-date;x-amz-security-token;x-amz-target, Signature=fdaa5b9cc9c86b80fe61eaf504141c0b3523780349120f2bd8145448456e0385",
                "host": "dynamodb.us-east-2.amazonaws.com",
                "x-amz-date": "20200811T065522Z",
                "Content-Type": "application/x-amz-json-1.0",
                "x-amz-target": "DynamoDB_20120810.CreateTable",
                "x-amz-security-token": TOKEN,
            },
            "data": REQUEST_PARAMS,
        },
    ),
]


class TestRequestSigner(object):
    @pytest.mark.parametrize(
        "region, time, credentials, original_request, signed_request", TEST_FIXTURES
    )
    @mock.patch("google.auth._helpers.utcnow")
    def test_get_request_options(
        self, utcnow, region, time, credentials, original_request, signed_request
    ):
        utcnow.return_value = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
        request_signer = aws.RequestSigner(region)
        actual_signed_request = request_signer.get_request_options(
            credentials,
            original_request.get("url"),
            original_request.get("method"),
            original_request.get("data"),
            original_request.get("headers"),
        )

        assert actual_signed_request == signed_request

    def test_get_request_options_with_missing_scheme_url(self):
        request_signer = aws.RequestSigner("us-east-2")

        with pytest.raises(ValueError) as excinfo:
            request_signer.get_request_options(
                {
                    "access_key_id": ACCESS_KEY_ID,
                    "secret_access_key": SECRET_ACCESS_KEY,
                },
                "invalid",
                "POST",
            )

        assert excinfo.match(r"Invalid AWS service URL")

    def test_get_request_options_with_invalid_scheme_url(self):
        request_signer = aws.RequestSigner("us-east-2")

        with pytest.raises(ValueError) as excinfo:
            request_signer.get_request_options(
                {
                    "access_key_id": ACCESS_KEY_ID,
                    "secret_access_key": SECRET_ACCESS_KEY,
                },
                "http://invalid",
                "POST",
            )

        assert excinfo.match(r"Invalid AWS service URL")

    def test_get_request_options_with_missing_hostname_url(self):
        request_signer = aws.RequestSigner("us-east-2")

        with pytest.raises(ValueError) as excinfo:
            request_signer.get_request_options(
                {
                    "access_key_id": ACCESS_KEY_ID,
                    "secret_access_key": SECRET_ACCESS_KEY,
                },
                "https://",
                "POST",
            )

        assert excinfo.match(r"Invalid AWS service URL")


class TestCredentials(object):
    AWS_REGION = "us-east-2"
    AWS_ROLE = "gcp-aws-role"
    AWS_SECURITY_CREDENTIALS_RESPONSE = {
        "AccessKeyId": ACCESS_KEY_ID,
        "SecretAccessKey": SECRET_ACCESS_KEY,
        "Token": TOKEN,
    }
    AWS_IMDSV2_SESSION_TOKEN = "awsimdsv2sessiontoken"
    AWS_SIGNATURE_TIME = "2020-08-11T06:55:22Z"
    CREDENTIAL_SOURCE = {
        "environment_id": "aws1",
        "region_url": REGION_URL,
        "url": SECURITY_CREDS_URL,
        "regional_cred_verification_url": CRED_VERIFICATION_URL,
    }
    CREDENTIAL_SOURCE_IPV6 = {
        "environment_id": "aws1",
        "region_url": REGION_URL_IPV6,
        "url": SECURITY_CREDS_URL_IPV6,
        "regional_cred_verification_url": CRED_VERIFICATION_URL,
        "imdsv2_session_token_url": IMDSV2_SESSION_TOKEN_URL_IPV6,
    }
    SUCCESS_RESPONSE = {
        "access_token": "ACCESS_TOKEN",
        "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": " ".join(SCOPES),
    }

    @classmethod
    def make_serialized_aws_signed_request(
        cls,
        aws_security_credentials,
        region_name="us-east-2",
        url="https://sts.us-east-2.amazonaws.com?Action=GetCallerIdentity&Version=2011-06-15",
    ):
        """Utility to generate serialize AWS signed requests.
        This makes it easy to assert generated subject tokens based on the
        provided AWS security credentials, regions and AWS STS endpoint.
        """
        request_signer = aws.RequestSigner(region_name)
        signed_request = request_signer.get_request_options(
            aws_security_credentials, url, "POST"
        )
        reformatted_signed_request = {
            "url": signed_request.get("url"),
            "method": signed_request.get("method"),
            "headers": [
                {
                    "key": "Authorization",
                    "value": signed_request.get("headers").get("Authorization"),
                },
                {"key": "host", "value": signed_request.get("headers").get("host")},
                {
                    "key": "x-amz-date",
                    "value": signed_request.get("headers").get("x-amz-date"),
                },
            ],
        }
        # Include security token if available.
        if "security_token" in aws_security_credentials:
            reformatted_signed_request.get("headers").append(
                {
                    "key": "x-amz-security-token",
                    "value": signed_request.get("headers").get("x-amz-security-token"),
                }
            )
        # Append x-goog-cloud-target-resource header.
        reformatted_signed_request.get("headers").append(
            {"key": "x-goog-cloud-target-resource", "value": AUDIENCE}
        ),
        return urllib.parse.quote(
            json.dumps(
                reformatted_signed_request, separators=(",", ":"), sort_keys=True
            )
        )

    @classmethod
    def make_mock_request(
        cls,
        region_status=None,
        region_name=None,
        role_status=None,
        role_name=None,
        security_credentials_status=None,
        security_credentials_data=None,
        token_status=None,
        token_data=None,
        impersonation_status=None,
        impersonation_data=None,
        imdsv2_session_token_status=None,
        imdsv2_session_token_data=None,
    ):
        """Utility function to generate a mock HTTP request object.
        This will facilitate testing various edge cases by specify how the
        various endpoints will respond while generating a Google Access token
        in an AWS environment.
        """
        responses = []
        if imdsv2_session_token_status:
            # AWS session token request
            imdsv2_session_response = mock.create_autospec(
                transport.Response, instance=True
            )
            imdsv2_session_response.status = imdsv2_session_token_status
            imdsv2_session_response.data = imdsv2_session_token_data
            responses.append(imdsv2_session_response)

        if region_status:
            # AWS region request.
            region_response = mock.create_autospec(transport.Response, instance=True)
            region_response.status = region_status
            if region_name:
                region_response.data = "{}b".format(region_name).encode("utf-8")
            responses.append(region_response)

        if role_status:
            # AWS role name request.
            role_response = mock.create_autospec(transport.Response, instance=True)
            role_response.status = role_status
            if role_name:
                role_response.data = role_name.encode("utf-8")
            responses.append(role_response)

        if security_credentials_status:
            # AWS security credentials request.
            security_credentials_response = mock.create_autospec(
                transport.Response, instance=True
            )
            security_credentials_response.status = security_credentials_status
            if security_credentials_data:
                security_credentials_response.data = json.dumps(
                    security_credentials_data
                ).encode("utf-8")
            responses.append(security_credentials_response)

        if token_status:
            # GCP token exchange request.
            token_response = mock.create_autospec(transport.Response, instance=True)
            token_response.status = token_status
            token_response.data = json.dumps(token_data).encode("utf-8")
            responses.append(token_response)

        if impersonation_status:
            # Service account impersonation request.
            impersonation_response = mock.create_autospec(
                transport.Response, instance=True
            )
            impersonation_response.status = impersonation_status
            impersonation_response.data = json.dumps(impersonation_data).encode("utf-8")
            responses.append(impersonation_response)

        request = mock.create_autospec(transport.Request)
        request.side_effect = responses

        return request

    @classmethod
    def make_credentials(
        cls,
        credential_source,
        token_url=TOKEN_URL,
        token_info_url=TOKEN_INFO_URL,
        client_id=None,
        client_secret=None,
        quota_project_id=None,
        scopes=None,
        default_scopes=None,
        service_account_impersonation_url=None,
    ):
        return aws.Credentials(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=token_url,
            token_info_url=token_info_url,
            service_account_impersonation_url=service_account_impersonation_url,
            credential_source=credential_source,
            client_id=client_id,
            client_secret=client_secret,
            quota_project_id=quota_project_id,
            scopes=scopes,
            default_scopes=default_scopes,
        )

    @classmethod
    def assert_aws_metadata_request_kwargs(
        cls, request_kwargs, url, headers=None, method="GET"
    ):
        assert request_kwargs["url"] == url
        # All used AWS metadata server endpoints use GET HTTP method.
        assert request_kwargs["method"] == method
        if headers:
            assert request_kwargs["headers"] == headers
        else:
            assert "headers" not in request_kwargs or request_kwargs["headers"] is None
        # None of the endpoints used require any data in request.
        assert "body" not in request_kwargs

    @classmethod
    def assert_token_request_kwargs(
        cls, request_kwargs, headers, request_data, token_url=TOKEN_URL
    ):
        assert request_kwargs["url"] == token_url
        assert request_kwargs["method"] == "POST"
        assert request_kwargs["headers"] == headers
        assert request_kwargs["body"] is not None
        body_tuples = urllib.parse.parse_qsl(request_kwargs["body"])
        assert len(body_tuples) == len(request_data.keys())
        for (k, v) in body_tuples:
            assert v.decode("utf-8") == request_data[k.decode("utf-8")]

    @classmethod
    def assert_impersonation_request_kwargs(
        cls,
        request_kwargs,
        headers,
        request_data,
        service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
    ):
        assert request_kwargs["url"] == service_account_impersonation_url
        assert request_kwargs["method"] == "POST"
        assert request_kwargs["headers"] == headers
        assert request_kwargs["body"] is not None
        body_json = json.loads(request_kwargs["body"].decode("utf-8"))
        assert body_json == request_data

    @mock.patch.object(aws.Credentials, "__init__", return_value=None)
    def test_from_info_full_options(self, mock_init):
        credentials = aws.Credentials.from_info(
            {
                "audience": AUDIENCE,
                "subject_token_type": SUBJECT_TOKEN_TYPE,
                "token_url": TOKEN_URL,
                "token_info_url": TOKEN_INFO_URL,
                "service_account_impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
                "service_account_impersonation": {"token_lifetime_seconds": 2800},
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "quota_project_id": QUOTA_PROJECT_ID,
                "credential_source": self.CREDENTIAL_SOURCE,
            }
        )

        # Confirm aws.Credentials instance initialized with the expected parameters.
        assert isinstance(credentials, aws.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=TOKEN_INFO_URL,
            service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=QUOTA_PROJECT_ID,
            workforce_pool_user_project=None,
        )

    @mock.patch.object(aws.Credentials, "__init__", return_value=None)
    def test_from_info_required_options_only(self, mock_init):
        credentials = aws.Credentials.from_info(
            {
                "audience": AUDIENCE,
                "subject_token_type": SUBJECT_TOKEN_TYPE,
                "token_url": TOKEN_URL,
                "credential_source": self.CREDENTIAL_SOURCE,
            }
        )

        # Confirm aws.Credentials instance initialized with the expected parameters.
        assert isinstance(credentials, aws.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=None,
            service_account_impersonation_url=None,
            service_account_impersonation_options={},
            client_id=None,
            client_secret=None,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=None,
            workforce_pool_user_project=None,
        )

    @mock.patch.object(aws.Credentials, "__init__", return_value=None)
    def test_from_file_full_options(self, mock_init, tmpdir):
        info = {
            "audience": AUDIENCE,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "token_url": TOKEN_URL,
            "token_info_url": TOKEN_INFO_URL,
            "service_account_impersonation_url": SERVICE_ACCOUNT_IMPERSONATION_URL,
            "service_account_impersonation": {"token_lifetime_seconds": 2800},
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "quota_project_id": QUOTA_PROJECT_ID,
            "credential_source": self.CREDENTIAL_SOURCE,
        }
        config_file = tmpdir.join("config.json")
        config_file.write(json.dumps(info))
        credentials = aws.Credentials.from_file(str(config_file))

        # Confirm aws.Credentials instance initialized with the expected parameters.
        assert isinstance(credentials, aws.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=TOKEN_INFO_URL,
            service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
            service_account_impersonation_options={"token_lifetime_seconds": 2800},
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=QUOTA_PROJECT_ID,
            workforce_pool_user_project=None,
        )

    @mock.patch.object(aws.Credentials, "__init__", return_value=None)
    def test_from_file_required_options_only(self, mock_init, tmpdir):
        info = {
            "audience": AUDIENCE,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "token_url": TOKEN_URL,
            "credential_source": self.CREDENTIAL_SOURCE,
        }
        config_file = tmpdir.join("config.json")
        config_file.write(json.dumps(info))
        credentials = aws.Credentials.from_file(str(config_file))

        # Confirm aws.Credentials instance initialized with the expected parameters.
        assert isinstance(credentials, aws.Credentials)
        mock_init.assert_called_once_with(
            audience=AUDIENCE,
            subject_token_type=SUBJECT_TOKEN_TYPE,
            token_url=TOKEN_URL,
            token_info_url=None,
            service_account_impersonation_url=None,
            service_account_impersonation_options={},
            client_id=None,
            client_secret=None,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=None,
            workforce_pool_user_project=None,
        )

    def test_constructor_invalid_credential_source(self):
        # Provide invalid credential source.
        credential_source = {"unsupported": "value"}

        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(credential_source=credential_source)

        assert excinfo.match(r"No valid AWS 'credential_source' provided")

    def test_constructor_invalid_environment_id(self):
        # Provide invalid environment_id.
        credential_source = self.CREDENTIAL_SOURCE.copy()
        credential_source["environment_id"] = "azure1"

        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(credential_source=credential_source)

        assert excinfo.match(r"No valid AWS 'credential_source' provided")

    def test_constructor_missing_cred_verification_url(self):
        # regional_cred_verification_url is a required field.
        credential_source = self.CREDENTIAL_SOURCE.copy()
        credential_source.pop("regional_cred_verification_url")

        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(credential_source=credential_source)

        assert excinfo.match(r"No valid AWS 'credential_source' provided")

    def test_constructor_invalid_environment_id_version(self):
        # Provide an unsupported version.
        credential_source = self.CREDENTIAL_SOURCE.copy()
        credential_source["environment_id"] = "aws3"

        with pytest.raises(ValueError) as excinfo:
            self.make_credentials(credential_source=credential_source)

        assert excinfo.match(r"aws version '3' is not supported in the current build.")

    def test_info(self):
        credentials = self.make_credentials(
            credential_source=self.CREDENTIAL_SOURCE.copy()
        )

        assert credentials.info == {
            "type": "external_account",
            "audience": AUDIENCE,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
            "token_url": TOKEN_URL,
            "token_info_url": TOKEN_INFO_URL,
            "credential_source": self.CREDENTIAL_SOURCE,
        }

    def test_token_info_url(self):
        credentials = self.make_credentials(
            credential_source=self.CREDENTIAL_SOURCE.copy()
        )

        assert credentials.token_info_url == TOKEN_INFO_URL

    def test_token_info_url_custom(self):
        for url in VALID_TOKEN_URLS:
            credentials = self.make_credentials(
                credential_source=self.CREDENTIAL_SOURCE.copy(),
                token_info_url=(url + "/introspect"),
            )

            assert credentials.token_info_url == (url + "/introspect")

    def test_token_info_url_negative(self):
        credentials = self.make_credentials(
            credential_source=self.CREDENTIAL_SOURCE.copy(), token_info_url=None
        )

        assert not credentials.token_info_url

    def test_token_url_custom(self):
        for url in VALID_TOKEN_URLS:
            credentials = self.make_credentials(
                credential_source=self.CREDENTIAL_SOURCE.copy(),
                token_url=(url + "/token"),
            )

            assert credentials._token_url == (url + "/token")

    def test_service_account_impersonation_url_custom(self):
        for url in VALID_SERVICE_ACCOUNT_IMPERSONATION_URLS:
            credentials = self.make_credentials(
                credential_source=self.CREDENTIAL_SOURCE.copy(),
                service_account_impersonation_url=(
                    url + SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE
                ),
            )

            assert credentials._service_account_impersonation_url == (
                url + SERVICE_ACCOUNT_IMPERSONATION_URL_ROUTE
            )

    def test_retrieve_subject_token_missing_region_url(self):
        # When AWS_REGION envvar is not available, region_url is required for
        # determining the current AWS region.
        credential_source = self.CREDENTIAL_SOURCE.copy()
        credential_source.pop("region_url")
        credentials = self.make_credentials(credential_source=credential_source)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.retrieve_subject_token(None)

        assert excinfo.match(r"Unable to determine AWS region")

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_temp_creds_no_environment_vars(
        self, utcnow
    ):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(request)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        # Assert region request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1], REGION_URL
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[1][1], SECURITY_CREDS_URL
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[2][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {"Content-Type": "application/json"},
        )

        # Retrieve subject_token again. Region should not be queried again.
        new_request = self.make_mock_request(
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
        )

        credentials.retrieve_subject_token(new_request)

        # Only 3 requests should be sent as the region is cached.
        assert len(new_request.call_args_list) == 2
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            new_request.call_args_list[0][1], SECURITY_CREDS_URL
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            new_request.call_args_list[1][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {"Content-Type": "application/json"},
        )

    @mock.patch("google.auth._helpers.utcnow")
    @mock.patch.dict(os.environ, {})
    def test_retrieve_subject_token_success_temp_creds_no_environment_vars_idmsv2(
        self, utcnow
    ):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            imdsv2_session_token_status=http_client.OK,
            imdsv2_session_token_data=self.AWS_IMDSV2_SESSION_TOKEN,
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE.copy()
        credential_source_token_url[
            "imdsv2_session_token_url"
        ] = IMDSV2_SESSION_TOKEN_URL
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        subject_token = credentials.retrieve_subject_token(request)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        # Assert session token request
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )
        # Assert region request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[1][1],
            REGION_URL,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[2][1],
            SECURITY_CREDS_URL,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[3][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {
                "Content-Type": "application/json",
                "X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN,
            },
        )

        # Retrieve subject_token again. Region should not be queried again.
        new_request = self.make_mock_request(
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            imdsv2_session_token_status=http_client.OK,
            imdsv2_session_token_data=self.AWS_IMDSV2_SESSION_TOKEN,
        )

        credentials.retrieve_subject_token(new_request)

        # Only 3 requests should be sent as the region is cached.
        assert len(new_request.call_args_list) == 3
        # Assert session token request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            new_request.call_args_list[1][1],
            SECURITY_CREDS_URL,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            new_request.call_args_list[2][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {
                "Content-Type": "application/json",
                "X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN,
            },
        )

    @mock.patch("google.auth._helpers.utcnow")
    @mock.patch.dict(
        os.environ,
        {
            environment_vars.AWS_REGION: AWS_REGION,
            environment_vars.AWS_ACCESS_KEY_ID: ACCESS_KEY_ID,
        },
    )
    def test_retrieve_subject_token_success_temp_creds_environment_vars_missing_secret_access_key_idmsv2(
        self, utcnow
    ):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            imdsv2_session_token_status=http_client.OK,
            imdsv2_session_token_data=self.AWS_IMDSV2_SESSION_TOKEN,
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE.copy()
        credential_source_token_url[
            "imdsv2_session_token_url"
        ] = IMDSV2_SESSION_TOKEN_URL
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        subject_token = credentials.retrieve_subject_token(request)
        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        # Assert session token request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[1][1],
            SECURITY_CREDS_URL,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[2][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {
                "Content-Type": "application/json",
                "X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN,
            },
        )

    @mock.patch("google.auth._helpers.utcnow")
    @mock.patch.dict(
        os.environ,
        {
            environment_vars.AWS_REGION: AWS_REGION,
            environment_vars.AWS_SECRET_ACCESS_KEY: SECRET_ACCESS_KEY,
        },
    )
    def test_retrieve_subject_token_success_temp_creds_environment_vars_missing_access_key_id_idmsv2(
        self, utcnow
    ):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            imdsv2_session_token_status=http_client.OK,
            imdsv2_session_token_data=self.AWS_IMDSV2_SESSION_TOKEN,
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE.copy()
        credential_source_token_url[
            "imdsv2_session_token_url"
        ] = IMDSV2_SESSION_TOKEN_URL
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        subject_token = credentials.retrieve_subject_token(request)
        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        # Assert session token request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[1][1],
            SECURITY_CREDS_URL,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[2][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {
                "Content-Type": "application/json",
                "X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN,
            },
        )

    @mock.patch("google.auth._helpers.utcnow")
    @mock.patch.dict(os.environ, {environment_vars.AWS_REGION: AWS_REGION})
    def test_retrieve_subject_token_success_temp_creds_environment_vars_missing_creds_idmsv2(
        self, utcnow
    ):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            imdsv2_session_token_status=http_client.OK,
            imdsv2_session_token_data=self.AWS_IMDSV2_SESSION_TOKEN,
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE.copy()
        credential_source_token_url[
            "imdsv2_session_token_url"
        ] = IMDSV2_SESSION_TOKEN_URL
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        subject_token = credentials.retrieve_subject_token(request)
        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        # Assert session token request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[1][1],
            SECURITY_CREDS_URL,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[2][1],
            "{}/{}".format(SECURITY_CREDS_URL, self.AWS_ROLE),
            {
                "Content-Type": "application/json",
                "X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN,
            },
        )

    @mock.patch("google.auth._helpers.utcnow")
    @mock.patch.dict(
        os.environ,
        {
            environment_vars.AWS_REGION: AWS_REGION,
            environment_vars.AWS_ACCESS_KEY_ID: ACCESS_KEY_ID,
            environment_vars.AWS_SECRET_ACCESS_KEY: SECRET_ACCESS_KEY,
        },
    )
    def test_retrieve_subject_token_success_temp_creds_idmsv2(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            role_status=http_client.OK, role_name=self.AWS_ROLE
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE.copy()
        credential_source_token_url[
            "imdsv2_session_token_url"
        ] = IMDSV2_SESSION_TOKEN_URL
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        credentials.retrieve_subject_token(request)
        assert not request.called

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_ipv6(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            imdsv2_session_token_status=http_client.OK,
            imdsv2_session_token_data=self.AWS_IMDSV2_SESSION_TOKEN,
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE_IPV6.copy()
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        subject_token = credentials.retrieve_subject_token(request)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        # Assert session token request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL_IPV6,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )
        # Assert region request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[1][1],
            REGION_URL_IPV6,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert role request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[2][1],
            SECURITY_CREDS_URL_IPV6,
            {"X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN},
        )
        # Assert security credentials request.
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[3][1],
            "{}/{}".format(SECURITY_CREDS_URL_IPV6, self.AWS_ROLE),
            {
                "Content-Type": "application/json",
                "X-aws-ec2-metadata-token": self.AWS_IMDSV2_SESSION_TOKEN,
            },
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_session_error_idmsv2(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            imdsv2_session_token_status=http_client.UNAUTHORIZED,
            imdsv2_session_token_data="unauthorized",
        )
        credential_source_token_url = self.CREDENTIAL_SOURCE.copy()
        credential_source_token_url[
            "imdsv2_session_token_url"
        ] = IMDSV2_SESSION_TOKEN_URL
        credentials = self.make_credentials(
            credential_source=credential_source_token_url
        )

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.retrieve_subject_token(request)

        assert excinfo.match(r"Unable to retrieve AWS Session Token")

        # Assert session token request
        self.assert_aws_metadata_request_kwargs(
            request.call_args_list[0][1],
            IMDSV2_SESSION_TOKEN_URL,
            {"X-aws-ec2-metadata-token-ttl-seconds": "300"},
            "PUT",
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_permanent_creds_no_environment_vars(
        self, utcnow
    ):
        # Simualte a permanent credential without a session token is
        # returned by the security-credentials endpoint.
        security_creds_response = self.AWS_SECURITY_CREDENTIALS_RESPONSE.copy()
        security_creds_response.pop("Token")
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=security_creds_response,
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(request)

        assert subject_token == self.make_serialized_aws_signed_request(
            {"access_key_id": ACCESS_KEY_ID, "secret_access_key": SECRET_ACCESS_KEY}
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_environment_vars(self, utcnow, monkeypatch):
        monkeypatch.setenv(environment_vars.AWS_ACCESS_KEY_ID, ACCESS_KEY_ID)
        monkeypatch.setenv(environment_vars.AWS_SECRET_ACCESS_KEY, SECRET_ACCESS_KEY)
        monkeypatch.setenv(environment_vars.AWS_SESSION_TOKEN, TOKEN)
        monkeypatch.setenv(environment_vars.AWS_REGION, self.AWS_REGION)
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(None)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_environment_vars_with_default_region(
        self, utcnow, monkeypatch
    ):
        monkeypatch.setenv(environment_vars.AWS_ACCESS_KEY_ID, ACCESS_KEY_ID)
        monkeypatch.setenv(environment_vars.AWS_SECRET_ACCESS_KEY, SECRET_ACCESS_KEY)
        monkeypatch.setenv(environment_vars.AWS_SESSION_TOKEN, TOKEN)
        monkeypatch.setenv(environment_vars.AWS_DEFAULT_REGION, self.AWS_REGION)
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(None)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_environment_vars_with_both_regions_set(
        self, utcnow, monkeypatch
    ):
        monkeypatch.setenv(environment_vars.AWS_ACCESS_KEY_ID, ACCESS_KEY_ID)
        monkeypatch.setenv(environment_vars.AWS_SECRET_ACCESS_KEY, SECRET_ACCESS_KEY)
        monkeypatch.setenv(environment_vars.AWS_SESSION_TOKEN, TOKEN)
        monkeypatch.setenv(environment_vars.AWS_DEFAULT_REGION, "Malformed AWS Region")
        # This test makes sure that the AWS_REGION gets used over AWS_DEFAULT_REGION,
        # So, AWS_DEFAULT_REGION is set to something that would cause the test to fail,
        # And AWS_REGION is set to the a valid value, and it should succeed
        monkeypatch.setenv(environment_vars.AWS_REGION, self.AWS_REGION)
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(None)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_environment_vars_no_session_token(
        self, utcnow, monkeypatch
    ):
        monkeypatch.setenv(environment_vars.AWS_ACCESS_KEY_ID, ACCESS_KEY_ID)
        monkeypatch.setenv(environment_vars.AWS_SECRET_ACCESS_KEY, SECRET_ACCESS_KEY)
        monkeypatch.setenv(environment_vars.AWS_REGION, self.AWS_REGION)
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(None)

        assert subject_token == self.make_serialized_aws_signed_request(
            {"access_key_id": ACCESS_KEY_ID, "secret_access_key": SECRET_ACCESS_KEY}
        )

    @mock.patch("google.auth._helpers.utcnow")
    def test_retrieve_subject_token_success_environment_vars_except_region(
        self, utcnow, monkeypatch
    ):
        monkeypatch.setenv(environment_vars.AWS_ACCESS_KEY_ID, ACCESS_KEY_ID)
        monkeypatch.setenv(environment_vars.AWS_SECRET_ACCESS_KEY, SECRET_ACCESS_KEY)
        monkeypatch.setenv(environment_vars.AWS_SESSION_TOKEN, TOKEN)
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        # Region will be queried since it is not found in envvars.
        request = self.make_mock_request(
            region_status=http_client.OK, region_name=self.AWS_REGION
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        subject_token = credentials.retrieve_subject_token(request)

        assert subject_token == self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )

    def test_retrieve_subject_token_error_determining_aws_region(self):
        # Simulate error in retrieving the AWS region.
        request = self.make_mock_request(region_status=http_client.BAD_REQUEST)
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.retrieve_subject_token(request)

        assert excinfo.match(r"Unable to retrieve AWS region")

    def test_retrieve_subject_token_error_determining_aws_role(self):
        # Simulate error in retrieving the AWS role name.
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.BAD_REQUEST,
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.retrieve_subject_token(request)

        assert excinfo.match(r"Unable to retrieve AWS role name")

    def test_retrieve_subject_token_error_determining_security_creds_url(self):
        # Simulate the security-credentials url is missing. This is needed for
        # determining the AWS security credentials when not found in envvars.
        credential_source = self.CREDENTIAL_SOURCE.copy()
        credential_source.pop("url")
        request = self.make_mock_request(
            region_status=http_client.OK, region_name=self.AWS_REGION
        )
        credentials = self.make_credentials(credential_source=credential_source)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.retrieve_subject_token(request)

        assert excinfo.match(
            r"Unable to determine the AWS metadata server security credentials endpoint"
        )

    def test_retrieve_subject_token_error_determining_aws_security_creds(self):
        # Simulate error in retrieving the AWS security credentials.
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.BAD_REQUEST,
        )
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.retrieve_subject_token(request)

        assert excinfo.match(r"Unable to retrieve AWS security credentials")

    @mock.patch("google.auth._helpers.utcnow")
    def test_refresh_success_without_impersonation_ignore_default_scopes(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        expected_subject_token = self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + BASIC_AUTH_ENCODING,
        }
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": " ".join(SCOPES),
            "subject_token": expected_subject_token,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            token_status=http_client.OK,
            token_data=self.SUCCESS_RESPONSE,
        )
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=QUOTA_PROJECT_ID,
            scopes=SCOPES,
            # Default scopes should be ignored.
            default_scopes=["ignored"],
        )

        credentials.refresh(request)

        assert len(request.call_args_list) == 4
        # Fourth request should be sent to GCP STS endpoint.
        self.assert_token_request_kwargs(
            request.call_args_list[3][1], token_headers, token_request_data
        )
        assert credentials.token == self.SUCCESS_RESPONSE["access_token"]
        assert credentials.quota_project_id == QUOTA_PROJECT_ID
        assert credentials.scopes == SCOPES
        assert credentials.default_scopes == ["ignored"]

    @mock.patch("google.auth._helpers.utcnow")
    def test_refresh_success_without_impersonation_use_default_scopes(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        expected_subject_token = self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + BASIC_AUTH_ENCODING,
        }
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": " ".join(SCOPES),
            "subject_token": expected_subject_token,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
        }
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            token_status=http_client.OK,
            token_data=self.SUCCESS_RESPONSE,
        )
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            quota_project_id=QUOTA_PROJECT_ID,
            scopes=None,
            # Default scopes should be used since user specified scopes are none.
            default_scopes=SCOPES,
        )

        credentials.refresh(request)

        assert len(request.call_args_list) == 4
        # Fourth request should be sent to GCP STS endpoint.
        self.assert_token_request_kwargs(
            request.call_args_list[3][1], token_headers, token_request_data
        )
        assert credentials.token == self.SUCCESS_RESPONSE["access_token"]
        assert credentials.quota_project_id == QUOTA_PROJECT_ID
        assert credentials.scopes is None
        assert credentials.default_scopes == SCOPES

    @mock.patch("google.auth._helpers.utcnow")
    def test_refresh_success_with_impersonation_ignore_default_scopes(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=3600)
        ).isoformat("T") + "Z"
        expected_subject_token = self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + BASIC_AUTH_ENCODING,
        }
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "https://www.googleapis.com/auth/iam",
            "subject_token": expected_subject_token,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
            "x-goog-user-project": QUOTA_PROJECT_ID,
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": SCOPES,
            "lifetime": "3600s",
        }
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            token_status=http_client.OK,
            token_data=self.SUCCESS_RESPONSE,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
            quota_project_id=QUOTA_PROJECT_ID,
            scopes=SCOPES,
            # Default scopes should be ignored.
            default_scopes=["ignored"],
        )

        credentials.refresh(request)

        assert len(request.call_args_list) == 5
        # Fourth request should be sent to GCP STS endpoint.
        self.assert_token_request_kwargs(
            request.call_args_list[3][1], token_headers, token_request_data
        )
        # Fifth request should be sent to iamcredentials endpoint for service
        # account impersonation.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[4][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.token == impersonation_response["accessToken"]
        assert credentials.quota_project_id == QUOTA_PROJECT_ID
        assert credentials.scopes == SCOPES
        assert credentials.default_scopes == ["ignored"]

    @mock.patch("google.auth._helpers.utcnow")
    def test_refresh_success_with_impersonation_use_default_scopes(self, utcnow):
        utcnow.return_value = datetime.datetime.strptime(
            self.AWS_SIGNATURE_TIME, "%Y-%m-%dT%H:%M:%SZ"
        )
        expire_time = (
            _helpers.utcnow().replace(microsecond=0) + datetime.timedelta(seconds=3600)
        ).isoformat("T") + "Z"
        expected_subject_token = self.make_serialized_aws_signed_request(
            {
                "access_key_id": ACCESS_KEY_ID,
                "secret_access_key": SECRET_ACCESS_KEY,
                "security_token": TOKEN,
            }
        )
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + BASIC_AUTH_ENCODING,
        }
        token_request_data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "audience": AUDIENCE,
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "https://www.googleapis.com/auth/iam",
            "subject_token": expected_subject_token,
            "subject_token_type": SUBJECT_TOKEN_TYPE,
        }
        # Service account impersonation request/response.
        impersonation_response = {
            "accessToken": "SA_ACCESS_TOKEN",
            "expireTime": expire_time,
        }
        impersonation_headers = {
            "Content-Type": "application/json",
            "authorization": "Bearer {}".format(self.SUCCESS_RESPONSE["access_token"]),
            "x-goog-user-project": QUOTA_PROJECT_ID,
        }
        impersonation_request_data = {
            "delegates": None,
            "scope": SCOPES,
            "lifetime": "3600s",
        }
        request = self.make_mock_request(
            region_status=http_client.OK,
            region_name=self.AWS_REGION,
            role_status=http_client.OK,
            role_name=self.AWS_ROLE,
            security_credentials_status=http_client.OK,
            security_credentials_data=self.AWS_SECURITY_CREDENTIALS_RESPONSE,
            token_status=http_client.OK,
            token_data=self.SUCCESS_RESPONSE,
            impersonation_status=http_client.OK,
            impersonation_data=impersonation_response,
        )
        credentials = self.make_credentials(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            credential_source=self.CREDENTIAL_SOURCE,
            service_account_impersonation_url=SERVICE_ACCOUNT_IMPERSONATION_URL,
            quota_project_id=QUOTA_PROJECT_ID,
            scopes=None,
            # Default scopes should be used since user specified scopes are none.
            default_scopes=SCOPES,
        )

        credentials.refresh(request)

        assert len(request.call_args_list) == 5
        # Fourth request should be sent to GCP STS endpoint.
        self.assert_token_request_kwargs(
            request.call_args_list[3][1], token_headers, token_request_data
        )
        # Fifth request should be sent to iamcredentials endpoint for service
        # account impersonation.
        self.assert_impersonation_request_kwargs(
            request.call_args_list[4][1],
            impersonation_headers,
            impersonation_request_data,
        )
        assert credentials.token == impersonation_response["accessToken"]
        assert credentials.quota_project_id == QUOTA_PROJECT_ID
        assert credentials.scopes is None
        assert credentials.default_scopes == SCOPES

    def test_refresh_with_retrieve_subject_token_error(self):
        request = self.make_mock_request(region_status=http_client.BAD_REQUEST)
        credentials = self.make_credentials(credential_source=self.CREDENTIAL_SOURCE)

        with pytest.raises(exceptions.RefreshError) as excinfo:
            credentials.refresh(request)

        assert excinfo.match(r"Unable to retrieve AWS region")
