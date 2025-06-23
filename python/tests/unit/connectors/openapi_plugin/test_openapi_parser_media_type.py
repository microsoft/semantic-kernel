# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.openapi_plugin.openapi_parser import OpenApiParser


class TestOpenApiParserMediaTypeSupport:
    def test_exact_application_json(self):
        """Test that 'application/json' is supported."""
        assert OpenApiParser.is_supported_media_type("application/json") is True

    def test_exact_text_plain(self):
        """Test that 'text/plain' is supported."""
        assert OpenApiParser.is_supported_media_type("text/plain") is True

    def test_vendor_json_patch(self):
        """Test that 'application/json-patch+json' is supported."""
        assert OpenApiParser.is_supported_media_type("application/json-patch+json") is True

    def test_vendor_custom_json(self):
        """Test that 'application/vnd.api+json' is supported."""
        assert OpenApiParser.is_supported_media_type("application/vnd.api+json") is True

    def test_custom_json_with_dots(self):
        """Test that 'application/vnd.mycompany.v1+json' is supported."""
        assert OpenApiParser.is_supported_media_type("application/vnd.mycompany.v1+json") is True

    def test_invalid_type_xml(self):
        """Test that 'application/xml' is not supported."""
        assert OpenApiParser.is_supported_media_type("application/xml") is False

    def test_invalid_type_html(self):
        """Test that 'text/html' is not supported."""
        assert OpenApiParser.is_supported_media_type("text/html") is False

    def test_case_sensitivity(self):
        """Test that media type matching is case-sensitive."""
        assert OpenApiParser.is_supported_media_type("Application/Json") is False

    def test_empty_string(self):
        """Test that an empty string is not a supported media type."""
        assert OpenApiParser.is_supported_media_type("") is False

    def test_partial_match(self):
        """Test that partial matches like 'json' are not supported."""
        assert OpenApiParser.is_supported_media_type("json") is False

    def test_type_with_parameters(self):
        """Test that types with parameters (e.g., charset) are not supported."""
        assert OpenApiParser.is_supported_media_type("application/json; charset=utf-8") is False

    def test_pattern_logging(self):
        """Test that 'application/json' is supported (no log check)."""
        assert OpenApiParser.is_supported_media_type("application/json") is True

    def test_pattern_logging_no_match(self):
        """Test that 'application/xml' is not supported (no log check)."""
        assert OpenApiParser.is_supported_media_type("application/xml") is False
