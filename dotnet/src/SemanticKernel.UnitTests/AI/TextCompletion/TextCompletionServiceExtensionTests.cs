// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI.TextCompletion;

/// <summary>
/// Unit tests of <see cref="TextCompletionServiceExtensions"/>.
/// </summary>
public class TextCompletionServiceExtensionsTests
{
    [Fact]
    public void ItCanAddTextCompletionServiceInstance()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();

        // Act
        services.AddTextCompletionService(serviceId, instance);

        // Assert
        Assert.Contains(serviceId, services.GetTextCompletionServiceIds());
        Assert.Same(instance, services.GetTextCompletionServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddTextCompletionServiceFactory()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        var factory = new Func<ITextCompletion>(() => instance);

        // Act
        services.AddTextCompletionService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetTextCompletionServiceIds());
        Assert.Same(instance, services.GetTextCompletionServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddTextCompletionServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        var factory = new Func<INamedServiceProvider, ITextCompletion>(sp => instance);

        // Act
        services.AddTextCompletionService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetTextCompletionServiceIds());
        Assert.Same(instance, services.GetTextCompletionServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanSetDefaultTextCompletionService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextCompletion>();
        var instance2 = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId1, instance1);
        services.AddTextCompletionService(serviceId2, instance2);

        // Act
        services.SetDefaultTextCompletionService(serviceId2);

        // Assert
        Assert.Equal(serviceId2, services.GetDefaultTextCompletionServiceId());
        Assert.Same(instance2, services.GetTextCompletionServiceOrDefault());
    }

    [Fact]
    public void ItThrowsIfSettingDefaultTextCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId1, instance1);

        // Act - Assert
        Assert.Throws<KernelException>(() => services.SetDefaultTextCompletionService(serviceId2));
    }

    [Fact]
    public void ItCanRemoveTextCompletionService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextCompletion>();
        var instance2 = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId1, instance1);
        services.AddTextCompletionService(serviceId2, instance2);

        // Act
        var result = services.TryRemoveTextCompletionService(serviceId1);

        // Assert
        Assert.True(result);
        Assert.DoesNotContain(serviceId1, services.GetTextCompletionServiceIds());
        Assert.Contains(serviceId2, services.GetTextCompletionServiceIds());
    }

    [Fact]
    public void ItReturnsFalseIfRemovingTextCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId1, instance1);

        // Act
        var result = services.TryRemoveTextCompletionService(serviceId2);

        // Assert
        Assert.False(result);
        Assert.Contains(serviceId1, services.GetTextCompletionServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllTextCompletionServices()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextCompletion>();
        var instance2 = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId1, instance1);
        services.AddTextCompletionService(serviceId2, instance2);

        // Act
        services.RemoveAllTextCompletionServices();

        // Assert
        Assert.Empty(services.GetTextCompletionServiceIds());
    }

    [Fact]
    public void ItReturnsNullIfNoDefaultTextCompletionServiceIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.GetDefaultTextCompletionServiceId();

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasTextCompletionServiceWithValidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId, instance);

        // Act
        var result = services.HasTextCompletionService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId1, instance);

        // Act
        var result = services.HasTextCompletionService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasTextCompletionServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        services.AddTextCompletionService(serviceId, instance, setAsDefault: true);

        // Act
        var result = services.HasTextCompletionService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextCompletionServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.HasTextCompletionService();

        // Assert
        Assert.False(result);
    }
}
