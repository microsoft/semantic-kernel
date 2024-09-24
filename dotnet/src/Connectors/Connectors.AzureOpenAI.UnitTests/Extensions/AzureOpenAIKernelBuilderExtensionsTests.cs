// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;

namespace SemanticKernel.Connectors.AzureOpenAI.UnitTests.Extensions;

/// <summary>
/// Unit tests for the kernel builder extensions in the <see cref="AzureOpenAIKernelBuilderExtensions"/> class.
/// </summary>
public sealed class AzureOpenAIKernelBuilderExtensionsTests
{
    #region Chat completion

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void KernelBuilderAddAzureOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("http://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAIChatCompletion("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAIChatCompletion("deployment-name"),
            _ => builder
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService is AzureOpenAIChatCompletionService);

        var textGenerationService = builder.Build().GetRequiredService<ITextGenerationService>();
        Assert.True(textGenerationService is AzureOpenAIChatCompletionService);
    }

    #endregion

    #region Text embeddings

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void KernelBuilderAddAzureOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("http://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextEmbeddingGenerationService);
    }

    #endregion

    #region Text to audio

    [Fact]
    public void KernelBuilderAddAzureOpenAITextToAudioAddsValidService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddAzureOpenAITextToAudio("deployment-name", "https://endpoint", "api-key")
            .Build()
            .GetRequiredService<ITextToAudioService>();

        // Assert
        Assert.IsType<AzureOpenAITextToAudioService>(service);
    }

    #endregion

    #region Text to image

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void KernelBuilderExtensionsAddAzureOpenAITextToImageService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("http://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAITextToImage("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAITextToImage("deployment-name"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.True(service is AzureOpenAITextToImageService);
    }

    #endregion

    #region Audio to text

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void KernelBuilderAddAzureOpenAIAudioToTextAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("http://endpoint"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAIAudioToText("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAIAudioToText("deployment-name"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IAudioToTextService>();

        Assert.IsType<AzureOpenAIAudioToTextService>(service);
    }

    #endregion

    public enum InitializationType
    {
        ApiKey,
        TokenCredential,
        ClientInline,
        ClientInServiceProvider,
        ClientEndpoint,
    }
}
