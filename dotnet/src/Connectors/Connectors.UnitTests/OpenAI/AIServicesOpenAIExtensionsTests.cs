// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
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
        Kernel targetKernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextGeneration("depl", "https://url", "key", "azure")
            .AddAzureOpenAITextEmbeddingGeneration("depl2", "https://url", "key", "azure")
            .Build();

        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextEmbeddingGenerationService>("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        Kernel targetKernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextGeneration("depl", "https://url", "key", serviceId: "azure")
            .AddOpenAITextGeneration("model", "apikey", serviceId: "oai")
            .AddAzureOpenAITextEmbeddingGeneration("depl2", "https://url2", "key", serviceId: "azure")
            .AddOpenAITextEmbeddingGeneration("model2", "apikey2", serviceId: "oai2")
            .Build();

        // Assert
        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("oai"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextEmbeddingGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        // Act - Assert no exception occurs
        var builder = Kernel.CreateBuilder();

        builder.Services.AddAzureOpenAITextGeneration("depl", "https://localhost", "key", serviceId: "one");
        builder.Services.AddAzureOpenAITextGeneration("depl", "https://localhost", "key", serviceId: "one");

        builder.Services.AddOpenAITextGeneration("model", "key", serviceId: "one");
        builder.Services.AddOpenAITextGeneration("model", "key", serviceId: "one");

        builder.Services.AddAzureOpenAITextEmbeddingGeneration("dep", "https://localhost", "key", serviceId: "one");
        builder.Services.AddAzureOpenAITextEmbeddingGeneration("dep", "https://localhost", "key", serviceId: "one");

        builder.Services.AddOpenAITextEmbeddingGeneration("model", "key", serviceId: "one");
        builder.Services.AddOpenAITextEmbeddingGeneration("model", "key", serviceId: "one");

        builder.Services.AddAzureOpenAIChatCompletion("dep", "https://localhost", "key", serviceId: "one");
        builder.Services.AddAzureOpenAIChatCompletion("dep", "https://localhost", "key", serviceId: "one");

        builder.Services.AddOpenAIChatCompletion("model", "key", serviceId: "one");
        builder.Services.AddOpenAIChatCompletion("model", "key", serviceId: "one");

        builder.Services.AddOpenAITextToImage("model", "key", serviceId: "one");
        builder.Services.AddOpenAITextToImage("model", "key", serviceId: "one");

        builder.Services.AddSingleton(new OpenAITextGenerationService("model", "key"));
        builder.Services.AddSingleton(new OpenAITextGenerationService("model", "key"));

        builder.Services.AddSingleton((_) => new OpenAITextGenerationService("model", "key"));
        builder.Services.AddSingleton((_) => new OpenAITextGenerationService("model", "key"));

        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", new OpenAITextGenerationService("model", "key"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", new OpenAITextGenerationService("model", "key"));

        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", (_, _) => new OpenAITextGenerationService("model", "key"));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", (_, _) => new OpenAITextGenerationService("model", "key"));

        builder.Build();
    }
}
