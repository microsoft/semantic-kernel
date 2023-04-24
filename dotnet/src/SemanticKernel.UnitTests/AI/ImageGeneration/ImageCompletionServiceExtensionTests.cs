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
    public void ItCanAddImageGenerationServiceInstance()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IImageGenerationService>();

        // Act
        services.AddImageGenerationService(serviceId, instance);

        // Assert
        Assert.Contains(serviceId, services.GetImageGenerationServiceIds());
        Assert.Same(instance, services.GetImageGenerationServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddImageGenerationServiceFactory()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IImageGenerationService>();
        var factory = new Func<IImageGenerationService>(() => instance);

        // Act
        services.AddImageGenerationService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetImageGenerationServiceIds());
        Assert.Same(instance, services.GetImageGenerationServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddImageGenerationServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IImageGenerationService>();
        var factory = new Func<INamedServiceProvider, IImageGenerationService>(sp => instance);

        // Act
        services.AddImageGenerationService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetImageGenerationServiceIds());
        Assert.Same(instance, services.GetImageGenerationServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanSetDefaultImageGenerationService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IImageGenerationService>();
        var instance2 = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId1, instance1);
        services.AddImageGenerationService(serviceId2, instance2);

        // Act
        services.SetDefaultImageGenerationService(serviceId2);

        // Assert
        Assert.Equal(serviceId2, services.GetDefaultImageGenerationServiceId());
        Assert.Same(instance2, services.GetImageGenerationServiceOrDefault());
    }

    [Fact]
    public void ItThrowsIfSettingDefaultImageGenerationServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId1, instance1);

        // Act - Assert
        Assert.Throws<KernelException>(() => services.SetDefaultImageGenerationService(serviceId2));
    }

    [Fact]
    public void ItCanRemoveImageGenerationService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IImageGenerationService>();
        var instance2 = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId1, instance1);
        services.AddImageGenerationService(serviceId2, instance2);

        // Act
        var result = services.TryRemoveImageGenerationService(serviceId1);

        // Assert
        Assert.True(result);
        Assert.DoesNotContain(serviceId1, services.GetImageGenerationServiceIds());
        Assert.Contains(serviceId2, services.GetImageGenerationServiceIds());
    }

    [Fact]
    public void ItReturnsFalseIfRemovingImageGenerationServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId1, instance1);

        // Act
        var result = services.TryRemoveImageGenerationService(serviceId2);

        // Assert
        Assert.False(result);
        Assert.Contains(serviceId1, services.GetImageGenerationServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllImageGenerationServices()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IImageGenerationService>();
        var instance2 = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId1, instance1);
        services.AddImageGenerationService(serviceId2, instance2);

        // Act
        services.RemoveAllImageGenerationServices();

        // Assert
        Assert.Empty(services.GetImageGenerationServiceIds());
    }

    [Fact]
    public void ItReturnsNullIfNoDefaultImageGenerationServiceIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.GetDefaultImageGenerationServiceId();

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasImageGenerationServiceWithValidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId, instance);

        // Act
        var result = services.HasImageGenerationService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasImageGenerationServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId1, instance);

        // Act
        var result = services.HasImageGenerationService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasImageGenerationServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IImageGenerationService>();
        services.AddImageGenerationService(serviceId, instance, setAsDefault: true);

        // Act
        var result = services.HasImageGenerationService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasImageGenerationServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.HasImageGenerationService();

        // Assert
        Assert.False(result);
    }
}
