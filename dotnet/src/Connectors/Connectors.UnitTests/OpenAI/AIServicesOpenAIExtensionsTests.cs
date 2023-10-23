// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="OpenAIKernelBuilderExtensions"/>.
/// </summary>
public class AIServicesOpenAIExtensionsTests
{
    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        KernelBuilder targetBuilder = Kernel.Builder;
        targetBuilder.WithAzureTextCompletionService("depl", "https://url", "key", "azure");
        targetBuilder.WithAzureTextEmbeddingGenerationService("depl2", "https://url", "key", "azure");

        IKernel targetKernel = targetBuilder.Build();
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        KernelBuilder targetBuilder = Kernel.Builder;
        targetBuilder.WithAzureTextCompletionService("depl", "https://url", "key", serviceId: "azure");
        targetBuilder.WithOpenAITextCompletionService("model", "apikey", serviceId: "oai");
        targetBuilder.WithAzureTextEmbeddingGenerationService("depl2", "https://url2", "key", serviceId: "azure");
        targetBuilder.WithOpenAITextEmbeddingGenerationService("model2", "apikey2", serviceId: "oai2");

        // Assert
        IKernel targetKernel = targetBuilder.Build();
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("oai"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        KernelBuilder targetBuilder = Kernel.Builder;

        // Act - Assert no exception occurs
        targetBuilder.WithAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.WithAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");

        targetBuilder.WithOpenAITextCompletionService("model", "key", serviceId: "one");
        targetBuilder.WithOpenAITextCompletionService("model", "key", serviceId: "one");

        targetBuilder.WithAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.WithAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "one");

        targetBuilder.WithOpenAITextEmbeddingGenerationService("model", "key", serviceId: "one");
        targetBuilder.WithOpenAITextEmbeddingGenerationService("model", "key", serviceId: "one");

        targetBuilder.WithAzureChatCompletionService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.WithAzureChatCompletionService("dep", "https://localhost", "key", serviceId: "one");

        targetBuilder.WithOpenAIChatCompletionService("model", "key", serviceId: "one");
        targetBuilder.WithOpenAIChatCompletionService("model", "key", serviceId: "one");

        targetBuilder.WithOpenAIImageGenerationService("model", "key", serviceId: "one");
        targetBuilder.WithOpenAIImageGenerationService("model", "key", serviceId: "one");

        targetBuilder.WithDefaultAIService(new OpenAITextCompletion("model", "key"));
        targetBuilder.WithDefaultAIService(new OpenAITextCompletion("model", "key"));

        targetBuilder.WithDefaultAIService((_) => new OpenAITextCompletion("model", "key"));
        targetBuilder.WithDefaultAIService((_) => new OpenAITextCompletion("model", "key"));

        targetBuilder.WithAIService<ITextCompletion>("one", new OpenAITextCompletion("model", "key"));
        targetBuilder.WithAIService<ITextCompletion>("one", new OpenAITextCompletion("model", "key"));

        targetBuilder.WithAIService<ITextCompletion>("one", (loggerFactory) => new OpenAITextCompletion("model", "key"));
        targetBuilder.WithAIService<ITextCompletion>("one", (loggerFactory) => new OpenAITextCompletion("model", "key"));
    }
}
