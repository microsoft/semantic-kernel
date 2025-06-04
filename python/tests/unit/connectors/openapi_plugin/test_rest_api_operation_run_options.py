# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.openapi_plugin.models.rest_api_run_options import RestApiRunOptions


def test_initialization():
    server_url_override = "http://example.com"
    api_host_url = "http://example.com"

    rest_api_operation_run_options = RestApiRunOptions(server_url_override, api_host_url)

    assert rest_api_operation_run_options.server_url_override == server_url_override
    assert rest_api_operation_run_options.api_host_url == api_host_url


def test_initialization_no_params():
    rest_api_operation_run_options = RestApiRunOptions()

    assert rest_api_operation_run_options.server_url_override is None
    assert rest_api_operation_run_options.api_host_url is None
