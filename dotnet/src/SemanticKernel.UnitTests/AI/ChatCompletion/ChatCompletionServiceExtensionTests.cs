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
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();

        // Act
        services.SetService<IChatCompletion>(serviceId, instance);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<IChatCompletion>(serviceId, out var instanceRetrieved));
        Assert.Same(instance, instanceRetrieved);
    }

    [Fact]
    public void ItCanAddChatCompletionServiceFactory()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        var factory = new Func<IChatCompletion>(() => instance);

        // Act
        services.SetService<IChatCompletion>(serviceId, factory);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<IChatCompletion>(serviceId, out _));
    }

    [Fact]
    public void ItCanSetDefaultChatCompletionService()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<IChatCompletion>();
        var instance2 = Mock.Of<IChatCompletion>();
        services.SetService<IChatCompletion>(serviceId1, instance1);

        // Act
        services.SetService<IChatCompletion>(serviceId2, instance2, true);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<IChatCompletion>(out var instanceRetrieved));
        Assert.Same(instance2, instanceRetrieved);
    }

    [Fact]
    public void ItReturnsFalseIfNoDefaultChatCompletionServiceIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Assert
        Assert.False(provider.TryGetService<IChatCompletion>(out var instanceRetrieved));
    }

    [Fact]
    public void ItReturnsTrueIfHasChatCompletionServiceWithValidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        services.SetService<IChatCompletion>(serviceId, instance);

        // Act
        var provider = services.Build();
        var result = provider.HasChatCompletionService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasChatCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<IChatCompletion>();
        services.SetService<IChatCompletion>(serviceId1, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasChatCompletionService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasChatCompletionServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<IChatCompletion>();
        services.SetService<IChatCompletion>(serviceId, instance, setAsDefault: true);
        var provider = services.Build();

        // Act
        var result = provider.HasChatCompletionService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasChatCompletionServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Act
        var result = provider.HasChatCompletionService();

        // Assert
        Assert.False(result);
    }
}
