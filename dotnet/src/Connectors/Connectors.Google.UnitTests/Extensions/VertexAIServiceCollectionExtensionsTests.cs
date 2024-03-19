// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Extensions;

/// <summary>
/// Unit tests for <see cref="VertexAIServiceCollectionExtensions"/> and <see cref="VertexAIKernelBuilderExtensions"/> classes.
/// </summary>
public sealed class VertexAIServiceCollectionExtensionsTests
{
    [Fact]
    public void VertexAIGeminiTextGenerationServiceShouldBeRegisteredInKernelServicesBearerAsString()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIGeminiTextGeneration("modelId", "apiKey", location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<VertexAIGeminiTextGenerationService>(textGenerationService);
    }

    [Fact]
    public void VertexAIGeminiTextGenerationServiceShouldBeRegisteredInKernelServicesBearerAsFunc()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIGeminiTextGeneration("modelId", () => Task.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<VertexAIGeminiTextGenerationService>(textGenerationService);
    }

    [Fact]
    public void VertexAIGeminiTextGenerationServiceShouldBeRegisteredInServiceCollectionBearerAsString()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIGeminiTextGeneration("modelId", "apiKey", location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<VertexAIGeminiTextGenerationService>(textGenerationService);
    }

    [Fact]
    public void VertexAIGeminiTextGenerationServiceShouldBeRegisteredInServiceCollectionBearerAsFunc()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIGeminiTextGeneration("modelId", () => Task.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<VertexAIGeminiTextGenerationService>(textGenerationService);
    }

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
        kernelBuilder.AddVertexAIGeminiChatCompletion("modelId", () => Task.FromResult("apiKey"), location: "test2", projectId: "projectId");
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
        services.AddVertexAIGeminiChatCompletion("modelId", () => Task.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var chatCompletionService = serviceProvider.GetRequiredService<IChatCompletionService>();
        Assert.NotNull(chatCompletionService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(chatCompletionService);
    }

    [Fact]
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
    public void VertexAIEmbeddingGenerationServiceShouldBeRegisteredInKernelServicesBearerAsFunc()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIEmbeddingGeneration("modelId", () => Task.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
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
    public void VertexAIEmbeddingGenerationServiceShouldBeRegisteredInServiceCollectionBearerAsFunc()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIEmbeddingGeneration("modelId", () => Task.FromResult("apiKey"), location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }
}
