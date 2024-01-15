// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests;

public sealed class GoogleVertexAIServiceCollectionExtensionsTests
{
    [Fact]
    public void GoogleAIGeminiTextGenerationServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleAIGeminiTextGeneration("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<GoogleAIGeminiTextGenerationService>(textGenerationService);
    }

    [Fact]
    public void GoogleAIGeminiTextGenerationServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleAIGeminiTextGeneration("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<GoogleAIGeminiTextGenerationService>(textGenerationService);
    }

    [Fact]
    public void VertexAIGeminiTextGenerationServiceShouldBeRegisteredInKernelServices()
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
    public void VertexAIGeminiTextGenerationServiceShouldBeRegisteredInServiceCollection()
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
    public void GoogleAIGeminiChatCompletionServiceAsIChatCompletionShouldBeRegisteredInKernelServices()
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
    public void GoogleAIGeminiChatCompletionServiceAsIChatCompletionShouldBeRegisteredInServiceCollection()
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
    public void VertexAIGeminiChatCompletionServiceAsIChatCompletionShouldBeRegisteredInKernelServices()
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
    public void VertexAIGeminiChatCompletionServiceAsIChatCompletionShouldBeRegisteredInServiceCollection()
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
    public void GoogleAIGeminiChatCompletionServiceAsITextGenerationShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleAIGeminiChatCompletion("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<GoogleAIGeminiChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void GoogleAIGeminiChatCompletionServiceAsITextGenerationShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleAIGeminiChatCompletion("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<GoogleAIGeminiChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void VertexAIGeminiChatCompletionServiceAsITextGenerationShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIGeminiChatCompletion("modelId", "apiKey", location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var textGenerationService = serviceProvider.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void VertexAIGeminiChatCompletionServiceAsITextGenerationShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIGeminiChatCompletion("modelId", "apiKey", location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var textGenerationService = kernel.GetRequiredService<ITextGenerationService>();
        Assert.NotNull(textGenerationService);
        Assert.IsType<VertexAIGeminiChatCompletionService>(textGenerationService);
    }

    [Fact]
    public void GoogleAIGeminiEmbeddingsGenerationServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddGoogleAIEmbeddingsGeneration("modelId", "apiKey");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<GoogleAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void GoogleAIGeminiEmbeddingsGenerationServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddGoogleAIEmbeddingsGeneration("modelId", "apiKey");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<GoogleAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void VertexAIGeminiEmbeddingsGenerationServiceShouldBeRegisteredInKernelServices()
    {
        // Arrange
        var kernelBuilder = Kernel.CreateBuilder();

        // Act
        kernelBuilder.AddVertexAIEmbeddingsGeneration("modelId", "apiKey", location: "test2", projectId: "projectId");
        var kernel = kernelBuilder.Build();

        // Assert
        var embeddingsGenerationService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }

    [Fact]
    public void VertexAIGeminiEmbeddingsGenerationServiceShouldBeRegisteredInServiceCollection()
    {
        // Arrange
        var services = new ServiceCollection();

        // Act
        services.AddVertexAIEmbeddingsGeneration("modelId", "apiKey", location: "test2", projectId: "projectId");
        var serviceProvider = services.BuildServiceProvider();

        // Assert
        var embeddingsGenerationService = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();
        Assert.NotNull(embeddingsGenerationService);
        Assert.IsType<VertexAITextEmbeddingGenerationService>(embeddingsGenerationService);
    }
}
