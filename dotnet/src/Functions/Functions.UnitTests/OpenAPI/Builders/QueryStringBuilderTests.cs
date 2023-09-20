// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Query;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Builders;
public class QueryStringBuilderTests
{
    private readonly QueryStringBuilder _sut;

    public QueryStringBuilderTests()
    {
        this._sut = new QueryStringBuilder();
    }

    [Fact]
    public void ShouldAddQueryStringParametersAndUseValuesFromArguments()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            true,
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            true,
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

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
        var queryString = this._sut.Build(operation, arguments);

        // Assert
        Assert.Equal("p1=v1&p2=v2", queryString);
    }

    [Fact]
    public void ShouldSkipNotRequiredQueryStringParametersIfTheirValuesMissing()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            false,
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            false,
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

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
        var queryString = this._sut.Build(operation, arguments);

        // Assert
        Assert.Equal("p2=v2", queryString);
    }

    [Fact]
    public void ShouldThrowExceptionIfNoValueIsProvideForRequiredQueryStringParameter()
    {
        // Arrange
        var firstParameterMetadata = new RestApiOperationParameter(
            "p1",
            "fake_type",
            true,
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

        var secondParameterMetadata = new RestApiOperationParameter(
            "p2",
            "fake_type",
            false,
            false,
            RestApiOperationParameterLocation.Query,
            RestApiOperationParameterStyle.Form);

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
        Assert.Throws<SKException>(() => this._sut.Build(operation, arguments));
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
                "p1",
                "string",
                false,
                false,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form)
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", $"p1_value{specialSymbol}" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var queryString = this._sut.Build(operation, arguments);

        // Assert
        Assert.NotNull(queryString);

        Assert.EndsWith(encodedEquivalent, queryString, StringComparison.Ordinal);
    }

    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItem()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                "p1",
                "array",
                false,
                true,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                "p2",
                "array",
                false,
                true,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = this._sut.Build(operation, arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a&p1=b&p1=c&p2=1&p2=2&p2=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithCommaSeparatedValuePerArrayItem()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                "p1",
                "array",
                false,
                false,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                "p2",
                "array",
                false,
                false,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form,
                arrayItemType: "integer")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\",\"c\"]" },
            { "p2", "[1,2,3]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = this._sut.Build(operation, arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a,b,c&p2=1,2,3", result);
    }

    [Fact]
    public void ItShouldCreateParameterForPrimitiveValues()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            new RestApiOperationParameter(
                "p1",
                "string",
                false,
                false,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form,
                arrayItemType: "string"),
            new RestApiOperationParameter(
                "p2",
                "boolean",
                false,
                false,
                RestApiOperationParameterLocation.Query,
                RestApiOperationParameterStyle.Form)
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "v1" },
            { "p2", "true" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = this._sut.Build(operation, arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=v1&p2=true", result);
    }

    [Fact]
    public void ItShouldMixAndMatchParametersOfDifferentTypesAndStyles()
    {
        // Arrange
        var metadata = new List<RestApiOperationParameter>
        {
            //'Form' style array parameter with comma separated values
            new RestApiOperationParameter("p1", "array", true, false,RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form, arrayItemType: "string"),

            //Primitive boolean parameter
            new RestApiOperationParameter("p2", "boolean", true, false, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form),

            //'Form' style array parameter with parameter per array item
            new RestApiOperationParameter("p3", "array", true, true, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form, arrayItemType: "number")
        };

        var arguments = new Dictionary<string, string>
        {
            { "p1", "[\"a\",\"b\"]" },
            { "p2", "false" },
            { "p3", "[1,2]" }
        };

        var operation = new RestApiOperation("fake_id", new Uri("https://fake-random-test-host"), "fake_path", HttpMethod.Get, "fake_description", metadata, new Dictionary<string, string>());

        // Act
        var result = this._sut.Build(operation, arguments);

        // Assert
        Assert.NotNull(result);

        Assert.Equal("p1=a,b&p2=false&p3=1&p3=2", result);
    }
}
