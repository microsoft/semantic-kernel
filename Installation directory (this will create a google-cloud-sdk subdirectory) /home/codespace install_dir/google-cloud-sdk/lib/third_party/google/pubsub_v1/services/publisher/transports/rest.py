# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from google.auth.transport.requests import AuthorizedSession  # type: ignore
import json  # type: ignore
import grpc  # type: ignore
from google.auth.transport.grpc import SslCredentials  # type: ignore
from google.auth import credentials as ga_credentials  # type: ignore
from google.api_core import exceptions as core_exceptions
from google.api_core import retry as retries
from google.api_core import rest_helpers
from google.api_core import rest_streaming
from google.api_core import path_template
from google.api_core import gapic_v1

from cloudsdk.google.protobuf import json_format
from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from requests import __version__ as requests_version
import dataclasses
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import warnings

try:
    OptionalRetry = Union[retries.Retry, gapic_v1.method._MethodDefault]
except AttributeError:  # pragma: NO COVER
    OptionalRetry = Union[retries.Retry, object]  # type: ignore


from google.iam.v1 import iam_policy_pb2  # type: ignore
from google.iam.v1 import policy_pb2  # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from google.pubsub_v1.types import pubsub

from .base import PublisherTransport, DEFAULT_CLIENT_INFO as BASE_DEFAULT_CLIENT_INFO


DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(
    gapic_version=BASE_DEFAULT_CLIENT_INFO.gapic_version,
    grpc_version=None,
    rest_version=requests_version,
)


class PublisherRestInterceptor:
    """Interceptor for Publisher.

    Interceptors are used to manipulate requests, request metadata, and responses
    in arbitrary ways.
    Example use cases include:
    * Logging
    * Verifying requests according to service or custom semantics
    * Stripping extraneous information from responses

    These use cases and more can be enabled by injecting an
    instance of a custom subclass when constructing the PublisherRestTransport.

    .. code-block:: python
        class MyCustomPublisherInterceptor(PublisherRestInterceptor):
            def pre_create_topic(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_topic(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_delete_topic(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_detach_subscription(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_detach_subscription(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_topic(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_topic(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_topics(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_topics(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_topic_snapshots(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_topic_snapshots(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_topic_subscriptions(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_topic_subscriptions(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_publish(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_publish(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_update_topic(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_update_topic(self, response):
                logging.log(f"Received response: {response}")
                return response

        transport = PublisherRestTransport(interceptor=MyCustomPublisherInterceptor())
        client = PublisherClient(transport=transport)


    """

    def pre_create_topic(
        self, request: pubsub.Topic, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[pubsub.Topic, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for create_topic

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_create_topic(self, response: pubsub.Topic) -> pubsub.Topic:
        """Post-rpc interceptor for create_topic

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_delete_topic(
        self, request: pubsub.DeleteTopicRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[pubsub.DeleteTopicRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for delete_topic

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def pre_detach_subscription(
        self,
        request: pubsub.DetachSubscriptionRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[pubsub.DetachSubscriptionRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for detach_subscription

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_detach_subscription(
        self, response: pubsub.DetachSubscriptionResponse
    ) -> pubsub.DetachSubscriptionResponse:
        """Post-rpc interceptor for detach_subscription

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_get_topic(
        self, request: pubsub.GetTopicRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[pubsub.GetTopicRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for get_topic

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_get_topic(self, response: pubsub.Topic) -> pubsub.Topic:
        """Post-rpc interceptor for get_topic

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_list_topics(
        self, request: pubsub.ListTopicsRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[pubsub.ListTopicsRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for list_topics

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_list_topics(
        self, response: pubsub.ListTopicsResponse
    ) -> pubsub.ListTopicsResponse:
        """Post-rpc interceptor for list_topics

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_list_topic_snapshots(
        self,
        request: pubsub.ListTopicSnapshotsRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[pubsub.ListTopicSnapshotsRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for list_topic_snapshots

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_list_topic_snapshots(
        self, response: pubsub.ListTopicSnapshotsResponse
    ) -> pubsub.ListTopicSnapshotsResponse:
        """Post-rpc interceptor for list_topic_snapshots

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_list_topic_subscriptions(
        self,
        request: pubsub.ListTopicSubscriptionsRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[pubsub.ListTopicSubscriptionsRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for list_topic_subscriptions

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_list_topic_subscriptions(
        self, response: pubsub.ListTopicSubscriptionsResponse
    ) -> pubsub.ListTopicSubscriptionsResponse:
        """Post-rpc interceptor for list_topic_subscriptions

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_publish(
        self, request: pubsub.PublishRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[pubsub.PublishRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for publish

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_publish(self, response: pubsub.PublishResponse) -> pubsub.PublishResponse:
        """Post-rpc interceptor for publish

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_update_topic(
        self, request: pubsub.UpdateTopicRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[pubsub.UpdateTopicRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for update_topic

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_update_topic(self, response: pubsub.Topic) -> pubsub.Topic:
        """Post-rpc interceptor for update_topic

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_get_iam_policy(
        self,
        request: iam_policy_pb2.GetIamPolicyRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[iam_policy_pb2.GetIamPolicyRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for get_iam_policy

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_get_iam_policy(self, response: policy_pb2.Policy) -> policy_pb2.Policy:
        """Post-rpc interceptor for get_iam_policy

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_set_iam_policy(
        self,
        request: iam_policy_pb2.SetIamPolicyRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[iam_policy_pb2.SetIamPolicyRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for set_iam_policy

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_set_iam_policy(self, response: policy_pb2.Policy) -> policy_pb2.Policy:
        """Post-rpc interceptor for set_iam_policy

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response

    def pre_test_iam_permissions(
        self,
        request: iam_policy_pb2.TestIamPermissionsRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[iam_policy_pb2.TestIamPermissionsRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for test_iam_permissions

        Override in a subclass to manipulate the request or metadata
        before they are sent to the Publisher server.
        """
        return request, metadata

    def post_test_iam_permissions(
        self, response: iam_policy_pb2.TestIamPermissionsResponse
    ) -> iam_policy_pb2.TestIamPermissionsResponse:
        """Post-rpc interceptor for test_iam_permissions

        Override in a subclass to manipulate the response
        after it is returned by the Publisher server but before
        it is returned to user code.
        """
        return response


@dataclasses.dataclass
class PublisherRestStub:
    _session: AuthorizedSession
    _host: str
    _interceptor: PublisherRestInterceptor


class PublisherRestTransport(PublisherTransport):
    """REST backend transport for Publisher.

    The service that an application uses to manipulate topics,
    and to send messages to a topic.

    This class defines the same methods as the primary client, so the
    primary client can load the underlying transport implementation
    and call it.

    It sends JSON representations of protocol buffers over HTTP/1.1

    """

    def __init__(
        self,
        *,
        host: str = "pubsub.googleapis.com",
        credentials: Optional[ga_credentials.Credentials] = None,
        credentials_file: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        client_cert_source_for_mtls: Optional[Callable[[], Tuple[bytes, bytes]]] = None,
        quota_project_id: Optional[str] = None,
        client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
        always_use_jwt_access: Optional[bool] = False,
        url_scheme: str = "https",
        interceptor: Optional[PublisherRestInterceptor] = None,
        api_audience: Optional[str] = None,
    ) -> None:
        """Instantiate the transport.

        Args:
            host (Optional[str]):
                 The hostname to connect to.
            credentials (Optional[google.auth.credentials.Credentials]): The
                authorization credentials to attach to requests. These
                credentials identify the application to the service; if none
                are specified, the client will attempt to ascertain the
                credentials from the environment.

            credentials_file (Optional[str]): A file with credentials that can
                be loaded with :func:`google.auth.load_credentials_from_file`.
                This argument is ignored if ``channel`` is provided.
            scopes (Optional(Sequence[str])): A list of scopes. This argument is
                ignored if ``channel`` is provided.
            client_cert_source_for_mtls (Callable[[], Tuple[bytes, bytes]]): Client
                certificate to configure mutual TLS HTTP channel. It is ignored
                if ``channel`` is provided.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you are developing
                your own client library.
            always_use_jwt_access (Optional[bool]): Whether self signed JWT should
                be used for service account credentials.
            url_scheme: the protocol scheme for the API endpoint.  Normally
                "https", but for testing or local servers,
                "http" can be specified.
        """
        # Run the base constructor
        # TODO(yon-mg): resolve other ctor params i.e. scopes, quota, etc.
        # TODO: When custom host (api_endpoint) is set, `scopes` must *also* be set on the
        # credentials object
        maybe_url_match = re.match("^(?P<scheme>http(?:s)?://)?(?P<host>.*)$", host)
        if maybe_url_match is None:
            raise ValueError(
                f"Unexpected hostname structure: {host}"
            )  # pragma: NO COVER

        url_match_items = maybe_url_match.groupdict()

        host = f"{url_scheme}://{host}" if not url_match_items["scheme"] else host

        super().__init__(
            host=host,
            credentials=credentials,
            client_info=client_info,
            always_use_jwt_access=always_use_jwt_access,
            api_audience=api_audience,
        )
        self._session = AuthorizedSession(
            self._credentials, default_host=self.DEFAULT_HOST
        )
        if client_cert_source_for_mtls:
            self._session.configure_mtls_channel(client_cert_source_for_mtls)
        self._interceptor = interceptor or PublisherRestInterceptor()
        self._prep_wrapped_messages(client_info)

    class _CreateTopic(PublisherRestStub):
        def __hash__(self):
            return hash("CreateTopic")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.Topic,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.Topic:
            r"""Call the create topic method over HTTP.

            Args:
                request (~.pubsub.Topic):
                    The request object. A topic resource.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.Topic:
                    A topic resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "put",
                    "uri": "/v1/{name=projects/*/topics/*}",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_create_topic(request, metadata)
            pb_request = pubsub.Topic.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            # Jsonify the request body

            body = json_format.MessageToJson(
                transcoded_request["body"],
                including_default_value_fields=False,
                use_integers_for_enums=True,
            )
            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                data=body,
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.Topic()
            pb_resp = pubsub.Topic.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_create_topic(resp)
            return resp

    class _DeleteTopic(PublisherRestStub):
        def __hash__(self):
            return hash("DeleteTopic")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.DeleteTopicRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ):
            r"""Call the delete topic method over HTTP.

            Args:
                request (~.pubsub.DeleteTopicRequest):
                    The request object. Request for the ``DeleteTopic`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "delete",
                    "uri": "/v1/{topic=projects/*/topics/*}",
                },
            ]
            request, metadata = self._interceptor.pre_delete_topic(request, metadata)
            pb_request = pubsub.DeleteTopicRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

    class _DetachSubscription(PublisherRestStub):
        def __hash__(self):
            return hash("DetachSubscription")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.DetachSubscriptionRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.DetachSubscriptionResponse:
            r"""Call the detach subscription method over HTTP.

            Args:
                request (~.pubsub.DetachSubscriptionRequest):
                    The request object. Request for the DetachSubscription
                method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.DetachSubscriptionResponse:
                    Response for the DetachSubscription
                method. Reserved for future use.

            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{subscription=projects/*/subscriptions/*}:detach",
                },
            ]
            request, metadata = self._interceptor.pre_detach_subscription(
                request, metadata
            )
            pb_request = pubsub.DetachSubscriptionRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.DetachSubscriptionResponse()
            pb_resp = pubsub.DetachSubscriptionResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_detach_subscription(resp)
            return resp

    class _GetTopic(PublisherRestStub):
        def __hash__(self):
            return hash("GetTopic")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.GetTopicRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.Topic:
            r"""Call the get topic method over HTTP.

            Args:
                request (~.pubsub.GetTopicRequest):
                    The request object. Request for the GetTopic method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.Topic:
                    A topic resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{topic=projects/*/topics/*}",
                },
            ]
            request, metadata = self._interceptor.pre_get_topic(request, metadata)
            pb_request = pubsub.GetTopicRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.Topic()
            pb_resp = pubsub.Topic.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_get_topic(resp)
            return resp

    class _ListTopics(PublisherRestStub):
        def __hash__(self):
            return hash("ListTopics")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.ListTopicsRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.ListTopicsResponse:
            r"""Call the list topics method over HTTP.

            Args:
                request (~.pubsub.ListTopicsRequest):
                    The request object. Request for the ``ListTopics`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.ListTopicsResponse:
                    Response for the ``ListTopics`` method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{project=projects/*}/topics",
                },
            ]
            request, metadata = self._interceptor.pre_list_topics(request, metadata)
            pb_request = pubsub.ListTopicsRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.ListTopicsResponse()
            pb_resp = pubsub.ListTopicsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_list_topics(resp)
            return resp

    class _ListTopicSnapshots(PublisherRestStub):
        def __hash__(self):
            return hash("ListTopicSnapshots")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.ListTopicSnapshotsRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.ListTopicSnapshotsResponse:
            r"""Call the list topic snapshots method over HTTP.

            Args:
                request (~.pubsub.ListTopicSnapshotsRequest):
                    The request object. Request for the ``ListTopicSnapshots`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.ListTopicSnapshotsResponse:
                    Response for the ``ListTopicSnapshots`` method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{topic=projects/*/topics/*}/snapshots",
                },
            ]
            request, metadata = self._interceptor.pre_list_topic_snapshots(
                request, metadata
            )
            pb_request = pubsub.ListTopicSnapshotsRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.ListTopicSnapshotsResponse()
            pb_resp = pubsub.ListTopicSnapshotsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_list_topic_snapshots(resp)
            return resp

    class _ListTopicSubscriptions(PublisherRestStub):
        def __hash__(self):
            return hash("ListTopicSubscriptions")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.ListTopicSubscriptionsRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.ListTopicSubscriptionsResponse:
            r"""Call the list topic subscriptions method over HTTP.

            Args:
                request (~.pubsub.ListTopicSubscriptionsRequest):
                    The request object. Request for the ``ListTopicSubscriptions`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.ListTopicSubscriptionsResponse:
                    Response for the ``ListTopicSubscriptions`` method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{topic=projects/*/topics/*}/subscriptions",
                },
            ]
            request, metadata = self._interceptor.pre_list_topic_subscriptions(
                request, metadata
            )
            pb_request = pubsub.ListTopicSubscriptionsRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.ListTopicSubscriptionsResponse()
            pb_resp = pubsub.ListTopicSubscriptionsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_list_topic_subscriptions(resp)
            return resp

    class _Publish(PublisherRestStub):
        def __hash__(self):
            return hash("Publish")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.PublishRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.PublishResponse:
            r"""Call the publish method over HTTP.

            Args:
                request (~.pubsub.PublishRequest):
                    The request object. Request for the Publish method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.PublishResponse:
                    Response for the ``Publish`` method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{topic=projects/*/topics/*}:publish",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_publish(request, metadata)
            pb_request = pubsub.PublishRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            # Jsonify the request body

            body = json_format.MessageToJson(
                transcoded_request["body"],
                including_default_value_fields=False,
                use_integers_for_enums=True,
            )
            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                data=body,
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.PublishResponse()
            pb_resp = pubsub.PublishResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_publish(resp)
            return resp

    class _UpdateTopic(PublisherRestStub):
        def __hash__(self):
            return hash("UpdateTopic")

        __REQUIRED_FIELDS_DEFAULT_VALUES: Dict[str, Any] = {}

        @classmethod
        def _get_unset_required_fields(cls, message_dict):
            return {
                k: v
                for k, v in cls.__REQUIRED_FIELDS_DEFAULT_VALUES.items()
                if k not in message_dict
            }

        def __call__(
            self,
            request: pubsub.UpdateTopicRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> pubsub.Topic:
            r"""Call the update topic method over HTTP.

            Args:
                request (~.pubsub.UpdateTopicRequest):
                    The request object. Request for the UpdateTopic method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.pubsub.Topic:
                    A topic resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "patch",
                    "uri": "/v1/{topic.name=projects/*/topics/*}",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_update_topic(request, metadata)
            pb_request = pubsub.UpdateTopicRequest.pb(request)
            transcoded_request = path_template.transcode(http_options, pb_request)

            # Jsonify the request body

            body = json_format.MessageToJson(
                transcoded_request["body"],
                including_default_value_fields=False,
                use_integers_for_enums=True,
            )
            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(
                json_format.MessageToJson(
                    transcoded_request["query_params"],
                    including_default_value_fields=False,
                    use_integers_for_enums=True,
                )
            )
            query_params.update(self._get_unset_required_fields(query_params))

            query_params["$alt"] = "json;enum-encoding=int"

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"
            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params, strict=True),
                data=body,
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            # Return the response
            resp = pubsub.Topic()
            pb_resp = pubsub.Topic.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_update_topic(resp)
            return resp

    @property
    def create_topic(self) -> Callable[[pubsub.Topic], pubsub.Topic]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateTopic(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def delete_topic(self) -> Callable[[pubsub.DeleteTopicRequest], empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteTopic(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def detach_subscription(
        self,
    ) -> Callable[
        [pubsub.DetachSubscriptionRequest], pubsub.DetachSubscriptionResponse
    ]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DetachSubscription(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def get_topic(self) -> Callable[[pubsub.GetTopicRequest], pubsub.Topic]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetTopic(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def list_topics(
        self,
    ) -> Callable[[pubsub.ListTopicsRequest], pubsub.ListTopicsResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListTopics(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def list_topic_snapshots(
        self,
    ) -> Callable[
        [pubsub.ListTopicSnapshotsRequest], pubsub.ListTopicSnapshotsResponse
    ]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListTopicSnapshots(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def list_topic_subscriptions(
        self,
    ) -> Callable[
        [pubsub.ListTopicSubscriptionsRequest], pubsub.ListTopicSubscriptionsResponse
    ]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListTopicSubscriptions(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def publish(self) -> Callable[[pubsub.PublishRequest], pubsub.PublishResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._Publish(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def update_topic(self) -> Callable[[pubsub.UpdateTopicRequest], pubsub.Topic]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._UpdateTopic(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def get_iam_policy(self):
        return self._GetIamPolicy(self._session, self._host, self._interceptor)  # type: ignore

    class _GetIamPolicy(PublisherRestStub):
        def __call__(
            self,
            request: iam_policy_pb2.GetIamPolicyRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> policy_pb2.Policy:

            r"""Call the get iam policy method over HTTP.

            Args:
                request (iam_policy_pb2.GetIamPolicyRequest):
                    The request object for GetIamPolicy method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                policy_pb2.Policy: Response from GetIamPolicy method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{resource=projects/*/topics/*}:getIamPolicy",
                },
                {
                    "method": "get",
                    "uri": "/v1/{resource=projects/*/subscriptions/*}:getIamPolicy",
                },
                {
                    "method": "get",
                    "uri": "/v1/{resource=projects/*/snapshots/*}:getIamPolicy",
                },
                {
                    "method": "get",
                    "uri": "/v1/{resource=projects/*/schemas/*}:getIamPolicy",
                },
            ]

            request, metadata = self._interceptor.pre_get_iam_policy(request, metadata)
            request_kwargs = json_format.MessageToDict(request)
            transcoded_request = path_template.transcode(http_options, **request_kwargs)

            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(json.dumps(transcoded_request["query_params"]))

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"

            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params),
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            resp = policy_pb2.Policy()
            resp = json_format.Parse(response.content.decode("utf-8"), resp)
            resp = self._interceptor.post_get_iam_policy(resp)
            return resp

    @property
    def set_iam_policy(self):
        return self._SetIamPolicy(self._session, self._host, self._interceptor)  # type: ignore

    class _SetIamPolicy(PublisherRestStub):
        def __call__(
            self,
            request: iam_policy_pb2.SetIamPolicyRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> policy_pb2.Policy:

            r"""Call the set iam policy method over HTTP.

            Args:
                request (iam_policy_pb2.SetIamPolicyRequest):
                    The request object for SetIamPolicy method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                policy_pb2.Policy: Response from SetIamPolicy method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/topics/*}:setIamPolicy",
                    "body": "*",
                },
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/subscriptions/*}:setIamPolicy",
                    "body": "*",
                },
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/snapshots/*}:setIamPolicy",
                    "body": "*",
                },
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/schemas/*}:setIamPolicy",
                    "body": "*",
                },
            ]

            request, metadata = self._interceptor.pre_set_iam_policy(request, metadata)
            request_kwargs = json_format.MessageToDict(request)
            transcoded_request = path_template.transcode(http_options, **request_kwargs)

            body = json.dumps(transcoded_request["body"])
            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(json.dumps(transcoded_request["query_params"]))

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"

            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params),
                data=body,
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            resp = policy_pb2.Policy()
            resp = json_format.Parse(response.content.decode("utf-8"), resp)
            resp = self._interceptor.post_set_iam_policy(resp)
            return resp

    @property
    def test_iam_permissions(self):
        return self._TestIamPermissions(self._session, self._host, self._interceptor)  # type: ignore

    class _TestIamPermissions(PublisherRestStub):
        def __call__(
            self,
            request: iam_policy_pb2.TestIamPermissionsRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> iam_policy_pb2.TestIamPermissionsResponse:

            r"""Call the test iam permissions method over HTTP.

            Args:
                request (iam_policy_pb2.TestIamPermissionsRequest):
                    The request object for TestIamPermissions method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                iam_policy_pb2.TestIamPermissionsResponse: Response from TestIamPermissions method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/subscriptions/*}:testIamPermissions",
                    "body": "*",
                },
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/topics/*}:testIamPermissions",
                    "body": "*",
                },
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/snapshots/*}:testIamPermissions",
                    "body": "*",
                },
                {
                    "method": "post",
                    "uri": "/v1/{resource=projects/*/schemas/*}:testIamPermissions",
                    "body": "*",
                },
            ]

            request, metadata = self._interceptor.pre_test_iam_permissions(
                request, metadata
            )
            request_kwargs = json_format.MessageToDict(request)
            transcoded_request = path_template.transcode(http_options, **request_kwargs)

            body = json.dumps(transcoded_request["body"])
            uri = transcoded_request["uri"]
            method = transcoded_request["method"]

            # Jsonify the query params
            query_params = json.loads(json.dumps(transcoded_request["query_params"]))

            # Send the request
            headers = dict(metadata)
            headers["Content-Type"] = "application/json"

            response = getattr(self._session, method)(
                "{host}{uri}".format(host=self._host, uri=uri),
                timeout=timeout,
                headers=headers,
                params=rest_helpers.flatten_query_params(query_params),
                data=body,
            )

            # In case of error, raise the appropriate core_exceptions.GoogleAPICallError exception
            # subclass.
            if response.status_code >= 400:
                raise core_exceptions.from_http_response(response)

            resp = iam_policy_pb2.TestIamPermissionsResponse()
            resp = json_format.Parse(response.content.decode("utf-8"), resp)
            resp = self._interceptor.post_test_iam_permissions(resp)
            return resp

    @property
    def kind(self) -> str:
        return "rest"

    def close(self):
        self._session.close()


__all__ = ("PublisherRestTransport",)
