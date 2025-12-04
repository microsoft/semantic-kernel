// Copyright (c) Microsoft. All rights reserved.

using System;
using Google.GenAI;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="Microsoft.SemanticKernel.GoogleAIServiceCollectionExtensions"/> and <see cref="GoogleAIKernelBuilderExtensions"/> classes.
/// </summary>
public sealed class GoogleAIServiceCollectionExtensionsTests
{
    [Fact]
    public void GoogleAIGeminiChatCompletionServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleAIGeminiChatCompletion("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<GoogleAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void GoogleAIGeminiChatCompletionServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleAIGeminiChatCompletion("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<GoogleAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
    [Obsolete("Temporary Test for GoogleAITextEmbeddingGenerationService")]
    public void GoogleAIEmbeddingGenerationServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleAIEmbeddingGeneration("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<GoogleAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    [Obsolete("Temporary Test for GoogleAITextEmbeddingGenerationService")]
    public void GoogleAIEmbeddingGenerationServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleAIEmbeddingGeneration("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<GoogleAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void GoogleAIEmbeddingGeneratorShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleAIEmbeddingGenerator("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<GoogleAIEmbeddingGenerator>(embeddingsGenerationService);
    }

    [Fact]
    public void GoogleAIEmbeddingGeneratorShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleAIEmbeddingGenerator("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<GoogleAIEmbeddingGenerator>(embeddingsGenerationService);
    }

#if NET
    [Fact]
    public void GoogleGenAIChatClientShouldBeRegisteredInKernelServicesWithApiKey()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleGenAIChatClient("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void GoogleGenAIChatClientShouldBeRegisteredInServiceCollectionWithApiKey()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleGenAIChatClient("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void GoogleVertexAIChatClientShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleVertexAIChatClient("modelId", project: "test-project", location: "us-central1");

        // Assert - just verify no exception during registration
        // Resolution requires real credentials, so skip that in unit tests
        var kernel = kernelBuilder.Build();
        Assert.NotNull(kernel.Services);
    }

    [Fact]
    public void GoogleVertexAIChatClientShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleVertexAIChatClient("modelId", project: "test-project", location: "us-central1");
        var serviceProvider = services.BuildServiceProvider();

        // Assert - just verify no exception during registration
        // Resolution requires real credentials, so skip that in unit tests
        Assert.NotNull(serviceProvider);
    }

    [Fact]
    public void GoogleAIChatClientShouldBeRegisteredInKernelServicesWithClient()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();
        using var googleClient = new Client(apiKey: "apiKey");

        // Act
        kernelBuilder.AddGoogleAIChatClient("modelId", googleClient);
        var kernel = kernelBuilder.Build();

        // Assert
        var chatClient = kernel.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void GoogleAIChatClientShouldBeRegisteredInServiceCollectionWithClient()
    {
        // Arrange
        var services = new ServiceCollection();
        using var googleClient = new Client(apiKey: "apiKey");

        // Act
        services.AddGoogleAIChatClient("modelId", googleClient);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void GoogleGenAIChatClientShouldBeRegisteredWithServiceId()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId = "test-service-id";

        // Act
        services.AddGoogleGenAIChatClient("modelId", "apiKey", serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetKeyedService<IChatClient>(serviceId);
        Assert.NotNull(chatClient);
    }

    [Fact]
    public void GoogleVertexAIChatClientShouldBeRegisteredWithServiceId()
    {
        // Arrange
        var services = new ServiceCollection();
        const string serviceId = "test-service-id";

        // Act
        services.AddGoogleVertexAIChatClient("modelId", project: "test-project", location: "us-central1", serviceId: serviceId);
        var serviceProvider = services.BuildServiceProvider();

        // Assert - just verify no exception during registration
        // Resolution requires real credentials, so skip that in unit tests
        Assert.NotNull(serviceProvider);
    }

    [Fact]
    public void GoogleAIChatClientShouldResolveFromServiceProviderWhenClientNotProvided()
    {
        // Arrange
        var services = new ServiceCollection();
        using var googleClient = new Client(apiKey: "apiKey");
        services.AddSingleton(googleClient);

        // Act
        services.AddGoogleAIChatClient("modelId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatClient = serviceProvider.GetRequiredService<IChatClient>();
        Assert.NotNull(chatClient);
    }
#endif
}
