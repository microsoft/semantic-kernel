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

import google.auth
import google.auth.credentials
import google.auth.jwt
import google.auth.transport.grpc
from google.oauth2 import service_account

from google.cloud import pubsub_v1


def test_grpc_request_with_regular_credentials(http_request):
    credentials, project_id = google.auth.default()
    credentials = google.auth.credentials.with_scopes_if_required(
        credentials, scopes=["https://www.googleapis.com/auth/pubsub"]
    )


    # Create a pub/sub client.
    client = pubsub_v1.PublisherClient(credentials=credentials)

    # list the topics and drain the iterator to test that an authorized API
    # call works.
    list_topics_iter = client.list_topics(project="projects/{}".format(project_id))
    list(list_topics_iter)


def test_grpc_request_with_regular_credentials_and_self_signed_jwt(http_request):
    credentials, project_id = google.auth.default()

    # At the time this test is being written, there are no GAPIC libraries
    # that will trigger the self-signed JWT flow. Manually create the self-signed
    # jwt on the service account credential to check that the request
    # succeeds.
    credentials = credentials.with_scopes(
        scopes=[], default_scopes=["https://www.googleapis.com/auth/pubsub"]
    )
    credentials._create_self_signed_jwt(audience="https://pubsub.googleapis.com/")

    # Create a pub/sub client.
    client = pubsub_v1.PublisherClient(credentials=credentials)

    # list the topics and drain the iterator to test that an authorized API
    # call works.
    list_topics_iter = client.list_topics(project="projects/{}".format(project_id))
    list(list_topics_iter)
    
    # Check that self-signed JWT was created and is being used
    assert credentials._jwt_credentials is not None
    assert credentials._jwt_credentials.token == credentials.token


def test_grpc_request_with_jwt_credentials():
    credentials, project_id = google.auth.default()
    audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    credentials = google.auth.jwt.Credentials.from_signing_credentials(
        credentials, audience=audience
    )

    # Create a pub/sub client.
    client = pubsub_v1.PublisherClient(credentials=credentials)

    # list the topics and drain the iterator to test that an authorized API
    # call works.
    list_topics_iter = client.list_topics(project="projects/{}".format(project_id))
    list(list_topics_iter)


def test_grpc_request_with_on_demand_jwt_credentials():
    credentials, project_id = google.auth.default()
    credentials = google.auth.jwt.OnDemandCredentials.from_signing_credentials(
        credentials
    )

    # Create a pub/sub client.
    client = pubsub_v1.PublisherClient(credentials=credentials)

    # list the topics and drain the iterator to test that an authorized API
    # call works.
    list_topics_iter = client.list_topics(project="projects/{}".format(project_id))
    list(list_topics_iter)
