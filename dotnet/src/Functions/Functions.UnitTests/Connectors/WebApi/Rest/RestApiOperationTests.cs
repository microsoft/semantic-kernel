// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Web;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Connectors.WebApi.Rest;

public class RestApiOperationTests
{
    [Fact]
    public void ShouldUseHostUrlIfNoOverrideProvided()
    {
        // Arrange
        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>()
        );

        var arguments = new Dictionary<string, string>();

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/", url.OriginalString);
    }

    [Fact]
    public void ShouldUseHostUrlOverrideIfProvided()
    {
        // Arrange
        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>()
        );

        var arguments = new Dictionary<string, string>
        {
            { "server-url", "https://fake-random-test-host-override" }
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host-override/", url.OriginalString);
    }

    [Fact]
    public void ShouldReplacePathParametersByValuesFromArguments()
    {
        // Arrange
        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/{fake-path-parameter}/other_fake_path_section",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter>(),
            new Dictionary<string, string>()
        );

        var arguments = new Dictionary<string, string>
        {
            { "fake-path-parameter", "fake-path-value" }
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/fake-path-value/other_fake_path_section", url.OriginalString);
    }

    [Fact]
    public void ShouldReplacePathParametersByDefaultValues()
    {
        // Arrange
        var parameterMetadata = new RestApiOperationParameter(
            "fake-path-parameter",
            "fake_type",
            true,
            RestApiOperationParameterLocation.Path,
            defaultValue: "fake-default-path");

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/{fake-path-parameter}/other_fake_path_section",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { parameterMetadata },
            new Dictionary<string, string>());

        var arguments = new Dictionary<string, string>();

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/fake-default-path/other_fake_path_section", url.OriginalString);
    }

    [Fact]
    public void ShouldAddQueryStringParametersAndUseValuesFromArguments()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            true,
            RestApiOperationParameterLocation.Query);

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            true,
            RestApiOperationParameterLocation.Query);

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { firstParameterMetadata, secondParameterMetadata },
            new Dictionary<string, string>());

        var arguments = new Dictionary<string, string>
        {
            { "p1", "v1" },
            { "p2", "v2" }
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/?p1=v1&p2=v2", url.OriginalString);
    }

    [Fact]
    public void ShouldAddQueryStringParametersAndUseTheirDefaultValues()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            true,
            RestApiOperationParameterLocation.Query,
            defaultValue: "dv1");

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            true,
            RestApiOperationParameterLocation.Query,
            defaultValue: "dv2");

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { firstParameterMetadata, secondParameterMetadata },
            new Dictionary<string, string>());

        var arguments = new Dictionary<string, string>();

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/?p1=dv1&p2=dv2", url.OriginalString);
    }

    [Fact]
    public void ShouldSkipNotRequiredQueryStringParametersIfTheirValuesMissing()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            false,
            RestApiOperationParameterLocation.Query);

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            false,
            RestApiOperationParameterLocation.Query);

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { firstParameterMetadata, secondParameterMetadata },
            new Dictionary<string, string>());

        var arguments = new Dictionary<string, string>
        {
            { "p2", "v2" }
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host/?p2=v2", url.OriginalString);
    }

    [Fact]
    public void ShouldThrowExceptionIfNoValueIsProvideForRequiredQueryStringParameter()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            true,
            RestApiOperationParameterLocation.Query);

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            false,
            RestApiOperationParameterLocation.Query);

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { firstParameterMetadata, secondParameterMetadata },
            new Dictionary<string, string>());

        var arguments = new Dictionary<string, string>
        {
            { "p2", "v2" }
        };

        //Act and assert
        Assert.Throws<SKException>(() => sut.BuildOperationUrl(arguments));
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInQueryStringValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter("fake_query_param", "string", false, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_query_param", $"fake_query_param_value{specialSymbol}" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.NotNull(url);

        Assert.EndsWith(encodedEquivalent, url.OriginalString, StringComparison.Ordinal);
    }

    [Fact]
    public void ShouldBuildResourceUrlThatIncludesAllUrlComponents()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            false,
            RestApiOperationParameterLocation.Query,
            defaultValue: "dv1");

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            false,
            RestApiOperationParameterLocation.Query);

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "{fake-path}/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { firstParameterMetadata, secondParameterMetadata },
            new Dictionary<string, string>());

        var arguments = new Dictionary<string, string>
        {
            { "server-url", "https://fake-random-test-host-override" },
            { "fake-path", "fake-path-value" },
            { "p2", "v2" }
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host-override/fake-path-value/?p1=dv1&p2=v2", url.OriginalString);
    }

    [Fact]
    public void ItShouldRenderHeaderValuesFromArguments()
    {
        // Arrange
        var rawHeaders = new Dictionary<string, string>
        {
            { "fake_header_one", string.Empty },
            { "fake_header_two", string.Empty }
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_header_one", "fake_header_one_value" },
            { "fake_header_two", "fake_header_two_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", new List<RestApiOperationParameter>(), rawHeaders);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_value", headerTwo);
    }

    [Fact]
    public void ItShouldUseHeaderValuesIfTheyAreAlreadyProvided()
    {
        // Arrange
        var rawHeaders = new Dictionary<string, string>
        {
            { "fake_header_one", "fake_header_one_value" },
            { "fake_header_two", "fake_header_two_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", new List<RestApiOperationParameter>(),
            rawHeaders);

        // Act
        var headers = sut.RenderHeaders(new Dictionary<string, string>());

        // Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_value", headerTwo);
    }

    [Fact]
    public void ItShouldThrowExceptionIfHeadersHaveNoValuesAndHeadersMetadataNotSupplied()
    {
        // Arrange
        var rawHeaders = new Dictionary<string, string>
        {
            { "fake_header_one", string.Empty },
            { "fake_header_two", string.Empty }
        };

        var metadata = new List<RestApiOperationParameter>();

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        // Act
        void Act() => sut.RenderHeaders(new Dictionary<string, string>());

        // Assert
        Assert.Throws<SKException>(Act);
    }

    [Fact]
    public void ShouldThrowExceptionIfNoValueProvidedForRequiredHeader()
    {
        // Arrange
        var rawHeaders = new Dictionary<string, string>
        {
            { "fake_header_one", string.Empty },
            { "fake_header_two", string.Empty }
        };

        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter("fake_header_one", "string", true, RestApiOperationParameterLocation.Header, RestApiOperationParameterStyle.Simple),
            new RestApiOperationParameter("fake_header_two", "string", false, RestApiOperationParameterLocation.Header, RestApiOperationParameterStyle.Simple)
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        // Act
        void Act() => sut.RenderHeaders(new Dictionary<string, string>());

        // Assert
        Assert.Throws<SKException>(Act);
    }

    [Fact]
    public void ItShouldSkipOptionalHeaderHavingNeitherValueNorDefaultValue()
    {
        // Arrange
        var rawHeaders = new Dictionary<string, string>
        {
            { "fake_header_one", string.Empty },
            { "fake_header_two", string.Empty }
        };

        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter("fake_header_one", "string", true, RestApiOperationParameterLocation.Header, RestApiOperationParameterStyle.Simple),
            new RestApiOperationParameter("fake_header_two", "string", false, RestApiOperationParameterLocation.Header, RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_header_one", "fake_header_one_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.Equal(1, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);
    }

    [Fact]
    public void ShouldUseDefaultValueForOptionalHeaderIfNoValueProvided()
    {
        // Arrange
        var rawHeaders = new Dictionary<string, string>
        {
            { "fake_header_one", string.Empty },
            { "fake_header_two", string.Empty }
        };

        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter("fake_header_one", "string", true, RestApiOperationParameterLocation.Header, RestApiOperationParameterStyle.Simple),
            new RestApiOperationParameter("fake_header_two", "string", false, RestApiOperationParameterLocation.Header, RestApiOperationParameterStyle.Simple, defaultValue: "fake_header_two_default_value")
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_header_one", "fake_header_one_value" } //Argument is only provided for the first parameter and not for the second one
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.Equal(2, headers.Count);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);

        var headerTwo = headers["fake_header_two"];
        Assert.Equal("fake_header_two_default_value", headerTwo);
    }

    [Fact]
    public void ItShouldNotWrapQueryStringValuesOfStringTypeIntoSingleQuotes()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter("fake_query_string_param", "string", false, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_query_string_param", "fake_query_string_param_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.NotNull(url);

        var parameterValue = HttpUtility.ParseQueryString(url.Query)["fake_query_string_param"];
        Assert.NotNull(parameterValue);
        Assert.Equal("fake_query_string_param_value", parameterValue); // Making sure that query string value of string type is not wrapped with quotes.
    }
}
