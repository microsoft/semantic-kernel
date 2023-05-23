// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ImageGeneration;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ImageGeneration;

/// <summary>
/// Unit tests of <see cref="ImageGenerationServiceExtensions"/>.
/// </summary>
public class ImageGenerationServiceExtensionsTests
{
    [Fact]
    public void ItCanSetServiceImageGenerationInstance()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IImageGeneration>();

        // Act
        services.SetService<IImageGeneration>(serviceId, instance);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<IImageGeneration>(serviceId, out var instanceRetrieved));
        Assert.Same(instance, instanceRetrieved);
    }

    [Fact]
    public void ItCanSetServiceImageGenerationFactory()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IImageGeneration>();
        var factory = new Func<IImageGeneration>(() => instance);

        // Act
        services.SetService<IImageGeneration>(serviceId, factory);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<IImageGeneration>(out var instanceRetrieved));
    }

    [Fact]
    public void ItCanSetDefaultImageGenerationService()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IImageGeneration>();
        var instance2 = Mock.Of<IImageGeneration>();
        services.SetService<IImageGeneration>(serviceId1, instance1);

        // Act
        services.SetService<IImageGeneration>(serviceId2, instance2, setAsDefault: true);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<IImageGeneration>(out var instanceRetrieved));
        Assert.Same(instance2, instanceRetrieved);
    }

    [Fact]
    public void ItReturnsFalseIfNoDefaultImageGenerationServiceIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        Assert.False(provider.TryGetService<IImageGeneration>(out var instanceRetrieved));
    }

    [Fact]
    public void ItReturnsTrueIfHasImageGenerationServiceWithValidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IImageGeneration>();
        services.SetService<IImageGeneration>(serviceId, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasImageGenerationService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasImageGenerationServiceWithInvalidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<IImageGeneration>();
        services.SetService<IImageGeneration>(serviceId1, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasImageGenerationService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasImageGenerationServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IImageGeneration>();
        services.SetService<IImageGeneration>(serviceId, instance, setAsDefault: true);
        var provider = services.Build();

        // Act
        var result = provider.HasImageGenerationService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasImageGenerationServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Act
        var result = provider.HasImageGenerationService();

        // Assert
        Assert.False(result);
    }
}
