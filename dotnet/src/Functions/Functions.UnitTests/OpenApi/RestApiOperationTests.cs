// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi;

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
            new List<RestApiOperationParameter>()
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
            new List<RestApiOperationParameter>()
        );

        var fakeHostUrlOverride = "https://fake-random-test-host-override";

        var arguments = new Dictionary<string, string>();

        // Act
        var url = sut.BuildOperationUrl(arguments, serverUrlOverride: new Uri(fakeHostUrlOverride));

        // Assert
        Assert.Equal(fakeHostUrlOverride, url.OriginalString.TrimEnd('/'));
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
            new List<RestApiOperationParameter>()
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
            expand: false,
            location: RestApiOperationParameterLocation.Path,
            defaultValue: "fake-default-path");

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "/{fake-path-parameter}/other_fake_path_section",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { parameterMetadata });

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
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            defaultValue: "dv1");

        var secondParameterMetadata = new RestApiOperationParameter(
            name: "p2",
            type: "fake_type",
            isRequired: false,
            expand: false,
            location: RestApiOperationParameterLocation.Query);

        var sut = new RestApiOperation(
            "fake_id",
            new Uri("https://fake-random-test-host"),
            "{fake-path}/",
            HttpMethod.Get,
            "fake_description",
            new List<RestApiOperationParameter> { firstParameterMetadata, secondParameterMetadata });

        var fakeHostUrlOverride = "https://fake-random-test-host-override";

        var arguments = new Dictionary<string, string>
        {
            { "fake-path", "fake-path-value" },
        };

        // Act
        var url = sut.BuildOperationUrl(arguments, serverUrlOverride: new Uri(fakeHostUrlOverride));

        // Assert
        Assert.Equal($"{fakeHostUrlOverride}/fake-path-value/", url.OriginalString);
    }

    [Fact]
    public void ItShouldRenderHeaderValuesFromArguments()
    {
        // Arrange
        var parameters = new List<RestApiOperationParameter>
        {
            new(
                name: "fake_header_one",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiOperationParameterLocation.Header,
                style: RestApiOperationParameterStyle.Simple),

            new(
                name: "fake_header_two",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiOperationParameterLocation.Header,
                style: RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            { "fake_header_one", "fake_header_one_value" },
            { "fake_header_two", "fake_header_two_value" }
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", parameters);

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
    public void ShouldThrowExceptionIfNoValueProvidedForRequiredHeader()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new(name: "fake_header_one", type: "string", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "fake_header_two", type : "string", isRequired : false, expand : false, location : RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple)
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        void Act() => sut.RenderHeaders(new Dictionary<string, string>());

        // Assert
        Assert.Throws<KernelException>(Act);
    }

    [Fact]
    public void ItShouldSkipOptionalHeaderHavingNoValue()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new(name: "fake_header_one", type : "string", isRequired : true, expand : false, location : RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "fake_header_two", type : "string", isRequired : false, expand : false, location : RestApiOperationParameterLocation.Header, style : RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            ["fake_header_one"] = "fake_header_one_value"
        };

        var sut = new RestApiOperation("fake_id", new Uri("http://fake_url"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.Single(headers);

        var headerOne = headers["fake_header_one"];
        Assert.Equal("fake_header_one_value", headerOne);
    }

    [Fact]
    public void ItShouldCreateHeaderWithCommaSeparatedValues()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new( name: "h1", type: "array", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple, arrayItemType: "string"),
            new( name: "h2", type: "array", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple, arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            ["h1"] = "[\"a\",\"b\",\"c\"]",
            ["h2"] = "[1,2,3]"
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.NotNull(headers);
        Assert.Equal(2, headers.Count);

        Assert.Equal("a,b,c", headers["h1"]);
        Assert.Equal("1,2,3", headers["h2"]);
    }

    [Fact]
    public void ItShouldCreateHeaderWithPrimitiveValue()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new( name: "h1", type: "string", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new( name: "h2", type: "boolean", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple)
        };

        var arguments = new Dictionary<string, string>
        {
            ["h1"] = "v1",
            ["h2"] = "true"
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.NotNull(headers);
        Assert.Equal(2, headers.Count);

        Assert.Equal("v1", headers["h1"]);
        Assert.Equal("true", headers["h2"]);
    }

    [Fact]
    public void ItShouldMixAndMatchHeadersOfDifferentValueTypes()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new(name: "h1", type: "array", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
            new(name: "h2", type: "boolean", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Header, style: RestApiOperationParameterStyle.Simple),
        };

        var arguments = new Dictionary<string, string>
        {
            ["h1"] = "[\"a\",\"b\"]",
            ["h2"] = "false"
        };

        var sut = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata);

        // Act
        var headers = sut.RenderHeaders(arguments);

        // Assert
        Assert.NotNull(headers);
        Assert.Equal(2, headers.Count);

        Assert.Equal("a,b", headers["h1"]);
        Assert.Equal("false", headers["h2"]);
    }
}
