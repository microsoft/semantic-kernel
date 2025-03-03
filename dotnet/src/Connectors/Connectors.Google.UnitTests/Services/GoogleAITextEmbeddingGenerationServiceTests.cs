// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Services;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Services;

public sealed class GoogleAITextEmbeddingGenerationServiceTests
{
    private const string Model = "fake-model";
    private const string ApiKey = "fake-key";
    private const int Dimensions = 512;

    [Fact]
    public void AttributesShouldContainModelId()
    {
        // Arrange & Act
        var service = new GoogleAITextEmbeddingGenerationService(Model, ApiKey);

        // Assert
        Assert.Equal(Model, service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void AttributesShouldNotContainDimensionsWhenNotProvided()
    {
        // Arrange & Act
        var service = new GoogleAITextEmbeddingGenerationService(Model, ApiKey);

        // Assert
        Assert.False(service.Attributes.ContainsKey(AIServiceExtensions.DimensionsKey));
    }

    [Fact]
    public void AttributesShouldContainDimensionsWhenProvided()
    {
        // Arrange & Act
        var service = new GoogleAITextEmbeddingGenerationService(Model, ApiKey, dimensions: Dimensions);

        // Assert
        Assert.Equal(Dimensions, service.Attributes[AIServiceExtensions.DimensionsKey]);
    }

    [Fact]
    public void GetDimensionsReturnsCorrectValue()
    {
        // Arrange
        var service = new GoogleAITextEmbeddingGenerationService(Model, ApiKey, dimensions: Dimensions);

        // Act
        var result = service.GetDimensions();

        // Assert
        Assert.Equal(Dimensions, result);
    }

    [Fact]
    public void GetDimensionsReturnsNullWhenNotProvided()
    {
        // Arrange
        var service = new GoogleAITextEmbeddingGenerationService(Model, ApiKey);

        // Act
        var result = service.GetDimensions();

        // Assert
        Assert.Null(result);
    }
}
