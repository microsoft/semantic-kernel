// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="OpenAKernelBuilderExtensions"/>.
/// </summary>
public class AIServicesOpenAIExtensionsTests
{
    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        KernelBuilder targetBuilder = Kernel.Builder;
        targetBuilder.AddAzureTextCompletionService("depl", "https://url", "key", "azure");
        targetBuilder.AddAzureTextEmbeddingGenerationService("depl2", "https://url", "key", "azure");

        IKernel targetKernel = targetBuilder.Build();
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        KernelBuilder targetBuilder = Kernel.Builder;
        targetBuilder.AddAzureTextCompletionService("azure", "depl", "https://url", "key");
        targetBuilder.AddOpenAITextCompletionService("oai", "model", "apikey");
        targetBuilder.AddAzureTextEmbeddingGenerationService("azure", "depl2", "https://url2", "key");
        targetBuilder.AddOpenAITextEmbeddingGenerationService("oai2", "model2", "apikey2");

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
        targetBuilder.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        targetBuilder.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        targetBuilder.AddOpenAITextCompletionService("one", "model", "key");
        targetBuilder.AddOpenAITextCompletionService("one", "model", "key");
        targetBuilder.AddAzureTextEmbeddingGenerationService("one", "dep", "https://localhost", "key");
        targetBuilder.AddAzureTextEmbeddingGenerationService("one", "dep", "https://localhost", "key");
        targetBuilder.AddOpenAITextEmbeddingGenerationService("one", "model", "key");
        targetBuilder.AddOpenAITextEmbeddingGenerationService("one", "model", "key");
    }
}
