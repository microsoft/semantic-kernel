// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Serialization;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenAPI.Builders.Serialization;

public class FormStyleParametersSerializerTests
{
    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItem()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: true, //Specify generating a separate parameter for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer");

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, "[1,2,3]");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithCommaSeparatedValuePerArrayItem()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: false, //Specify generating a parameter with comma-separated values for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form,
                arrayItemType: "integer");

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, "[1,2,3]");

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
                expand: false,
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, "28");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=28", result);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInPrimitiveParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiOperationParameter("id", "string", false, false, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, $"fake_query_param_value{specialSymbol}");

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInAmpersandSeparatedParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiOperationParameter("id", "array", false, true, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, $"[\"{specialSymbol}\"]");

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInCommaSeparatedParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiOperationParameter("id", "array", false, false, RestApiOperationParameterLocation.Query, RestApiOperationParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, $"[\"{specialSymbol}\"]");

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }
}
