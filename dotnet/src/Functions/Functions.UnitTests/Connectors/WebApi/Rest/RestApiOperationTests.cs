// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.Connectors.WebApi.Rest;

public class RestApiOperationTests
{
    [Fact]
    public void ItShouldUseHostUrlIfNoOverrideProvided()
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
    public void ItShouldUseHostUrlOverrideIfProvided()
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
    public void ItShouldReplacePathParametersByValuesFromArguments()
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
    public void ItShouldReplacePathParametersByDefaultValues()
    {
        // Arrange
        var parameterMetadata = new RestApiOperationParameter(
            name: "fake-path-parameter",
            type: "fake_type",
            isRequired: true,
            explode: false,
            location: RestApiOperationParameterLocation.Path,
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
    public void ShouldBuildResourceUrlWithoutQueryString()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            name: "p1",
            type: "fake_type",
            isRequired: false,
            explode: false,
            location: RestApiOperationParameterLocation.Query,
            defaultValue: "dv1");

        var secondParameterMetadata = new RestApiOperationParameter(
            name: "p2",
            type: "fake_type",
            isRequired: false,
            explode: false,
            location: RestApiOperationParameterLocation.Query);

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
        };

        // Act
        var url = sut.BuildOperationUrl(arguments);

        // Assert
        Assert.Equal("https://fake-random-test-host-override/fake-path-value/", url.OriginalString);
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
            new(name: "fake_header_one", type: "string", isRequired: true, explode: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "fake_header_two", type : "string", isRequired : false, explode : false, location : RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple)
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
            new RestApiOperationParameter(name: "fake_header_one", type : "string", isRequired : true, explode : false, location : RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new RestApiOperationParameter(name : "fake_header_two", type : "string", isRequired : false, explode : false, location : RestApiOperationParameterLocation.Header, style : RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_header_one", "fake_header_one_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata, rawHeaders);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.Single(headers);

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
            new(name : "fake_header_one", type : "string", isRequired : true, explode : false, location : RestApiOperationParameterLocation.Header, style : RestApiOperationParameterStyle.Simple),
            new(name: "fake_header_two", type : "string", isRequired : false, explode : false, location : RestApiOperationParameterLocation.Header, style : RestApiOperationParameterStyle.Simple, defaultValue: "fake_header_two_default_value")
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
}
