// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Serialization;

public class FormStyleParametersSerializerTests
{
    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItem()
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: true, //Specify generating a separate parameter for each array item.
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.Form,
                arrayItemType: "integer");

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, new JsonArray(1, 2, 3));

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithCommaSeparatedValuePerArrayItem()
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: false, //Specify generating a parameter with comma-separated values for each array item.
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.Form,
                arrayItemType: "integer");

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, new JsonArray(1, 2, 3));

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1,2,3", result);
    }

    [Fact]
    public void ItShouldCreateParameterForPrimitiveValue()
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "integer",
                isRequired: true,
                expand: false,
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, "28");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=28", result);
    }

    [Fact]
    public void ItShouldCreateParameterForDateTimeValue()
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, JsonValue.Create(new DateTime(2023, 12, 06, 11, 53, 36, DateTimeKind.Utc)));

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=2023-12-06T11%3a53%3a36Z", result);
    }

    [Theory]
    [InlineData("2024-01-01T00:00:00+00:00", "2024-01-01T00%3a00%3a00%2b00%3a00")]
    public void ItShouldCreateParameterForStringValue(string value, string encodedValue)
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "string",
                isRequired: true,
                expand: false,
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, JsonValue.Create(value));

        // Assert
        Assert.NotNull(result);

        Assert.Equal($"id={encodedValue}", result);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInPrimitiveParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiParameter("id", "string", false, false, RestApiParameterLocation.Query, RestApiParameterStyle.Form);

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
        var parameter = new RestApiParameter("id", "array", false, true, RestApiParameterLocation.Query, RestApiParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, new JsonArray($"{specialSymbol}"));

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
        var parameter = new RestApiParameter("id", "array", false, false, RestApiParameterLocation.Query, RestApiParameterStyle.Form);

        // Act
        var result = FormStyleParameterSerializer.Serialize(parameter, new JsonArray($"{specialSymbol}"));

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }
}
