// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Services;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI.ChatCompletion;

/// <summary>
/// Unit tests of <see cref="ChatCompletionServiceExtensions"/>.
/// </summary>
public class ChatCompletionServiceExtensionsTests
{
    [Fact]
    public void ItCanAddChatCompletionServiceInstance()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();

        // Act
        services.AddChatCompletionService(serviceId, instance);

        // Assert
        Assert.Contains(serviceId, services.GetChatCompletionServiceIds());
        Assert.Same(instance, services.GetChatCompletionServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddChatCompletionServiceFactory()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        var factory = new Func<IChatCompletion>(() => instance);

        // Act
        services.AddChatCompletionService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetChatCompletionServiceIds());
        Assert.Same(instance, services.GetChatCompletionServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanAddChatCompletionServiceFactoryWithServiceProvider()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        var factory = new Func<INamedServiceProvider, IChatCompletion>(sp => instance);

        // Act
        services.AddChatCompletionService(serviceId, factory);

        // Assert
        Assert.Contains(serviceId, services.GetChatCompletionServiceIds());
        Assert.Same(instance, services.GetChatCompletionServiceOrDefault(serviceId));
    }

    [Fact]
    public void ItCanSetDefaultChatCompletionService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IChatCompletion>();
        var instance2 = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId1, instance1);
        services.AddChatCompletionService(serviceId2, instance2);

        // Act
        services.SetDefaultChatCompletionService(serviceId2);

        // Assert
        Assert.Equal(serviceId2, services.GetDefaultChatCompletionServiceId());
        Assert.Same(instance2, services.GetChatCompletionServiceOrDefault());
    }

    [Fact]
    public void ItThrowsIfSettingDefaultChatCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId1, instance1);

        // Act - Assert
        Assert.Throws<KernelException>(() => services.SetDefaultChatCompletionService(serviceId2));
    }

    [Fact]
    public void ItCanRemoveChatCompletionService()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IChatCompletion>();
        var instance2 = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId1, instance1);
        services.AddChatCompletionService(serviceId2, instance2);

        // Act
        var result = services.TryRemoveChatCompletionService(serviceId1);

        // Assert
        Assert.True(result);
        Assert.DoesNotContain(serviceId1, services.GetChatCompletionServiceIds());
        Assert.Contains(serviceId2, services.GetChatCompletionServiceIds());
    }

    [Fact]
    public void ItReturnsFalseIfRemovingChatCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId1, instance1);

        // Act
        var result = services.TryRemoveChatCompletionService(serviceId2);

        // Assert
        Assert.False(result);
        Assert.Contains(serviceId1, services.GetChatCompletionServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllChatCompletionServices()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IChatCompletion>();
        var instance2 = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId1, instance1);
        services.AddChatCompletionService(serviceId2, instance2);

        // Act
        services.RemoveAllChatCompletionServices();

        // Assert
        Assert.Empty(services.GetChatCompletionServiceIds());
    }

    [Fact]
    public void ItReturnsNullIfNoDefaultChatCompletionServiceIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.GetDefaultChatCompletionServiceId();

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasChatCompletionServiceWithValidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId, instance);

        // Act
        var result = services.HasChatCompletionService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasChatCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId1, instance);

        // Act
        var result = services.HasChatCompletionService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasChatCompletionServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new ServiceRegistry();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        services.AddChatCompletionService(serviceId, instance, setAsDefault: true);

        // Act
        var result = services.HasChatCompletionService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasChatCompletionServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new ServiceRegistry();

        // Act
        var result = services.HasChatCompletionService();

        // Assert
        Assert.False(result);
    }
}
