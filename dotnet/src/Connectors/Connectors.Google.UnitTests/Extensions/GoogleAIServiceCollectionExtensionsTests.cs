// Copyright (c) Microsoft. All rights reserved.

using System;
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
}
