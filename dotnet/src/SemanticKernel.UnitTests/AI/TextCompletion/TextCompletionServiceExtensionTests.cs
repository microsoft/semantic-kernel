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
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();

        // Act
        services.SetService<ITextCompletion>(serviceId, instance);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<ITextCompletion>(serviceId, out var instanceRetrieved));
        Assert.Same(instance, instanceRetrieved);
    }

    [Fact]
    public void ItCanAddTextCompletionServiceFactory()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        var factory = new Func<ITextCompletion>(() => instance);

        // Act
        services.SetService<ITextCompletion>(serviceId, factory);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<ITextCompletion>(serviceId, out var _));
    }

    [Fact]
    public void ItCanSetDefaultTextCompletionService()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance1 = Mock.Of<ITextCompletion>();
        var instance2 = Mock.Of<ITextCompletion>();
        services.SetService<ITextCompletion>(serviceId1, instance1);

        // Act
        services.SetService<ITextCompletion>(serviceId2, instance2, setAsDefault: true);
        var provider = services.Build();

        // Assert
        Assert.True(provider.TryGetService<ITextCompletion>(out var instanceRetrieved));
        Assert.Same(instance2, instanceRetrieved);
    }

    [Fact]
    public void ItReturnsFalseIfNoDefaultTextCompletionServiceIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Assert
        Assert.False(provider.TryGetService<ITextCompletion>(out var _));
    }

    [Fact]
    public void ItReturnsTrueIfHasTextCompletionServiceWithValidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        services.SetService<ITextCompletion>(serviceId, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasTextCompletionService(serviceId);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextCompletionServiceWithInvalidId()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId1 = "test1";
        var serviceId2 = "test2";
        var instance = Mock.Of<ITextCompletion>();
        services.SetService<ITextCompletion>(serviceId1, instance);
        var provider = services.Build();

        // Act
        var result = provider.HasTextCompletionService(serviceId2);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void ItReturnsTrueIfHasTextCompletionServiceWithNullIdAndDefaultIsSet()
    {
        // Arrange
        var services = new AIServiceCollection();
        var serviceId = "test";
        var instance = Mock.Of<ITextCompletion>();
        services.SetService<ITextCompletion>(serviceId, instance, setAsDefault: true);
        var provider = services.Build();

        // Act
        var result = provider.HasTextCompletionService();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void ItReturnsFalseIfHasTextCompletionServiceWithNullIdAndNoDefaultExists()
    {
        // Arrange
        var services = new AIServiceCollection();
        var provider = services.Build();

        // Act
        var result = provider.HasTextCompletionService();

        // Assert
        Assert.False(result);
    }
}
