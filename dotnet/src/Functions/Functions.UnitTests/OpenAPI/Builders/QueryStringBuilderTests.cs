// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Builders;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Builders;
public class QueryStringBuilderTests
{
    [Fact]
    public void ShouldAddQueryStringParametersAndUseValuesFromArguments()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            name: "p1",
            type: "fake_type",
            isRequired: true,
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            style: RestApiOperationParameterStyle.Form);

        var secondParameterMetadata = new RestApiOperationParameter(
            name: "p2",
            type: "fake_type",
            isRequired: true,
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            style: RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
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
        var queryString = operation.BuildQueryString(arguments);

        // Assert
        Assert.Equal("p1=v1&p2=v2", queryString);
    }

    [Fact]
    public void ShouldSkipNotRequiredQueryStringParametersIfTheirArgumentsMissing()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            name: "p1",
            type: "fake_type",
            isRequired: false,
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            style: RestApiOperationParameterStyle.Form);

        var secondParameterMetadata = new RestApiOperationParameter(
            name: "p2",
            type: "fake_type",
            isRequired: false,
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            style: RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
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
        var queryString = operation.BuildQueryString(arguments);

        // Assert
        Assert.Equal("p2=v2", queryString);
    }

    [Fact]
    public void ShouldThrowExceptionIfNoValueIsProvideForRequiredQueryStringParameter()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            name: "p1",
            type: "fake_type",
            isRequired: true,
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            style: RestApiOperationParameterStyle.Form);

        var secondParameterMetadata = new RestApiOperationParameter(
            name: "p2",
            type: "fake_type",
            isRequired: false,
            expand: false,
            location: RestApiOperationParameterLocation.Query,
            style: RestApiOperationParameterStyle.Form);

        var operation = new RestApiOperation(
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
        Assert.Throws<SKException>(() => operation.BuildQueryString(arguments));
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
            new RestApiOperationParameter(
                name: "p1",
                type: "string",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form)
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", $"p1_value{specialSymbol}" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var queryString = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(queryString);

        Assert.EndsWith(encodedEquivalent, queryString, StringComparison.Ordinal);
    }

    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItemForFormStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "array",
                isRequired: false,
                expand: true,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "array",
                isRequired: false,
                expand: true,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a&p1=b&p1=c&p2=1&p2=2&p2=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithCommaSeparatedValuePerArrayItemForFormStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "array",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "array",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a,b,c&p2=1,2,3", result);
    }

    [Fact]
    public void ItShouldCreateParameterForPrimitiveValuesForFormStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "string",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "boolean",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form)
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "v1" },
            { "p2", "true" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=v1&p2=true", result);
    }

    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItemForSpaceDelimitedStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "array",
                isRequired: false,
                expand: true,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.SpaceDelimited,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "array",
                isRequired: false,
                expand: true,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.SpaceDelimited,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a&p1=b&p1=c&p2=1&p2=2&p2=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithSpaceSeparatedValuePerArrayItemForSpaceDelimitedStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "array",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.SpaceDelimited,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "array",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.SpaceDelimited,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a%20b%20c&p2=1%202%203", result);
    }

    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItemForPipeDelimitedStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "array",
                isRequired: false,
                expand: true,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.PipeDelimited,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "array",
                isRequired: false,
                expand: true,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.PipeDelimited,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a&p1=b&p1=c&p2=1&p2=2&p2=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithPipeSeparatedValuePerArrayItemForPipeDelimitedStyleParameters()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                name: "p1",
                type: "array",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.PipeDelimited,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                name: "p2",
                type: "array",
                isRequired: false,
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.PipeDelimited,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a|b|c&p2=1|2|3", result);
    }

    [Fact]
    public void ItShouldMixAndMatchParametersOfDifferentTypesAndStyles()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            //'Form' style array parameter with comma separated values
            new RestApiOperationParameter(name: "p1", type: "array", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Query, style: RestApiOperationParameterStyle.Form, arrayItemType: "string"),

            //'Form' style primitive boolean parameter
            new RestApiOperationParameter(name: "p2", type: "boolean", isRequired: true, expand: false, location: RestApiOperationParameterLocation.Query, style: RestApiOperationParameterStyle.Form),

            //'Form' style array parameter with parameter per array item
            new RestApiOperationParameter(name : "p3", type : "array", isRequired : true, expand : true, location : RestApiOperationParameterLocation.Query, style : RestApiOperationParameterStyle.Form),

            //'SpaceDelimited' style array parameter with space separated values
            new RestApiOperationParameter(name : "p4", type : "array", isRequired : true, expand : false, location : RestApiOperationParameterLocation.Query, style : RestApiOperationParameterStyle.SpaceDelimited),

            //'SpaceDelimited' style array parameter with parameter per array item
            new RestApiOperationParameter(name : "p5", type : "array", isRequired : true, expand : true, location : RestApiOperationParameterLocation.Query, style : RestApiOperationParameterStyle.SpaceDelimited),

            //'PipeDelimited' style array parameter with pipe separated values
            new RestApiOperationParameter(name : "p6", type : "array", isRequired : true, expand : false, location : RestApiOperationParameterLocation.Query, style : RestApiOperationParameterStyle.PipeDelimited),

            //'PipeDelimited' style array parameter with parameter per array item
            new RestApiOperationParameter(name : "p7", type : "array", isRequired : true, expand : true, location : RestApiOperationParameterLocation.Query, style : RestApiOperationParameterStyle.PipeDelimited),
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\"]" },
            { "p2", "false" },
            { "p3", "[1,2]" },
            { "p4", "[3,4]" },
            { "p5", "[\"c\",\"d\"]" },
            { "p6", "[5,6]" },
            { "p7", "[\"e\",\"f\"]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = operation.BuildQueryString(arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a,b&p2=false&p3=1&p3=2&p4=3%204&p5=c&p5=d&p6=5|6&p7=e&p7=f", result);
    }
}
