// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="OpenAIServiceCollectionExtensions"/>.
/// </summary>
public class AIServicesOpenAIExtensionsTests
{
    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        Kernel targetKernel = new KernelBuilder()
            .WithAzureOpenAITextGeneration("depl", "model", "https://url", "key", "azure")
            .WithAzureOpenAITextEmbeddingGeneration("depl2", "model2", "https://url", "key", "azure")
            .Build();

        Assert.NotNull(targetKernel.GetService<ITextGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        Kernel targetKernel = new KernelBuilder()
            .WithAzureOpenAITextGeneration("depl", "model", "https://url", "key", serviceId: "azure")
            .WithOpenAITextGeneration("model", "apikey", serviceId: "oai")
            .WithAzureOpenAITextEmbeddingGeneration("depl2", "model2", "https://url2", "key", serviceId: "azure")
            .WithOpenAITextEmbeddingGeneration("model2", "apikey2", serviceId: "oai2")
            .Build();

        // Assert
        Assert.NotNull(targetKernel.GetService<ITextGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextGenerationService>("oai"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextGenerationService>("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        // Act - Assert no exception occurs
        new KernelBuilder().WithServices(c =>
        {
            c.AddAzureOpenAITextGeneration("dep", "model", "https://localhost", "key", serviceId: "one");
            c.AddAzureOpenAITextGeneration("dep", "model", "https://localhost", "key", serviceId: "one");

            c.AddOpenAITextGeneration("model", "key", serviceId: "one");
            c.AddOpenAITextGeneration("model", "key", serviceId: "one");

            c.AddAzureOpenAITextEmbeddingGeneration("dep", "model", "https://localhost", "key", serviceId: "one");
            c.AddAzureOpenAITextEmbeddingGeneration("dep", "model", "https://localhost", "key", serviceId: "one");

            c.AddOpenAITextEmbeddingGeneration("model", "key", serviceId: "one");
            c.AddOpenAITextEmbeddingGeneration("model", "key", serviceId: "one");

            c.AddAzureOpenAIChatCompletion("dep", "model", "https://localhost", "key", serviceId: "one");
            c.AddAzureOpenAIChatCompletion("dep", "model", "https://localhost", "key", serviceId: "one");

            c.AddOpenAIChatCompletion("model", "key", serviceId: "one");
            c.AddOpenAIChatCompletion("model", "key", serviceId: "one");

            c.AddOpenAITextToImage("model", "key", serviceId: "one");
            c.AddOpenAITextToImage("model", "key", serviceId: "one");

            c.AddSingleton(new OpenAITextGenerationService("model", "key"));
            c.AddSingleton(new OpenAITextGenerationService("model", "key"));

            c.AddSingleton((_) => new OpenAITextGenerationService("model", "key"));
            c.AddSingleton((_) => new OpenAITextGenerationService("model", "key"));

            c.AddKeyedSingleton<ITextGenerationService>("one", new OpenAITextGenerationService("model", "key"));
            c.AddKeyedSingleton<ITextGenerationService>("one", new OpenAITextGenerationService("model", "key"));

            c.AddKeyedSingleton<ITextGenerationService>("one", (_, _) => new OpenAITextGenerationService("model", "key"));
            c.AddKeyedSingleton<ITextGenerationService>("one", (_, _) => new OpenAITextGenerationService("model", "key"));
        }).Build();
    }
}
