// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Skills.OpenAPI.Builders.Query;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Skills.UnitTests.OpenAPI.Builders.Query;

public class FormStyleQueryParametersSerializerTests
{
    [Fact]
    public void ItShouldCreateAmpersandSeparatedQueryStringParameterPerArrayItem()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                explode: true, //Specify generating a separate parameter for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer");

        var sut = new FormStyleQueryParametersSerializer();

        // Act
        var result = sut.Serialize(parameter, "[1,2,3]");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldCreateCommaSeparatedValuePerArrayItem()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                explode: false, //Specify generating a parameter with comma-separated values for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer");

        var sut = new FormStyleQueryParametersSerializer();

        // Act
        var result = sut.Serialize(parameter, "[1,2,3]");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1,2,3", result);
    }

    [Fact]
    public void ItShouldNotWrapQueryStringValuesOfStringTypeIntoSingleQuotesForArrayItems()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                explode: false, //Specify generating a parameter with comma-separated values for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer");

        var sut = new FormStyleQueryParametersSerializer();

        // Act
        var result = sut.Serialize(parameter, "[\"1\",\"2\",\"3\"]");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1,2,3", result);
    }

    [Fact]
    public void ItShouldCreateParameterForPrimitiveValue()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "integer",
                isRequired: true,
                explode: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form);

        var sut = new FormStyleQueryParametersSerializer();

        // Act
        var result = sut.Serialize(parameter, "28");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=28", result);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiOperationParameter("fake_query_param", "string", false, false, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form);

        var sut = new FormStyleQueryParametersSerializer();

        // Act
        var queryString = sut.Serialize(parameter, $"fake_query_param_value{specialSymbol}");

        // Assert
        Assert.NotNull(queryString);

        Assert.EndsWith(encodedEquivalent, queryString, StringComparison.Ordinal);
    }
}
