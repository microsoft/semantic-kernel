// Copyright (c) Microsoft. All rights reserved.

using Anthropic;
using Anthropic.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="AnthropicServiceCollectionExtensions"/>.
/// </summary>
public sealed class AnthropicServiceCollectionExtensionsTests
{
    #region AddAnthropicChatCompletion Registration Tests

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void AddAnthropicChatCompletionRegistersServices(InitializationType type)
    {
        // Arrange
        var clientOptions = new ClientOptions { APIKey = "test-api-key" };
        var client = new AnthropicClient(clientOptions);
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(client);

        // Act
        _ = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", "test-api-key"),
            InitializationType.ClientInline => builder.Services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAnthropicChatCompletion("claude-sonnet-4-20250514", anthropicClient: null),
            _ => builder.Services
        };

        var kernel = builder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);

        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<AnthropicChatCompletionService>(textGenerationService);
    }

    #endregion

    #region AddAnthropicChatClient Registration Tests

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void AddAnthropicChatClientRegistersService(InitializationType type)
    {
        // Arrange
        var clientOptions = new ClientOptions { APIKey = "test-api-key" };
        var client = new AnthropicClient(clientOptions);
        var builder = Kernel.CreateBuilder();
        builder.Services.AddSingleton(client);

        // Act
        _ = type switch
        {
            InitializationType.ApiKey => builder.Services.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key"),
            InitializationType.ClientInline => builder.Services.AddAnthropicChatClient("claude-sonnet-4-20250514", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddAnthropicChatClient("claude-sonnet-4-20250514", anthropicClient: null),
            _ => builder.Services
        };

        var kernel = builder.Build();

        // Assert
        var chatClient = kernel.Services.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    #endregion

    #region Singleton and Instance Sharing Tests

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

    #endregion

    #region Configuration and Parameter Tests

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
        Assert.True(chatCompletionService.Attributes.ContainsKey(AIServiceExtensions.ModelIdKey));
        Assert.Equal(modelId, chatCompletionService.Attributes[AIServiceExtensions.ModelIdKey]);
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
        Assert.Equal("claude-sonnet-4-20250514", service1.Attributes[AIServiceExtensions.ModelIdKey]);
        Assert.Equal("claude-opus-4-20250514", service2.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    #endregion

    #region IKernelBuilder Extension Tests

    [Fact]
    public void KernelBuilderAddAnthropicChatCompletionWithClientRegistersServices()
    {
        // Arrange
        var clientOptions = new ClientOptions { APIKey = "test-api-key" };
        var client = new AnthropicClient(clientOptions);
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicChatCompletion("claude-sonnet-4-20250514", client);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<AnthropicChatCompletionService>(chatCompletionService);

        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<AnthropicChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void KernelBuilderAddAnthropicChatClientWithApiKeyRegistersService()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key");
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.Services.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void KernelBuilderAddAnthropicChatClientWithClientRegistersService()
    {
        // Arrange
        var clientOptions = new ClientOptions { APIKey = "test-api-key" };
        var client = new AnthropicClient(clientOptions);
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddAnthropicChatClient("claude-sonnet-4-20250514", client);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.Services.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void KernelBuilderAddAnthropicChatClientWithServiceIdRegistersKeyedService()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();
        const string serviceId = "my-chat-client";

        // Act
        kernelBuilder.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key", serviceId: serviceId);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.Services.GetRequiredKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    #endregion

    #region IChatClient Keyed Service Tests

    [Fact]
    public void AddAnthropicChatClientWithServiceIdShouldBeRegisteredAsKeyed()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId = "anthropic-chat-client";

        // Act
        services.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key", serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetRequiredKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void MultipleAnthropicChatClientsCanBeRegisteredWithDifferentServiceIds()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId1 = "chat-client-sonnet";
        const string serviceId2 = "chat-client-opus";

        // Act
        services.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key-1", serviceId: serviceId1);
        services.AddAnthropicChatClient("claude-opus-4-20250514", "test-api-key-2", serviceId: serviceId2);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var client1 = serviceProvider.GetRequiredKeyedService<IChatClient>(serviceId1);
        var client2 = serviceProvider.GetRequiredKeyedService<IChatClient>(serviceId2);

        Assert.NotNull(client1);
        Assert.NotNull(client2);
        Assert.NotSame(client1, client2);
    }

    #endregion

    #region IChatClient Configuration Tests

    [Fact]
    public void AddAnthropicChatClientWithCustomBaseUrlShouldBeRegistered()
    {
        // Arrange
        var services = new ServiceCollection();
        var customBaseUrl = new System.Uri("https://custom.anthropic.endpoint/");

        // Act
        services.AddAnthropicChatClient("claude-sonnet-4-20250514", "test-api-key", baseUrl: customBaseUrl);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void AddAnthropicChatClientWithAllParametersShouldBeRegistered()
    {
        // Arrange
        var services = new ServiceCollection();
        var customBaseUrl = new System.Uri("https://custom.anthropic.endpoint/");
        const string serviceId = "full-config-chat-client";

        // Act
        services.AddAnthropicChatClient(
            modelId: "claude-sonnet-4-20250514",
            apiKey: "test-api-key",
            baseUrl: customBaseUrl,
            serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetRequiredKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    #endregion
}

/// <summary>
/// Specifies the type of initialization used when registering Anthropic services.
/// </summary>
public enum InitializationType
{
    /// <summary>
    /// Initialize with API key string.
    /// </summary>
    ApiKey,

    /// <summary>
    /// Initialize with an inline AnthropicClient instance.
    /// </summary>
    ClientInline,

    /// <summary>
    /// Initialize with AnthropicClient resolved from the service provider.
    /// </summary>
    ClientInServiceProvider
}
