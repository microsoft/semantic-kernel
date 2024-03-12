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
import abc
from typing import Awaitable, Callable, Dict, Optional, Sequence, Union

from googlecloudsdk.generated_clients.gapic_clients.logging_v2 import gapic_version as package_version

import google.auth  # type: ignore
import google.api_core
from google.api_core import exceptions as core_exceptions
from google.api_core import gapic_v1
from google.api_core import retry as retries
from google.api_core import operations_v1
from google.auth import credentials as ga_credentials  # type: ignore
from google.oauth2 import service_account # type: ignore

from google.longrunning import operations_pb2 # type: ignore
from cloudsdk.google.protobuf import empty_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import logging_config

DEFAULT_CLIENT_INFO = gapic_v1.client_info.ClientInfo(gapic_version=package_version.__version__)


class ConfigServiceV2Transport(abc.ABC):
    """Abstract transport class for ConfigServiceV2."""

    AUTH_SCOPES = (
        'https://www.googleapis.com/auth/cloud-platform',
        'https://www.googleapis.com/auth/cloud-platform.read-only',
        'https://www.googleapis.com/auth/logging.admin',
        'https://www.googleapis.com/auth/logging.read',
    )

    DEFAULT_HOST: str = 'logging.googleapis.com'
    def __init__(
            self, *,
            host: str = DEFAULT_HOST,
            credentials: Optional[ga_credentials.Credentials] = None,
            credentials_file: Optional[str] = None,
            scopes: Optional[Sequence[str]] = None,
            quota_project_id: Optional[str] = None,
            client_info: gapic_v1.client_info.ClientInfo = DEFAULT_CLIENT_INFO,
            always_use_jwt_access: Optional[bool] = False,
            api_audience: Optional[str] = None,
            **kwargs,
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
                This argument is mutually exclusive with credentials.
            scopes (Optional[Sequence[str]]): A list of scopes.
            quota_project_id (Optional[str]): An optional project to use for billing
                and quota.
            client_info (google.api_core.gapic_v1.client_info.ClientInfo):
                The client info used to send a user-agent string along with
                API requests. If ``None``, then default info will be used.
                Generally, you only need to set this if you're developing
                your own client library.
            always_use_jwt_access (Optional[bool]): Whether self signed JWT should
                be used for service account credentials.
        """

        scopes_kwargs = {"scopes": scopes, "default_scopes": self.AUTH_SCOPES}

        # Save the scopes.
        self._scopes = scopes

        # If no credentials are provided, then determine the appropriate
        # defaults.
        if credentials and credentials_file:
            raise core_exceptions.DuplicateCredentialArgs("'credentials_file' and 'credentials' are mutually exclusive")

        if credentials_file is not None:
            credentials, _ = google.auth.load_credentials_from_file(
                                credentials_file,
                                **scopes_kwargs,
                                quota_project_id=quota_project_id
                            )
        elif credentials is None:
            credentials, _ = google.auth.default(**scopes_kwargs, quota_project_id=quota_project_id)
            # Don't apply audience if the credentials file passed from user.
            if hasattr(credentials, "with_gdch_audience"):
                credentials = credentials.with_gdch_audience(api_audience if api_audience else host)

        # If the credentials are service account credentials, then always try to use self signed JWT.
        if always_use_jwt_access and isinstance(credentials, service_account.Credentials) and hasattr(service_account.Credentials, "with_always_use_jwt_access"):
            credentials = credentials.with_always_use_jwt_access(True)

        # Save the credentials.
        self._credentials = credentials

        # Save the hostname. Default to port 443 (HTTPS) if none is specified.
        if ':' not in host:
            host += ':443'
        self._host = host

    def _prep_wrapped_messages(self, client_info):
        # Precompute the wrapped methods.
        self._wrapped_methods = {
            self.list_buckets: gapic_v1.method.wrap_method(
                self.list_buckets,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_bucket: gapic_v1.method.wrap_method(
                self.get_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.create_bucket_async: gapic_v1.method.wrap_method(
                self.create_bucket_async,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_bucket_async: gapic_v1.method.wrap_method(
                self.update_bucket_async,
                default_timeout=None,
                client_info=client_info,
            ),
            self.create_bucket: gapic_v1.method.wrap_method(
                self.create_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_bucket: gapic_v1.method.wrap_method(
                self.update_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.delete_bucket: gapic_v1.method.wrap_method(
                self.delete_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.undelete_bucket: gapic_v1.method.wrap_method(
                self.undelete_bucket,
                default_timeout=None,
                client_info=client_info,
            ),
            self.list_views: gapic_v1.method.wrap_method(
                self.list_views,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_view: gapic_v1.method.wrap_method(
                self.get_view,
                default_timeout=None,
                client_info=client_info,
            ),
            self.create_view: gapic_v1.method.wrap_method(
                self.create_view,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_view: gapic_v1.method.wrap_method(
                self.update_view,
                default_timeout=None,
                client_info=client_info,
            ),
            self.delete_view: gapic_v1.method.wrap_method(
                self.delete_view,
                default_timeout=None,
                client_info=client_info,
            ),
            self.list_exclusions: gapic_v1.method.wrap_method(
                self.list_exclusions,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.get_exclusion: gapic_v1.method.wrap_method(
                self.get_exclusion,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.create_exclusion: gapic_v1.method.wrap_method(
                self.create_exclusion,
                default_timeout=120.0,
                client_info=client_info,
            ),
            self.update_exclusion: gapic_v1.method.wrap_method(
                self.update_exclusion,
                default_timeout=120.0,
                client_info=client_info,
            ),
            self.delete_exclusion: gapic_v1.method.wrap_method(
                self.delete_exclusion,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.list_sinks: gapic_v1.method.wrap_method(
                self.list_sinks,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.get_sink: gapic_v1.method.wrap_method(
                self.get_sink,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.create_sink: gapic_v1.method.wrap_method(
                self.create_sink,
                default_timeout=120.0,
                client_info=client_info,
            ),
            self.update_sink: gapic_v1.method.wrap_method(
                self.update_sink,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.delete_sink: gapic_v1.method.wrap_method(
                self.delete_sink,
                default_retry=retries.Retry(
initial=0.1,maximum=60.0,multiplier=1.3,                    predicate=retries.if_exception_type(
                        core_exceptions.DeadlineExceeded,
                        core_exceptions.InternalServerError,
                        core_exceptions.ServiceUnavailable,
                    ),
                    deadline=60.0,
                ),
                default_timeout=60.0,
                client_info=client_info,
            ),
            self.list_links: gapic_v1.method.wrap_method(
                self.list_links,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_link: gapic_v1.method.wrap_method(
                self.get_link,
                default_timeout=None,
                client_info=client_info,
            ),
            self.create_link: gapic_v1.method.wrap_method(
                self.create_link,
                default_timeout=None,
                client_info=client_info,
            ),
            self.delete_link: gapic_v1.method.wrap_method(
                self.delete_link,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_cmek_settings: gapic_v1.method.wrap_method(
                self.get_cmek_settings,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_cmek_settings: gapic_v1.method.wrap_method(
                self.update_cmek_settings,
                default_timeout=None,
                client_info=client_info,
            ),
            self.get_settings: gapic_v1.method.wrap_method(
                self.get_settings,
                default_timeout=None,
                client_info=client_info,
            ),
            self.update_settings: gapic_v1.method.wrap_method(
                self.update_settings,
                default_timeout=None,
                client_info=client_info,
            ),
            self.list_saved_queries: gapic_v1.method.wrap_method(
                self.list_saved_queries,
                default_timeout=None,
                client_info=client_info,
            ),
            self.create_saved_query: gapic_v1.method.wrap_method(
                self.create_saved_query,
                default_timeout=None,
                client_info=client_info,
            ),
            self.delete_saved_query: gapic_v1.method.wrap_method(
                self.delete_saved_query,
                default_timeout=None,
                client_info=client_info,
            ),
            self.list_recent_queries: gapic_v1.method.wrap_method(
                self.list_recent_queries,
                default_timeout=None,
                client_info=client_info,
            ),
            self.copy_log_entries: gapic_v1.method.wrap_method(
                self.copy_log_entries,
                default_timeout=None,
                client_info=client_info,
            ),
         }

    def close(self):
        """Closes resources associated with the transport.

       .. warning::
            Only call this method if the transport is NOT shared
            with other clients - this may cause errors in other clients!
        """
        raise NotImplementedError()

    @property
    def operations_client(self):
        """Return the client designed to process long-running operations."""
        raise NotImplementedError()

    @property
    def list_buckets(self) -> Callable[
            [logging_config.ListBucketsRequest],
            Union[
                logging_config.ListBucketsResponse,
                Awaitable[logging_config.ListBucketsResponse]
            ]]:
        raise NotImplementedError()

    @property
    def get_bucket(self) -> Callable[
            [logging_config.GetBucketRequest],
            Union[
                logging_config.LogBucket,
                Awaitable[logging_config.LogBucket]
            ]]:
        raise NotImplementedError()

    @property
    def create_bucket_async(self) -> Callable[
            [logging_config.CreateBucketRequest],
            Union[
                operations_pb2.Operation,
                Awaitable[operations_pb2.Operation]
            ]]:
        raise NotImplementedError()

    @property
    def update_bucket_async(self) -> Callable[
            [logging_config.UpdateBucketRequest],
            Union[
                operations_pb2.Operation,
                Awaitable[operations_pb2.Operation]
            ]]:
        raise NotImplementedError()

    @property
    def create_bucket(self) -> Callable[
            [logging_config.CreateBucketRequest],
            Union[
                logging_config.LogBucket,
                Awaitable[logging_config.LogBucket]
            ]]:
        raise NotImplementedError()

    @property
    def update_bucket(self) -> Callable[
            [logging_config.UpdateBucketRequest],
            Union[
                logging_config.LogBucket,
                Awaitable[logging_config.LogBucket]
            ]]:
        raise NotImplementedError()

    @property
    def delete_bucket(self) -> Callable[
            [logging_config.DeleteBucketRequest],
            Union[
                empty_pb2.Empty,
                Awaitable[empty_pb2.Empty]
            ]]:
        raise NotImplementedError()

    @property
    def undelete_bucket(self) -> Callable[
            [logging_config.UndeleteBucketRequest],
            Union[
                empty_pb2.Empty,
                Awaitable[empty_pb2.Empty]
            ]]:
        raise NotImplementedError()

    @property
    def list_views(self) -> Callable[
            [logging_config.ListViewsRequest],
            Union[
                logging_config.ListViewsResponse,
                Awaitable[logging_config.ListViewsResponse]
            ]]:
        raise NotImplementedError()

    @property
    def get_view(self) -> Callable[
            [logging_config.GetViewRequest],
            Union[
                logging_config.LogView,
                Awaitable[logging_config.LogView]
            ]]:
        raise NotImplementedError()

    @property
    def create_view(self) -> Callable[
            [logging_config.CreateViewRequest],
            Union[
                logging_config.LogView,
                Awaitable[logging_config.LogView]
            ]]:
        raise NotImplementedError()

    @property
    def update_view(self) -> Callable[
            [logging_config.UpdateViewRequest],
            Union[
                logging_config.LogView,
                Awaitable[logging_config.LogView]
            ]]:
        raise NotImplementedError()

    @property
    def delete_view(self) -> Callable[
            [logging_config.DeleteViewRequest],
            Union[
                empty_pb2.Empty,
                Awaitable[empty_pb2.Empty]
            ]]:
        raise NotImplementedError()

    @property
    def list_exclusions(self) -> Callable[
            [logging_config.ListExclusionsRequest],
            Union[
                logging_config.ListExclusionsResponse,
                Awaitable[logging_config.ListExclusionsResponse]
            ]]:
        raise NotImplementedError()

    @property
    def get_exclusion(self) -> Callable[
            [logging_config.GetExclusionRequest],
            Union[
                logging_config.LogExclusion,
                Awaitable[logging_config.LogExclusion]
            ]]:
        raise NotImplementedError()

    @property
    def create_exclusion(self) -> Callable[
            [logging_config.CreateExclusionRequest],
            Union[
                logging_config.LogExclusion,
                Awaitable[logging_config.LogExclusion]
            ]]:
        raise NotImplementedError()

    @property
    def update_exclusion(self) -> Callable[
            [logging_config.UpdateExclusionRequest],
            Union[
                logging_config.LogExclusion,
                Awaitable[logging_config.LogExclusion]
            ]]:
        raise NotImplementedError()

    @property
    def delete_exclusion(self) -> Callable[
            [logging_config.DeleteExclusionRequest],
            Union[
                empty_pb2.Empty,
                Awaitable[empty_pb2.Empty]
            ]]:
        raise NotImplementedError()

    @property
    def list_sinks(self) -> Callable[
            [logging_config.ListSinksRequest],
            Union[
                logging_config.ListSinksResponse,
                Awaitable[logging_config.ListSinksResponse]
            ]]:
        raise NotImplementedError()

    @property
    def get_sink(self) -> Callable[
            [logging_config.GetSinkRequest],
            Union[
                logging_config.LogSink,
                Awaitable[logging_config.LogSink]
            ]]:
        raise NotImplementedError()

    @property
    def create_sink(self) -> Callable[
            [logging_config.CreateSinkRequest],
            Union[
                logging_config.LogSink,
                Awaitable[logging_config.LogSink]
            ]]:
        raise NotImplementedError()

    @property
    def update_sink(self) -> Callable[
            [logging_config.UpdateSinkRequest],
            Union[
                logging_config.LogSink,
                Awaitable[logging_config.LogSink]
            ]]:
        raise NotImplementedError()

    @property
    def delete_sink(self) -> Callable[
            [logging_config.DeleteSinkRequest],
            Union[
                empty_pb2.Empty,
                Awaitable[empty_pb2.Empty]
            ]]:
        raise NotImplementedError()

    @property
    def list_links(self) -> Callable[
            [logging_config.ListLinksRequest],
            Union[
                logging_config.ListLinksResponse,
                Awaitable[logging_config.ListLinksResponse]
            ]]:
        raise NotImplementedError()

    @property
    def get_link(self) -> Callable[
            [logging_config.GetLinkRequest],
            Union[
                logging_config.Link,
                Awaitable[logging_config.Link]
            ]]:
        raise NotImplementedError()

    @property
    def create_link(self) -> Callable[
            [logging_config.CreateLinkRequest],
            Union[
                operations_pb2.Operation,
                Awaitable[operations_pb2.Operation]
            ]]:
        raise NotImplementedError()

    @property
    def delete_link(self) -> Callable[
            [logging_config.DeleteLinkRequest],
            Union[
                operations_pb2.Operation,
                Awaitable[operations_pb2.Operation]
            ]]:
        raise NotImplementedError()

    @property
    def get_cmek_settings(self) -> Callable[
            [logging_config.GetCmekSettingsRequest],
            Union[
                logging_config.CmekSettings,
                Awaitable[logging_config.CmekSettings]
            ]]:
        raise NotImplementedError()

    @property
    def update_cmek_settings(self) -> Callable[
            [logging_config.UpdateCmekSettingsRequest],
            Union[
                logging_config.CmekSettings,
                Awaitable[logging_config.CmekSettings]
            ]]:
        raise NotImplementedError()

    @property
    def get_settings(self) -> Callable[
            [logging_config.GetSettingsRequest],
            Union[
                logging_config.Settings,
                Awaitable[logging_config.Settings]
            ]]:
        raise NotImplementedError()

    @property
    def update_settings(self) -> Callable[
            [logging_config.UpdateSettingsRequest],
            Union[
                logging_config.Settings,
                Awaitable[logging_config.Settings]
            ]]:
        raise NotImplementedError()

    @property
    def list_saved_queries(self) -> Callable[
            [logging_config.ListSavedQueriesRequest],
            Union[
                logging_config.ListSavedQueriesResponse,
                Awaitable[logging_config.ListSavedQueriesResponse]
            ]]:
        raise NotImplementedError()

    @property
    def create_saved_query(self) -> Callable[
            [logging_config.CreateSavedQueryRequest],
            Union[
                logging_config.SavedQuery,
                Awaitable[logging_config.SavedQuery]
            ]]:
        raise NotImplementedError()

    @property
    def delete_saved_query(self) -> Callable[
            [logging_config.DeleteSavedQueryRequest],
            Union[
                empty_pb2.Empty,
                Awaitable[empty_pb2.Empty]
            ]]:
        raise NotImplementedError()

    @property
    def list_recent_queries(self) -> Callable[
            [logging_config.ListRecentQueriesRequest],
            Union[
                logging_config.ListRecentQueriesResponse,
                Awaitable[logging_config.ListRecentQueriesResponse]
            ]]:
        raise NotImplementedError()

    @property
    def copy_log_entries(self) -> Callable[
            [logging_config.CopyLogEntriesRequest],
            Union[
                operations_pb2.Operation,
                Awaitable[operations_pb2.Operation]
            ]]:
        raise NotImplementedError()

    @property
    def kind(self) -> str:
        raise NotImplementedError()


__all__ = (
    'ConfigServiceV2Transport',
)
