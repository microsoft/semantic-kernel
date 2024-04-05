// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="ClaudeServiceCollectionExtensions"/> and <see cref="ClaudeKernelBuilderExtensions"/> classes.
/// </summary>
public sealed class ClaudeServiceCollectionExtensionsTests
{
    [Fact]
    public void ClaudeChatCompletionServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddClaudeChatCompletion("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<ClaudeChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void ClaudeChatCompletionServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddClaudeChatCompletion("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<ClaudeChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void ClaudeChatCompletionServiceCustomEndpointShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddClaudeChatCompletion("modelId", new Uri("https://example.com"), null);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<ClaudeChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void ClaudeChatCompletionServiceCustomEndpointShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddClaudeChatCompletion("modelId", new Uri("https://example.com"), null);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<ClaudeChatCompletionService>(chatCompletionService);
    }
}
