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
from google.pubsub_v1.types import schema
from google.pubsub_v1.types import schema as gp_schema

from .base import (
    SchemaServiceTransport,
    DEFAULT_CLIENT_INFO as BASE_DEFAULT_CLIENT_INFO,
)


DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(
    gapic_version=BASE_DEFAULT_CLIENT_INFO.gapic_version,
    grpc_version=None,
    rest_version=requests_version,
)


class SchemaServiceRestInterceptor:
    """Interceptor for SchemaService.

    Interceptors are used to manipulate requests, request metadata, and responses
    in arbitrary ways.
    Example use cases include:
    * Logging
    * Verifying requests according to service or custom semantics
    * Stripping extraneous information from responses

    These use cases and more can be enabled by injecting an
    instance of a custom subclass when constructing the SchemaServiceRestTransport.

    .. code-block:: python
        class MyCustomSchemaServiceInterceptor(SchemaServiceRestInterceptor):
            def pre_commit_schema(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_commit_schema(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_create_schema(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_create_schema(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_delete_schema(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def pre_delete_schema_revision(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_delete_schema_revision(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_get_schema(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_get_schema(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_schema_revisions(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_schema_revisions(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_list_schemas(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_list_schemas(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_rollback_schema(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_rollback_schema(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_validate_message(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_validate_message(self, response):
                logging.log(f"Received response: {response}")
                return response

            def pre_validate_schema(self, request, metadata):
                logging.log(f"Received request: {request}")
                return request, metadata

            def post_validate_schema(self, response):
                logging.log(f"Received response: {response}")
                return response

        transport = SchemaServiceRestTransport(interceptor=MyCustomSchemaServiceInterceptor())
        client = SchemaServiceClient(transport=transport)


    """

    def pre_commit_schema(
        self,
        request: gp_schema.CommitSchemaRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[gp_schema.CommitSchemaRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for commit_schema

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_commit_schema(self, response: gp_schema.Schema) -> gp_schema.Schema:
        """Post-rpc interceptor for commit_schema

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_create_schema(
        self,
        request: gp_schema.CreateSchemaRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[gp_schema.CreateSchemaRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for create_schema

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_create_schema(self, response: gp_schema.Schema) -> gp_schema.Schema:
        """Post-rpc interceptor for create_schema

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_delete_schema(
        self, request: schema.DeleteSchemaRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[schema.DeleteSchemaRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for delete_schema

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def pre_delete_schema_revision(
        self,
        request: schema.DeleteSchemaRevisionRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[schema.DeleteSchemaRevisionRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for delete_schema_revision

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_delete_schema_revision(self, response: schema.Schema) -> schema.Schema:
        """Post-rpc interceptor for delete_schema_revision

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_get_schema(
        self, request: schema.GetSchemaRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[schema.GetSchemaRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for get_schema

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_get_schema(self, response: schema.Schema) -> schema.Schema:
        """Post-rpc interceptor for get_schema

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_list_schema_revisions(
        self,
        request: schema.ListSchemaRevisionsRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[schema.ListSchemaRevisionsRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for list_schema_revisions

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_list_schema_revisions(
        self, response: schema.ListSchemaRevisionsResponse
    ) -> schema.ListSchemaRevisionsResponse:
        """Post-rpc interceptor for list_schema_revisions

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_list_schemas(
        self, request: schema.ListSchemasRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[schema.ListSchemasRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for list_schemas

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_list_schemas(
        self, response: schema.ListSchemasResponse
    ) -> schema.ListSchemasResponse:
        """Post-rpc interceptor for list_schemas

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_rollback_schema(
        self, request: schema.RollbackSchemaRequest, metadata: Sequence[Tuple[str, str]]
    ) -> Tuple[schema.RollbackSchemaRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for rollback_schema

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_rollback_schema(self, response: schema.Schema) -> schema.Schema:
        """Post-rpc interceptor for rollback_schema

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_validate_message(
        self,
        request: schema.ValidateMessageRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[schema.ValidateMessageRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for validate_message

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_validate_message(
        self, response: schema.ValidateMessageResponse
    ) -> schema.ValidateMessageResponse:
        """Post-rpc interceptor for validate_message

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response

    def pre_validate_schema(
        self,
        request: gp_schema.ValidateSchemaRequest,
        metadata: Sequence[Tuple[str, str]],
    ) -> Tuple[gp_schema.ValidateSchemaRequest, Sequence[Tuple[str, str]]]:
        """Pre-rpc interceptor for validate_schema

        Override in a subclass to manipulate the request or metadata
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_validate_schema(
        self, response: gp_schema.ValidateSchemaResponse
    ) -> gp_schema.ValidateSchemaResponse:
        """Post-rpc interceptor for validate_schema

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
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
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_get_iam_policy(self, response: policy_pb2.Policy) -> policy_pb2.Policy:
        """Post-rpc interceptor for get_iam_policy

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
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
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_set_iam_policy(self, response: policy_pb2.Policy) -> policy_pb2.Policy:
        """Post-rpc interceptor for set_iam_policy

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
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
        before they are sent to the SchemaService server.
        """
        return request, metadata

    def post_test_iam_permissions(
        self, response: iam_policy_pb2.TestIamPermissionsResponse
    ) -> iam_policy_pb2.TestIamPermissionsResponse:
        """Post-rpc interceptor for test_iam_permissions

        Override in a subclass to manipulate the response
        after it is returned by the SchemaService server but before
        it is returned to user code.
        """
        return response


@dataclasses.dataclass
class SchemaServiceRestStub:
    _session: AuthorizedSession
    _host: str
    _interceptor: SchemaServiceRestInterceptor


class SchemaServiceRestTransport(SchemaServiceTransport):
    """REST backend transport for SchemaService.

    Service for doing schema-related operations.

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
        interceptor: Optional[SchemaServiceRestInterceptor] = None,
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
        self._interceptor = interceptor or SchemaServiceRestInterceptor()
        self._prep_wrapped_messages(client_info)

    class _CommitSchema(SchemaServiceRestStub):
        def __hash__(self):
            return hash("CommitSchema")

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
            request: gp_schema.CommitSchemaRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> gp_schema.Schema:
            r"""Call the commit schema method over HTTP.

            Args:
                request (~.gp_schema.CommitSchemaRequest):
                    The request object. Request for CommitSchema method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.gp_schema.Schema:
                    A schema resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{name=projects/*/schemas/*}:commit",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_commit_schema(request, metadata)
            pb_request = gp_schema.CommitSchemaRequest.pb(request)
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
            resp = gp_schema.Schema()
            pb_resp = gp_schema.Schema.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_commit_schema(resp)
            return resp

    class _CreateSchema(SchemaServiceRestStub):
        def __hash__(self):
            return hash("CreateSchema")

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
            request: gp_schema.CreateSchemaRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> gp_schema.Schema:
            r"""Call the create schema method over HTTP.

            Args:
                request (~.gp_schema.CreateSchemaRequest):
                    The request object. Request for the CreateSchema method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.gp_schema.Schema:
                    A schema resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{parent=projects/*}/schemas",
                    "body": "schema",
                },
            ]
            request, metadata = self._interceptor.pre_create_schema(request, metadata)
            pb_request = gp_schema.CreateSchemaRequest.pb(request)
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
            resp = gp_schema.Schema()
            pb_resp = gp_schema.Schema.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_create_schema(resp)
            return resp

    class _DeleteSchema(SchemaServiceRestStub):
        def __hash__(self):
            return hash("DeleteSchema")

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
            request: schema.DeleteSchemaRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ):
            r"""Call the delete schema method over HTTP.

            Args:
                request (~.schema.DeleteSchemaRequest):
                    The request object. Request for the ``DeleteSchema`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "delete",
                    "uri": "/v1/{name=projects/*/schemas/*}",
                },
            ]
            request, metadata = self._interceptor.pre_delete_schema(request, metadata)
            pb_request = schema.DeleteSchemaRequest.pb(request)
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

    class _DeleteSchemaRevision(SchemaServiceRestStub):
        def __hash__(self):
            return hash("DeleteSchemaRevision")

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
            request: schema.DeleteSchemaRevisionRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> schema.Schema:
            r"""Call the delete schema revision method over HTTP.

            Args:
                request (~.schema.DeleteSchemaRevisionRequest):
                    The request object. Request for the ``DeleteSchemaRevision`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.schema.Schema:
                    A schema resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "delete",
                    "uri": "/v1/{name=projects/*/schemas/*}:deleteRevision",
                },
            ]
            request, metadata = self._interceptor.pre_delete_schema_revision(
                request, metadata
            )
            pb_request = schema.DeleteSchemaRevisionRequest.pb(request)
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
            resp = schema.Schema()
            pb_resp = schema.Schema.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_delete_schema_revision(resp)
            return resp

    class _GetSchema(SchemaServiceRestStub):
        def __hash__(self):
            return hash("GetSchema")

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
            request: schema.GetSchemaRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> schema.Schema:
            r"""Call the get schema method over HTTP.

            Args:
                request (~.schema.GetSchemaRequest):
                    The request object. Request for the GetSchema method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.schema.Schema:
                    A schema resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{name=projects/*/schemas/*}",
                },
            ]
            request, metadata = self._interceptor.pre_get_schema(request, metadata)
            pb_request = schema.GetSchemaRequest.pb(request)
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
            resp = schema.Schema()
            pb_resp = schema.Schema.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_get_schema(resp)
            return resp

    class _ListSchemaRevisions(SchemaServiceRestStub):
        def __hash__(self):
            return hash("ListSchemaRevisions")

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
            request: schema.ListSchemaRevisionsRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> schema.ListSchemaRevisionsResponse:
            r"""Call the list schema revisions method over HTTP.

            Args:
                request (~.schema.ListSchemaRevisionsRequest):
                    The request object. Request for the ``ListSchemaRevisions`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.schema.ListSchemaRevisionsResponse:
                    Response for the ``ListSchemaRevisions`` method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{name=projects/*/schemas/*}:listRevisions",
                },
            ]
            request, metadata = self._interceptor.pre_list_schema_revisions(
                request, metadata
            )
            pb_request = schema.ListSchemaRevisionsRequest.pb(request)
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
            resp = schema.ListSchemaRevisionsResponse()
            pb_resp = schema.ListSchemaRevisionsResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_list_schema_revisions(resp)
            return resp

    class _ListSchemas(SchemaServiceRestStub):
        def __hash__(self):
            return hash("ListSchemas")

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
            request: schema.ListSchemasRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> schema.ListSchemasResponse:
            r"""Call the list schemas method over HTTP.

            Args:
                request (~.schema.ListSchemasRequest):
                    The request object. Request for the ``ListSchemas`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.schema.ListSchemasResponse:
                    Response for the ``ListSchemas`` method.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "get",
                    "uri": "/v1/{parent=projects/*}/schemas",
                },
            ]
            request, metadata = self._interceptor.pre_list_schemas(request, metadata)
            pb_request = schema.ListSchemasRequest.pb(request)
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
            resp = schema.ListSchemasResponse()
            pb_resp = schema.ListSchemasResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_list_schemas(resp)
            return resp

    class _RollbackSchema(SchemaServiceRestStub):
        def __hash__(self):
            return hash("RollbackSchema")

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
            request: schema.RollbackSchemaRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> schema.Schema:
            r"""Call the rollback schema method over HTTP.

            Args:
                request (~.schema.RollbackSchemaRequest):
                    The request object. Request for the ``RollbackSchema`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.schema.Schema:
                    A schema resource.
            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{name=projects/*/schemas/*}:rollback",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_rollback_schema(request, metadata)
            pb_request = schema.RollbackSchemaRequest.pb(request)
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
            resp = schema.Schema()
            pb_resp = schema.Schema.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_rollback_schema(resp)
            return resp

    class _ValidateMessage(SchemaServiceRestStub):
        def __hash__(self):
            return hash("ValidateMessage")

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
            request: schema.ValidateMessageRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> schema.ValidateMessageResponse:
            r"""Call the validate message method over HTTP.

            Args:
                request (~.schema.ValidateMessageRequest):
                    The request object. Request for the ``ValidateMessage`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.schema.ValidateMessageResponse:
                    Response for the ``ValidateMessage`` method. Empty for
                now.

            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{parent=projects/*}/schemas:validateMessage",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_validate_message(
                request, metadata
            )
            pb_request = schema.ValidateMessageRequest.pb(request)
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
            resp = schema.ValidateMessageResponse()
            pb_resp = schema.ValidateMessageResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_validate_message(resp)
            return resp

    class _ValidateSchema(SchemaServiceRestStub):
        def __hash__(self):
            return hash("ValidateSchema")

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
            request: gp_schema.ValidateSchemaRequest,
            *,
            retry: OptionalRetry = gapic_v1.method.DEFAULT,
            timeout: Optional[float] = None,
            metadata: Sequence[Tuple[str, str]] = (),
        ) -> gp_schema.ValidateSchemaResponse:
            r"""Call the validate schema method over HTTP.

            Args:
                request (~.gp_schema.ValidateSchemaRequest):
                    The request object. Request for the ``ValidateSchema`` method.
                retry (google.api_core.retry.Retry): Designation of what errors, if any,
                    should be retried.
                timeout (float): The timeout for this request.
                metadata (Sequence[Tuple[str, str]]): Strings which should be
                    sent along with the request as metadata.

            Returns:
                ~.gp_schema.ValidateSchemaResponse:
                    Response for the ``ValidateSchema`` method. Empty for
                now.

            """

            http_options: List[Dict[str, str]] = [
                {
                    "method": "post",
                    "uri": "/v1/{parent=projects/*}/schemas:validate",
                    "body": "*",
                },
            ]
            request, metadata = self._interceptor.pre_validate_schema(request, metadata)
            pb_request = gp_schema.ValidateSchemaRequest.pb(request)
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
            resp = gp_schema.ValidateSchemaResponse()
            pb_resp = gp_schema.ValidateSchemaResponse.pb(resp)

            json_format.Parse(response.content, pb_resp, ignore_unknown_fields=True)
            resp = self._interceptor.post_validate_schema(resp)
            return resp

    @property
    def commit_schema(
        self,
    ) -> Callable[[gp_schema.CommitSchemaRequest], gp_schema.Schema]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CommitSchema(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def create_schema(
        self,
    ) -> Callable[[gp_schema.CreateSchemaRequest], gp_schema.Schema]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._CreateSchema(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def delete_schema(self) -> Callable[[schema.DeleteSchemaRequest], empty_pb2.Empty]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteSchema(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def delete_schema_revision(
        self,
    ) -> Callable[[schema.DeleteSchemaRevisionRequest], schema.Schema]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._DeleteSchemaRevision(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def get_schema(self) -> Callable[[schema.GetSchemaRequest], schema.Schema]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._GetSchema(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def list_schema_revisions(
        self,
    ) -> Callable[
        [schema.ListSchemaRevisionsRequest], schema.ListSchemaRevisionsResponse
    ]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListSchemaRevisions(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def list_schemas(
        self,
    ) -> Callable[[schema.ListSchemasRequest], schema.ListSchemasResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ListSchemas(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def rollback_schema(
        self,
    ) -> Callable[[schema.RollbackSchemaRequest], schema.Schema]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._RollbackSchema(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def validate_message(
        self,
    ) -> Callable[[schema.ValidateMessageRequest], schema.ValidateMessageResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ValidateMessage(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def validate_schema(
        self,
    ) -> Callable[[gp_schema.ValidateSchemaRequest], gp_schema.ValidateSchemaResponse]:
        # The return type is fine, but mypy isn't sophisticated enough to determine what's going on here.
        # In C++ this would require a dynamic_cast
        return self._ValidateSchema(self._session, self._host, self._interceptor)  # type: ignore

    @property
    def get_iam_policy(self):
        return self._GetIamPolicy(self._session, self._host, self._interceptor)  # type: ignore

    class _GetIamPolicy(SchemaServiceRestStub):
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

    class _SetIamPolicy(SchemaServiceRestStub):
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

    class _TestIamPermissions(SchemaServiceRestStub):
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


__all__ = ("SchemaServiceRestTransport",)
