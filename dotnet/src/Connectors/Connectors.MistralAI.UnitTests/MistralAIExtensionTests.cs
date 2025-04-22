// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Reflection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.Connectors.MistralAI.UnitTests;

/// <summary>
/// Unit tests for <see cref="MistralAIServiceCollectionExtensions"/> and <see cref="MistralAIKernelBuilderExtensions"/>.
/// </summary>
public class MistralAIExtensionTests
{
    [Fact]
    public void AddMistralChatCompletionToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        collection.AddMistralChatCompletion("model", "apiKey");

        // Act
        var kernelBuilder = collection.AddKernel();
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<MistralAIChatCompletionService>(service);
    }

    [Fact]
    public void AddMistralTextEmbeddingGenerationToServiceCollection()
    {
        // Arrange
        var collection = new ServiceCollection();
        collection.AddMistralTextEmbeddingGeneration("model", "apiKey");

        // Act
        var kernelBuilder = collection.AddKernel();
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<MistralAITextEmbeddingGenerationService>(service);
    }

    [Fact]
    public void AddMistralChatCompletionToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        kernelBuilder.AddMistralChatCompletion("model", "apiKey");

        // Act
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<MistralAIChatCompletionService>(service);
    }

    [Fact]
    public void AddMistralTextEmbeddingGenerationToKernelBuilder()
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();
        kernelBuilder.AddMistralTextEmbeddingGeneration("model", "apiKey");

        // Act
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<MistralAITextEmbeddingGenerationService>(service);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void AddMistralChatCompletionInjectsExtraParametersHeader(bool useServiceCollection)
    {
        // Arrange
        var collection = new ServiceCollection();
        var kernelBuilder = collection.AddKernel();

        if (useServiceCollection)
        {
            // Use the service collection to add the Mistral chat completion
            kernelBuilder.Services.AddMistralChatCompletion(
                modelId: "model",
                apiKey: "key",
                endpoint: new Uri("https://example.com"));
        }
        else
        {
            // Use the kernel builder directly
            kernelBuilder.AddMistralChatCompletion(
                modelId: "model",
                apiKey: "key",
                endpoint: new Uri("https://example.com"));
        }

        // Act
        var kernel = collection.BuildServiceProvider().GetRequiredService<Kernel>();
        var service = kernel.GetRequiredService<IChatCompletionService>();

        // Assert
        Assert.NotNull(service);
        Assert.IsType<MistralAIChatCompletionService>(service);

        // Use reflection to get the private 'Client' field
        var clientField = typeof(MistralAIChatCompletionService)
            .GetField("<Client>k__BackingField", BindingFlags.NonPublic | BindingFlags.Instance);
        Assert.NotNull(clientField);

        var mistralClient = clientField.GetValue(service);
        Assert.NotNull(mistralClient);

        // Use reflection to get the private '_httpClient' field from MistralClient
        var httpClientField = mistralClient.GetType()
            .GetField("_httpClient", BindingFlags.NonPublic | BindingFlags.Instance);
        Assert.NotNull(httpClientField);

        var httpClient = (HttpClient)httpClientField.GetValue(mistralClient)!;
        Assert.True(httpClient.DefaultRequestHeaders.Contains("extra-parameters"));

        var headerValues = httpClient.DefaultRequestHeaders.GetValues("extra-parameters");
        Assert.Contains("pass-through", headerValues);
    }
}
