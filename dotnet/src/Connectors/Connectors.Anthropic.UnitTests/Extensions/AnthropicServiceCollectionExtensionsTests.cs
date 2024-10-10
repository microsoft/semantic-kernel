// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="AnthropicServiceCollectionExtensions"/> and <see cref="AnthropicKernelBuilderExtensions"/> classes.
/// </summary>
public sealed class AnthropicServiceCollectionExtensionsTests
{
    [Fact]
    public void AnthropicChatCompletionServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicChatCompletion("modelId", "apiKey");

        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void AnthropicChatCompletionServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddAnthropicChatCompletion("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void AnthropicChatCompletionServiceCustomEndpointShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicVertextAIChatCompletion("modelId", bearerTokenProvider: () => ValueTask.FromResult("token"), endpoint: new Uri("https://example.com"));

        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void AnthropicChatCompletionServiceCustomEndpointShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddAnthropicVertexAIChatCompletion("modelId", () => ValueTask.FromResult("token"), endpoint: new Uri("https://example.com"));
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }
}
