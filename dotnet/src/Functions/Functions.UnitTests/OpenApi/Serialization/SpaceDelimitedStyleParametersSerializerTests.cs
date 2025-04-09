// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Serialization;

public class SpaceDelimitedStyleParametersSerializerTests
{
    [Fact]
    public void ItShouldThrowExceptionForUnsupportedParameterStyle()
    {
        // Arrange
        var parameter = new RestApiParameter(name: "p1", type: "string", isRequired: false, expand: false, location: RestApiParameterLocation.Query, style: RestApiParameterStyle.Label);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => SpaceDelimitedStyleParameterSerializer.Serialize(parameter, "fake-argument"));
    }

    [Theory]
    [InlineData("integer")]
    [InlineData("number")]
    [InlineData("string")]
    [InlineData("boolean")]
    [InlineData("object")]
    public void ItShouldThrowExceptionIfParameterTypeIsNotArray(string parameterType)
    {
        // Arrange
        var parameter = new RestApiParameter(name: "p1", type: parameterType, isRequired: false, expand: false, location: RestApiParameterLocation.Query, style: RestApiParameterStyle.SpaceDelimited);

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => SpaceDelimitedStyleParameterSerializer.Serialize(parameter, "fake-argument"));
    }

    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItem()
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: true, //Specifies to generate a separate parameter for each array item.
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.SpaceDelimited,
                arrayItemType: "integer");

        // Act
        var result = SpaceDelimitedStyleParameterSerializer.Serialize(parameter, new JsonArray("1", "2", "3"));

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithSpaceSeparatedValuePerArrayItem()
    {
        // Arrange
        var parameter = new RestApiParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: false, //Specify generating a parameter with space-separated values for each array item.
                location: RestApiParameterLocation.Query,
                style: RestApiParameterStyle.SpaceDelimited,
                arrayItemType: "integer");

        // Act
        var result = SpaceDelimitedStyleParameterSerializer.Serialize(parameter, new JsonArray(1, 2, 3));

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1%202%203", result);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInSpaceDelimitedParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiParameter(name: "id", type: "array", isRequired: false, expand: false, location: RestApiParameterLocation.Query, style: RestApiParameterStyle.SpaceDelimited);

        // Act
        var result = SpaceDelimitedStyleParameterSerializer.Serialize(parameter, new JsonArray(specialSymbol));

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInAmpersandDelimitedParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiParameter(name: "id", type: "array", isRequired: false, expand: true, location: RestApiParameterLocation.Query, style: RestApiParameterStyle.SpaceDelimited);

        // Act
        var result = SpaceDelimitedStyleParameterSerializer.Serialize(parameter, new JsonArray(specialSymbol));

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }
}
