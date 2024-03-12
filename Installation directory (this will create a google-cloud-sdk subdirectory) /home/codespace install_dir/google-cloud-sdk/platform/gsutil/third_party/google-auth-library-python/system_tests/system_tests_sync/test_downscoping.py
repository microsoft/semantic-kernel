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

import re
import uuid

import google.auth

from google.auth import downscoped
from google.auth.transport import requests
from google.cloud import exceptions
from google.cloud import storage
from google.oauth2 import credentials

import pytest

 # The object prefix used to test access to files beginning with this prefix.
_OBJECT_PREFIX = "customer-a"
# The object name of the object inaccessible by the downscoped token.
_ACCESSIBLE_OBJECT_NAME = "{0}-data.txt".format(_OBJECT_PREFIX)
# The content of the object accessible by the downscoped token.
_ACCESSIBLE_CONTENT = "hello world"
# The content of the object inaccessible by the downscoped token.
_INACCESSIBLE_CONTENT = "secret content"
# The object name of the object inaccessible by the downscoped token.
_INACCESSIBLE_OBJECT_NAME = "other-customer-data.txt"


@pytest.fixture(scope="module")
def temp_bucket():
    """Yields a bucket that is deleted after the test completes."""
    bucket = None
    while bucket is None or bucket.exists():
        bucket_name = "auth-python-downscope-test-{}".format(uuid.uuid4())
        bucket = storage.Client().bucket(bucket_name)
    bucket = storage.Client().create_bucket(bucket.name)
    yield bucket
    bucket.delete(force=True)


@pytest.fixture(scope="module")
def temp_blobs(temp_bucket):
    """Yields two blobs that are deleted after the test completes."""
    bucket = temp_bucket
    # Downscoped tokens will have readonly access to this blob.
    accessible_blob = bucket.blob(_ACCESSIBLE_OBJECT_NAME)
    accessible_blob.upload_from_string(_ACCESSIBLE_CONTENT)
    # Downscoped tokens will have no access to this blob.
    inaccessible_blob = bucket.blob(_INACCESSIBLE_OBJECT_NAME)
    inaccessible_blob.upload_from_string(_INACCESSIBLE_CONTENT)
    yield (accessible_blob, inaccessible_blob)
    bucket.delete_blobs([accessible_blob, inaccessible_blob])


def get_token_from_broker(bucket_name, object_prefix):
    """Simulates token broker generating downscoped tokens for specified bucket.

    Args:
        bucket_name (str): The name of the Cloud Storage bucket.
        object_prefix (str): The prefix string of the object name. This is used
            to ensure access is restricted to only objects starting with this
            prefix string.

    Returns:
        Tuple[str, datetime.datetime]: The downscoped access token and its expiry date.
    """
    # Initialize the Credential Access Boundary rules.
    available_resource = "//storage.googleapis.com/projects/_/buckets/{0}".format(bucket_name)
    # Downscoped credentials will have readonly access to the resource.
    available_permissions = ["inRole:roles/storage.objectViewer"]
    # Only objects starting with the specified prefix string in the object name
    # will be allowed read access.
    availability_expression = (
        "resource.name.startsWith('projects/_/buckets/{0}/objects/{1}')".format(bucket_name, object_prefix)
    )
    availability_condition = downscoped.AvailabilityCondition(availability_expression)
    # Define the single access boundary rule using the above properties.
    rule = downscoped.AccessBoundaryRule(
        available_resource=available_resource,
        available_permissions=available_permissions,
        availability_condition=availability_condition,
    )
    # Define the Credential Access Boundary with all the relevant rules.
    credential_access_boundary = downscoped.CredentialAccessBoundary(rules=[rule])

    # Retrieve the source credentials via ADC.
    source_credentials, _ = google.auth.default()
    if source_credentials.requires_scopes:
        source_credentials = source_credentials.with_scopes(
            ["https://www.googleapis.com/auth/cloud-platform"]
        )

    # Create the downscoped credentials.
    downscoped_credentials = downscoped.Credentials(
        source_credentials=source_credentials,
        credential_access_boundary=credential_access_boundary,
    )

    # Refresh the tokens.
    downscoped_credentials.refresh(requests.Request())

    # These values will need to be passed to the token consumer.
    access_token = downscoped_credentials.token
    expiry = downscoped_credentials.expiry
    return (access_token, expiry)


def test_downscoping(temp_blobs):
    """Tests token consumer access to cloud storage using downscoped tokens.

    Args:
        temp_blobs (Tuple[google.cloud.storage.blob.Blob, ...]): The temporarily
            created test cloud storage blobs (one readonly accessible, the other
            not).
    """
    accessible_blob, inaccessible_blob = temp_blobs
    bucket_name = accessible_blob.bucket.name
    # Create the OAuth credentials from the downscoped token and pass a
    # refresh handler to handle token expiration. We are passing a
    # refresh_handler instead of a one-time access token/expiry pair.
    # This will allow testing this on-demand method for getting access tokens.
    def refresh_handler(request, scopes=None):
        # Get readonly access tokens to objects with accessible prefix in
        # the temporarily created bucket.
        return get_token_from_broker(bucket_name, _OBJECT_PREFIX)

    creds = credentials.Credentials(
        None,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
        refresh_handler=refresh_handler,
    )

    # Initialize a Cloud Storage client with the oauth2 credentials.
    storage_client = storage.Client(credentials=creds)

    # Test read access succeeds to accessible blob.
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(accessible_blob.name)
    assert blob.download_as_bytes().decode("utf-8") == _ACCESSIBLE_CONTENT

    # Test write access fails.
    with pytest.raises(exceptions.Forbidden) as excinfo:
        blob.upload_from_string("Write operations are not allowed")

    assert excinfo.match(r"does not have storage.objects.create access")

    # Test read access fails to inaccessible blob.
    with pytest.raises(exceptions.Forbidden) as excinfo:
        bucket.blob(inaccessible_blob.name).download_as_bytes()

    assert excinfo.match(r"does not have storage.objects.get access")
