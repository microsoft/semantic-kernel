// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="Microsoft.SemanticKernel.VertexAIServiceCollectionExtensions"/> and <see cref="VertexAIKernelBuilderExtensions"/> classes.
/// </summary>
public sealed class VertexAIServiceCollectionExtensionsTests
{
    [Fact]
    public void VertexAIGeminiChatCompletionServiceShouldBeRegisteredInKernelServicesBearerAsString()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIGeminiChatCompletion("modelId", "apiKey", location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void VertexAIGeminiChatCompletionServiceShouldBeRegisteredInKernelServicesBearerAsFunc()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIGeminiChatCompletion("modelId", () => ValueTask.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void VertexAIGeminiChatCompletionServiceShouldBeRegisteredInServiceCollectionBearerAsString()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIGeminiChatCompletion("modelId", "apiKey", location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
    public void VertexAIGeminiChatCompletionServiceShouldBeRegisteredInServiceCollectionBearerAsFunc()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIGeminiChatCompletion("modelId", () => ValueTask.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
    [Obsolete("Temporary Test for VertexAITextEmbeddingGenerationService")]
    public void VertexAIEmbeddingGenerationServiceShouldBeRegisteredInKernelServicesBearerAsString()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIEmbeddingGeneration("modelId", "apiKey", location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void VertexAIEmbeddingGeneratorShouldBeRegisteredInKernelServicesBearerAsString()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIEmbeddingGenerator("modelId", "apiKey", location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAIEmbeddingGenerator>(embeddingsGenerationService);
    }

    [Fact]
    [Obsolete("Temporary Test for VertexAITextEmbeddingGenerationService")]
    public void VertexAIEmbeddingGenerationServiceShouldBeRegisteredInKernelServicesBearerAsFunc()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIEmbeddingGeneration("modelId", () => ValueTask.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void VertexAIEmbeddingGeneratorShouldBeRegisteredInKernelServicesBearerAsFunc()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIEmbeddingGenerator("modelId", () => ValueTask.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAIEmbeddingGenerator>(embeddingsGenerationService);
    }

    [Fact]
    [Obsolete("Temporary Test for VertexAITextEmbeddingGenerationService")]
    public void VertexAIEmbeddingGenerationServiceShouldBeRegisteredInServiceCollectionBearerAsString()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIEmbeddingGeneration("modelId", "apiKey", location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void VertexAIEmbeddingGeneratorShouldBeRegisteredInServiceCollectionBearerAsString()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIEmbeddingGenerator("modelId", "apiKey", location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAIEmbeddingGenerator>(embeddingsGenerationService);
    }

    [Fact]
    [Obsolete("Temporary Test for VertexAITextEmbeddingGenerationService")]
    public void VertexAIEmbeddingGenerationServiceShouldBeRegisteredInServiceCollectionBearerAsFunc()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIEmbeddingGeneration("modelId", () => ValueTask.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void VertexAIEmbeddingGeneratorShouldBeRegisteredInServiceCollectionBearerAsFunc()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIEmbeddingGenerator("modelId", () => ValueTask.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAIEmbeddingGenerator>(embeddingsGenerationService);
    }
}
