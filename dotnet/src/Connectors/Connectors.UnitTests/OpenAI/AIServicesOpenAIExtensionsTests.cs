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
            .AddAzureOpenAITextGeneration(new() { DeploymentName = "depl", ModelId = "model", Endpoint = "https://url", ApiKey = "key" }, "azure")
            .AddAzureOpenAITextEmbeddingGeneration(new() { DeploymentName = "depl2", ModelId = "model2", Endpoint = "https://url2", ApiKey = "key" }, "azure")
            .Build();

        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextEmbeddingGeneration>("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        Kernel targetKernel = Kernel.CreateBuilder()
            .AddAzureOpenAITextGeneration(new() { DeploymentName = "depl", ModelId = "model", Endpoint = "https://url", ApiKey = "key" }, serviceId: "azure")
            .AddOpenAITextGeneration(new() { ModelId = "model", ApiKey = "apikey" }, serviceId: "oai")
            .AddAzureOpenAITextEmbeddingGeneration(new() { DeploymentName = "depl2", ModelId = "model2", Endpoint = "https://url2", ApiKey = "key" }, serviceId: "azure")
            .AddOpenAITextEmbeddingGeneration(new() { ModelId = "model2", ApiKey = "apikey2" }, serviceId: "oai2")
            .Build();

        // Assert
        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("azure"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("oai"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextEmbeddingGeneration>("azure"));
        Assert.NotNull(targetKernel.GetRequiredService<ITextGenerationService>("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        // Act - Assert no exception occurs
        var builder = Kernel.CreateBuilder();

        builder.Services.AddAzureOpenAITextGeneration(new() { DeploymentName = "dep", ModelId = "model", Endpoint = "https://localhost", ApiKey = "key" }, serviceId: "one");
        builder.Services.AddAzureOpenAITextGeneration(new() { DeploymentName = "dep", ModelId = "model", Endpoint = "https://localhost", ApiKey = "key" }, serviceId: "one");

        builder.Services.AddOpenAITextGeneration(new() { ModelId = "model", ApiKey = "apikey" }, serviceId: "one");
        builder.Services.AddOpenAITextGeneration(new() { ModelId = "model", ApiKey = "apikey" }, serviceId: "one");

        builder.Services.AddAzureOpenAITextEmbeddingGeneration(new() { DeploymentName = "dep", ModelId = "model", Endpoint = "https://localhost", ApiKey = "key" }, serviceId: "one");
        builder.Services.AddAzureOpenAITextEmbeddingGeneration(new() { DeploymentName = "dep", ModelId = "model", Endpoint = "https://localhost", ApiKey = "key" }, serviceId: "one");

        builder.Services.AddOpenAITextEmbeddingGeneration(new() { ModelId = "model", ApiKey = "key" }, serviceId: "one");
        builder.Services.AddOpenAITextEmbeddingGeneration(new() { ModelId = "model", ApiKey = "key" }, serviceId: "one");

        builder.Services.AddAzureOpenAIChatCompletion(new() { DeploymentName = "dep", ModelId = "model", Endpoint = "https://localhost", ApiKey = "key" }, serviceId: "one");
        builder.Services.AddAzureOpenAIChatCompletion(new() { DeploymentName = "dep", ModelId = "model", Endpoint = "https://localhost", ApiKey = "key" }, serviceId: "one");

        builder.Services.AddOpenAIChatCompletion(new() { ModelId = "model", ApiKey = "key" }, serviceId: "one");
        builder.Services.AddOpenAIChatCompletion(new() { ModelId = "model", ApiKey = "key" }, serviceId: "one");

        builder.Services.AddOpenAITextToImage("model", "key", serviceId: "one");
        builder.Services.AddOpenAITextToImage("model", "key", serviceId: "one");

        builder.Services.AddSingleton(new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));
        builder.Services.AddSingleton(new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));

        builder.Services.AddSingleton((_) => new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));
        builder.Services.AddSingleton((_) => new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));

        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));

        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", (_, _) => new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));
        builder.Services.AddKeyedSingleton<ITextGenerationService>("one", (_, _) => new OpenAITextGenerationService(new() { ModelId = "model", ApiKey = "apikey" }));

        builder.Build();
    }
}
