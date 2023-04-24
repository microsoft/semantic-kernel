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
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingService>();

        // Act
        services.AddTextEmbeddingService(serviceId, instance);

        // Assert
        Assert.Contains(serviceId, services.GetTextEmbeddingServiceIds());
        Assert.Same(instance, services.GetTextEmbeddingServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddTextEmbeddingServiceFactory()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingService>();
        var factory = new Func<ITextEmbeddingService>(() => instance);

        // Act
        services.AddTextEmbeddingService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetTextEmbeddingServiceIds());
        Assert.Same(instance, services.GetTextEmbeddingServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddTextEmbeddingServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingService>();
        var factory = new Func<INamedServiceProvider, ITextEmbeddingService>(sp => instance);

        // Act
        services.AddTextEmbeddingService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetTextEmbeddingServiceIds());
        Assert.Same(instance, services.GetTextEmbeddingServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanSetDefaultTextEmbeddingService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextEmbeddingService>();
        var instance2 = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId1, instance1);
        services.AddTextEmbeddingService(serviceId2, instance2);

        // Act
        services.SetDefaultTextEmbeddingService(serviceId2);

        // Assert
        Assert.Equal(serviceId2, services.GetDefaultTextEmbeddingServiceId());
        Assert.Same(instance2, services.GetTextEmbeddingServiceOrDefault());
    }

    [Fact]
    public void ItThrowsIfSettingDefaultTextEmbeddingServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId1, instance1);

        // Act - Assert
        Assert.Throws<KernelException>(() => services.SetDefaultTextEmbeddingService(serviceId2));
    }

    [Fact]
    public void ItCanRemoveTextEmbeddingService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextEmbeddingService>();
        var instance2 = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId1, instance1);
        services.AddTextEmbeddingService(serviceId2, instance2);

        // Act
        var result = services.TryRemoveTextEmbeddingService(serviceId1);

        // Assert
        Assert.True(result);
        Assert.DoesNotContain(serviceId1, services.GetTextEmbeddingServiceIds());
        Assert.Contains(serviceId2, services.GetTextEmbeddingServiceIds());
    }

    [Fact]
    public void ItReturnsFalseIfRemovingTextEmbeddingServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId1, instance1);

        // Act
        var result = services.TryRemoveTextEmbeddingService(serviceId2);

        // Assert
        Assert.False(result);
        Assert.Contains(serviceId1, services.GetTextEmbeddingServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllTextEmbeddingServices()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextEmbeddingService>();
        var instance2 = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId1, instance1);
        services.AddTextEmbeddingService(serviceId2, instance2);

        // Act
        services.RemoveAllTextEmbeddingServices();

        // Assert
        Assert.Empty(services.GetTextEmbeddingServiceIds());
    }

    [Fact]
    public void ItReturnsNullIfNoDefaultTextEmbeddingServiceIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.GetDefaultTextEmbeddingServiceId();

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasTextEmbeddingServiceWithValidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId, instance);

        // Act
        var result = services.HasTextEmbeddingService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextEmbeddingServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId1, instance);

        // Act
        var result = services.HasTextEmbeddingService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasTextEmbeddingServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextEmbeddingService>();
        services.AddTextEmbeddingService(serviceId, instance, setAsDefault: true);

        // Act
        var result = services.HasTextEmbeddingService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextEmbeddingServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.HasTextEmbeddingService();

        // Assert
        Assert.False(result);
    }
}
