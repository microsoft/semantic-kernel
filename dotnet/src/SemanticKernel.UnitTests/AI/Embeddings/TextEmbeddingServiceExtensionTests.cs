// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI.Embeddings;

/// <summary>
/// Unit tests of <see cref="TextEmbeddingServiceExtensions"/>.
/// </summary>
public class TextEmbeddingServiceExtensionsTests
{
    [Fact]
    public void ItCanAddTextEmbeddingServiceInstance()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingGeneration>();

        // Act
        services.SetService<ITextEmbeddingGeneration>(serviceId, instance);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<ITextEmbeddingGeneration>(serviceId, out var instanceRetrieved));
        Assert.Same(instance, instanceRetrieved);
    }

    [Fact]
    public void ItCanAddTextEmbeddingServiceFactory()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingGeneration>();
        var factory = new Func<ITextEmbeddingGeneration>(() => instance);

        // Act
        services.SetService<ITextEmbeddingGeneration>(serviceId, factory);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<ITextEmbeddingGeneration>(serviceId, out _));
    }

    [Fact]
    public void ItCanSetDefaultTextEmbeddingService()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextEmbeddingGeneration>();
        var instance2 = Mock.Of<ITextEmbeddingGeneration>();
        services.SetService<ITextEmbeddingGeneration>(serviceId1, instance1);

        // Act
        services.SetService<ITextEmbeddingGeneration>(serviceId2, instance2, setAsDefault: true);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<ITextEmbeddingGeneration>(out var instanceRetrieved));
        Assert.Same(instance2, instanceRetrieved);
    }

    [Fact]
    public void ItReturnsFalseIfNoDefaultTextEmbeddingServiceIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Assert
        Assert.False(provider.TryGetService<ITextEmbeddingGeneration>(out var instanceRetrieved));
    }

    [Fact]
    public void ItReturnsTrueIfHasTextEmbeddingServiceWithValidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingGeneration>();
        services.SetService<ITextEmbeddingGeneration>(serviceId, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasTextEmbeddingService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextEmbeddingServiceWithInvalidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<ITextEmbeddingGeneration>();
        services.SetService<ITextEmbeddingGeneration>(serviceId1, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasTextEmbeddingService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasTextEmbeddingServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingGeneration>();
        services.SetService<ITextEmbeddingGeneration>(serviceId, instance, setAsDefault: true);
        var provider = services.Build();

        // Act
        var result = provider.HasTextEmbeddingService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextEmbeddingServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Act
        var result = provider.HasTextEmbeddingService();

        // Assert
        Assert.False(result);
    }
}
