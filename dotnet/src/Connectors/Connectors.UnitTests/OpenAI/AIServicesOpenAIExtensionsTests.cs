// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
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
            .WithAzureOpenAITextCompletion("depl", "https://url", "key", "azure")
            .WithAzureOpenAITextEmbeddingGeneration("depl2", "https://url", "key", "azure")
            .Build();

        Assert.NotNull(targetKernel.GetService<ITextCompletion>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        Kernel targetKernel = new KernelBuilder()
            .WithAzureOpenAITextCompletion("depl", "https://url", "key", serviceId: "azure")
            .WithOpenAITextCompletion("model", "apikey", serviceId: "oai")
            .WithAzureOpenAITextEmbeddingGeneration("depl2", "https://url2", "key", serviceId: "azure")
            .WithOpenAITextEmbeddingGeneration("model2", "apikey2", serviceId: "oai2")
            .Build();

        // Assert
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("oai"));
        Assert.NotNull(targetKernel.GetService<ITextEmbeddingGeneration>("azure"));
        Assert.NotNull(targetKernel.GetService<ITextCompletion>("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        // Act - Assert no exception occurs
        new KernelBuilder().WithServices(c =>
        {
            c.AddAzureOpenAITextCompletion("dep", "https://localhost", "key", serviceId: "one");
            c.AddAzureOpenAITextCompletion("dep", "https://localhost", "key", serviceId: "one");

            c.AddOpenAITextCompletion("model", "key", serviceId: "one");
            c.AddOpenAITextCompletion("model", "key", serviceId: "one");

            c.AddAzureOpenAITextEmbeddingGeneration("dep", "https://localhost", "key", serviceId: "one");
            c.AddAzureOpenAITextEmbeddingGeneration("dep", "https://localhost", "key", serviceId: "one");

            c.AddOpenAITextEmbeddingGeneration("model", "key", serviceId: "one");
            c.AddOpenAITextEmbeddingGeneration("model", "key", serviceId: "one");

            c.AddAzureOpenAIChatCompletion("dep", "https://localhost", "key", serviceId: "one");
            c.AddAzureOpenAIChatCompletion("dep", "https://localhost", "key", serviceId: "one");

            c.AddOpenAIChatCompletion("model", "key", serviceId: "one");
            c.AddOpenAIChatCompletion("model", "key", serviceId: "one");

            c.AddOpenAIImageGeneration("model", "key", serviceId: "one");
            c.AddOpenAIImageGeneration("model", "key", serviceId: "one");

            c.AddSingleton(new OpenAITextCompletion("model", "key"));
            c.AddSingleton(new OpenAITextCompletion("model", "key"));

            c.AddSingleton((_) => new OpenAITextCompletion("model", "key"));
            c.AddSingleton((_) => new OpenAITextCompletion("model", "key"));

            c.AddKeyedSingleton<ITextCompletion>("one", new OpenAITextCompletion("model", "key"));
            c.AddKeyedSingleton<ITextCompletion>("one", new OpenAITextCompletion("model", "key"));

            c.AddKeyedSingleton<ITextCompletion>("one", (_, _) => new OpenAITextCompletion("model", "key"));
            c.AddKeyedSingleton<ITextCompletion>("one", (_, _) => new OpenAITextCompletion("model", "key"));
        }).Build();
    }
}
