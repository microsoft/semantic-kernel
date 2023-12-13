// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

namespace SemanticKernel.Functions.UnitTests.OpenApi.Builders.Serialization;

public class PipeDelimitedStyleParametersSerializerTests
{
    [Fact]
    public void ItShouldThrowExceptionForUnsupportedParameterStyle()
    {
        //Arrange
        var parameter = new RestApiOperationParameter(name: "p1", type: "string", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Query, style: RestApiOperationParameterStyle.Form);

        //Act & Assert
        Assert.Throws<ArgumentException>(() => PipeDelimitedStyleParameterSerializer.Serialize(parameter, "fake-argument"));
    }

    [Theory]
    [InlineData("integer")]
    [InlineData("number")]
    [InlineData("string")]
    [InlineData("boolean")]
    [InlineData("object")]
    public void ItShouldThrowExceptionIfParameterTypeIsNotArray(string parameterType)
    {
        //Arrange
        var parameter = new RestApiOperationParameter(name: "p1", type: parameterType, isRequired: false, expand: false, location: RestApiOperationParameterLocation.Query, style: RestApiOperationParameterStyle.PipeDelimited);

        //Act & Assert
        Assert.Throws<ArgumentException>(() => PipeDelimitedStyleParameterSerializer.Serialize(parameter, "fake-argument"));
    }

    [Fact]
    public void ItShouldCreateAmpersandSeparatedParameterPerArrayItem()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: true, //Specifies to generate a separate parameter for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.PipeDelimited,
                arrayItemType: "integer");

        // Act
        var result = PipeDelimitedStyleParameterSerializer.Serialize(parameter, "[1,2,3]");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1&id=2&id=3", result);
    }

    [Fact]
    public void ItShouldCreateParameterWithPipeSeparatedValuePerArrayItem()
    {
        // Arrange
        var parameter = new RestApiOperationParameter(
                name: "id",
                type: "array",
                isRequired: true,
                expand: false, //Specify generating a parameter with pipe-separated values for each array item.
                location: RestApiOperationParameterLocation.Query,
                style: RestApiOperationParameterStyle.PipeDelimited,
                arrayItemType: "integer");

        // Act
        var result = PipeDelimitedStyleParameterSerializer.Serialize(parameter, "[1,2,3]");

        // Assert
        Assert.NotNull(result);

        Assert.Equal("id=1|2|3", result);
    }

    [Theory]
    [InlineData(":", "%3a")]
    [InlineData("/", "%2f")]
    [InlineData("?", "%3f")]
    [InlineData("#", "%23")]
    public void ItShouldEncodeSpecialSymbolsInPipeDelimitedParameterValues(string specialSymbol, string encodedEquivalent)
    {
        // Arrange
        var parameter = new RestApiOperationParameter(name: "id", type: "array", isRequired: false, expand: false, location: RestApiOperationParameterLocation.Query, style: RestApiOperationParameterStyle.PipeDelimited);

        // Act
        var result = PipeDelimitedStyleParameterSerializer.Serialize(parameter, $"[\"{specialSymbol}\"]");

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
        var parameter = new RestApiOperationParameter(name: "id", type: "array", isRequired: false, expand: true, location: RestApiOperationParameterLocation.Query, style: RestApiOperationParameterStyle.PipeDelimited);

        // Act
        var result = PipeDelimitedStyleParameterSerializer.Serialize(parameter, $"[\"{specialSymbol}\"]");

        // Assert
        Assert.NotNull(result);

        Assert.EndsWith(encodedEquivalent, result, StringComparison.Ordinal);
    }
}
