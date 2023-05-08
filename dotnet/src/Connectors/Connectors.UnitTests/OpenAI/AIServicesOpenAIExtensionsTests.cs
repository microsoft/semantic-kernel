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
        targetBuilder.AddAzureTextCompletionService("depl", "https://url", "key", serviceId: "azure");
        targetBuilder.AddOpenAITextCompletionService("model", "apikey", serviceId: "oai");
        targetBuilder.AddAzureTextEmbeddingGenerationService("depl2", "https://url2", "key", serviceId: "azure");
        targetBuilder.AddOpenAITextEmbeddingGenerationService("model2", "apikey2", serviceId: "oai2");

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
        targetBuilder.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.AddAzureTextCompletionService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.AddOpenAITextCompletionService("model", "key, serviceId: \"one\"");
        targetBuilder.AddOpenAITextCompletionService("model", "key", serviceId: "one");
        targetBuilder.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.AddAzureTextEmbeddingGenerationService("dep", "https://localhost", "key", serviceId: "one");
        targetBuilder.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "one");
        targetBuilder.AddOpenAITextEmbeddingGenerationService("model", "key", serviceId: "one");
    }
}
