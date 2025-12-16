// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="AnthropicServiceCollectionExtensions"/>.
/// </summary>
public sealed class AnthropicServiceCollectionExtensionsTests
{
    [Fact]
    public void AnthropicChatCompletionServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key");
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
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void AnthropicTextGenerationServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<AnthropicChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void AnthropicTextGenerationServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<AnthropicChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void AnthropicServicesShouldShareSameInstance()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        var concreteService = serviceProvider.GetRequiredService<AnthropicChatCompletionService>();

        Assert.Same(chatCompletionService, textGenerationService);
        Assert.Same(chatCompletionService, concreteService);
    }

    [Fact]
    public void AnthropicServicesWithServiceIdShouldBeRegisteredAsKeyed()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId = "anthropic-service";

        // Act
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key", serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId);
        var textGenerationService = serviceProvider.GetRequiredKeyedService<ITextGenerationService>(serviceId);

        Assert.NotNull(chatCompletionService);
        Assert.NotNull(textGenerationService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
        Assert.Same(chatCompletionService, textGenerationService);
    }

    [Fact]
    public void AnthropicServicesWithCustomBaseUrlShouldBeRegistered()
    {
        // Arrange
        var services = new ServiceCollection();
        var customBaseUrl = new System.Uri("https://custom.anthropic.endpoint/");

        // Act
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key", baseUrl: customBaseUrl);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void MultipleAnthropicServicesCanBeRegisteredWithDifferentServiceIds()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId1 = "anthropic-claude-sonnet";
        const string serviceId2 = "anthropic-claude-opus";

        // Act
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key-1", serviceId: serviceId1);
        services.AddAnthropicChatCompletion("claude-opus-4-20250514", "test-api-key-2", serviceId: serviceId2);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var service1 = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId1);
        var service2 = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId2);

        Assert.NotNull(service1);
        Assert.NotNull(service2);
        Assert.NotSame(service1, service2);
    }

    [Fact]
    public void AnthropicServiceAttributesContainModelId()
    {
        // Arrange
        var services = new ServiceCollection();
        const string modelId = "claude-sonnet-4-20250514";

        // Act
        services.AddAnthropicChatCompletion(modelId, "test-api-key");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService.Attributes.ContainsKey("ModelId"));
        Assert.Equal(modelId, chatCompletionService.Attributes["ModelId"]);
    }

    [Fact]
    public void AnthropicServiceWithAllParametersShouldBeRegistered()
    {
        // Arrange
        var services = new ServiceCollection();
        var customBaseUrl = new System.Uri("https://custom.anthropic.endpoint/");
        const string serviceId = "full-config-service";

        // Act
        services.AddAnthropicChatCompletion(
            modelId: "claude-sonnet-4-20250514",
            apiKey: "test-api-key",
            baseUrl: customBaseUrl,
            serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId);
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void KernelBuilderWithMultipleServicesReturnsCorrectService()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();
        const string serviceId1 = "service1";
        const string serviceId2 = "service2";

        // Act
        kernelBuilder.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key-1", serviceId: serviceId1);
        kernelBuilder.AddAnthropicChatCompletion("claude-opus-4-20250514", "test-api-key-2", serviceId: serviceId2);
        var kernel = kernelBuilder.Build();

        // Assert
        var service1 = kernel.GetRequiredService<IChatCompletionService>(serviceId1);
        var service2 = kernel.GetRequiredService<IChatCompletionService>(serviceId2);

        Assert.NotNull(service1);
        Assert.NotNull(service2);
        Assert.NotSame(service1, service2);
    }

    [Fact]
    public void KeyedServicesCanBeResolvedIndependently()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId1 = "service1";
        const string serviceId2 = "service2";

        // Act
        services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key-1", serviceId: serviceId1);
        services.AddAnthropicChatCompletion("claude-opus-4-20250514", "test-api-key-2", serviceId: serviceId2);
        var serviceProvider = services.BuildServiceProvider();

        // Assert - keyed services can be resolved independently
        var service1 = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId1);
        var service2 = serviceProvider.GetRequiredKeyedService<IChatCompletionService>(serviceId2);

        Assert.NotNull(service1);
        Assert.NotNull(service2);
        Assert.NotSame(service1, service2);

        // Verify they have different model IDs
        Assert.Equal("claude-sonnet-4-20250514", service1.Attributes["ModelId"]);
        Assert.Equal("claude-opus-4-20250514", service2.Attributes["ModelId"]);
    }
}
