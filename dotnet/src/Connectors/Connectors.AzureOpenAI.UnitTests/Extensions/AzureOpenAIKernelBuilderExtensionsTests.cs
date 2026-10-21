// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;

#pragma warning disable MEAI001 // Image generation APIs are experimental.

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
    [InlineData(InitializationType.ApiVersion)]
    public void KernelBuilderAddAzureOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAIChatCompletion("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAIChatCompletion("deployment-name"),
            InitializationType.ApiVersion => builder.AddAzureOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
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
    [InlineData(InitializationType.ApiVersion)]
    [Obsolete("Temporary Obsoleted AzureOpenAITextEmbeddingGeneration tests.")]
    public void KernelBuilderAddAzureOpenAITextEmbeddingGenerationAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name"),
            InitializationType.ApiVersion => builder.AddAzureOpenAITextEmbeddingGeneration("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.True(service is AzureOpenAITextEmbeddingGenerationService);
    }

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    public void KernelBuilderAddAzureOpenAIEmbeddingGeneratorAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAIEmbeddingGenerator("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAIEmbeddingGenerator("deployment-name"),
            InitializationType.ApiVersion => builder.AddAzureOpenAIEmbeddingGenerator("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        Assert.NotNull(service);
    }

    #endregion

    #region Text to audio

    [Fact]
    public void KernelBuilderAddAzureOpenAITextToAudioAddsValidService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddAzureOpenAITextToAudio("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview")
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
    [InlineData(InitializationType.ApiVersion)]
    public void KernelBuilderExtensionsAddAzureOpenAITextToImageService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAITextToImage("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAITextToImage("deployment-name"),
            InitializationType.ApiVersion => builder.AddAzureOpenAITextToImage("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
            _ => builder
        };

        // Assert
        var service = builder.Build().GetRequiredService<ITextToImageService>();

        Assert.True(service is AzureOpenAITextToImageService);
    }

    #endregion

    #region Image Generation

    [Theory]
    [InlineData(InitializationType.ApiKey, null)]
    [InlineData(InitializationType.ApiKey, "images")]
    [InlineData(InitializationType.TokenCredential, null)]
    [InlineData(InitializationType.TokenCredential, "images")]
    [InlineData(InitializationType.ClientInline, null)]
    [InlineData(InitializationType.ClientInline, "images")]
    [InlineData(InitializationType.ClientInServiceProvider, null)]
    [InlineData(InitializationType.ClientInServiceProvider, "images")]
    [InlineData(InitializationType.ApiVersion, null)]
    [InlineData(InitializationType.ApiVersion, "images")]
    public void KernelBuilderAddAzureOpenAIImageGeneratorAddsValidService(InitializationType type, string? serviceId)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://localhost"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();
        bool telemetryConfigured = false;
        void configureTelemetry(OpenTelemetryImageGenerator _) => telemetryConfigured = true;
        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", "api-key", serviceId, openTelemetryConfig: configureTelemetry),
            InitializationType.TokenCredential => builder.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", credentials, serviceId, openTelemetryConfig: configureTelemetry),
            InitializationType.ClientInline => builder.AddAzureOpenAIImageGenerator("deployment-name", client, serviceId, openTelemetryConfig: configureTelemetry),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAIImageGenerator("deployment-name", serviceId: serviceId, openTelemetryConfig: configureTelemetry),
            InitializationType.ApiVersion => builder.AddAzureOpenAIImageGenerator("deployment-name", "https://endpoint", "api-key", serviceId, apiVersion: "2025-04-01-preview", openTelemetryConfig: configureTelemetry),
            _ => throw new ArgumentOutOfRangeException(nameof(type))
        };

        // Assert
        var kernel = builder.Build();
        var service = kernel.GetRequiredService<IImageGenerator>(serviceId);
        Assert.Equal("deployment-name", service.GetService<ImageGeneratorMetadata>()!.DefaultModelId);
        Assert.Same(service, kernel.GetRequiredService<IImageGenerator>(serviceId));
        Assert.True(telemetryConfigured);
    }

    #endregion

    #region Audio to text

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.TokenCredential)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    [InlineData(InitializationType.ApiVersion)]
    public void KernelBuilderAddAzureOpenAIAudioToTextAddsValidService(InitializationType type)
    {
        // Arrange
        var credentials = DelegatedTokenCredential.Create((_, _) => new AccessToken());
        var client = new AzureOpenAIClient(new Uri("https://endpoint"), new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton<AzureOpenAIClient>(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", "api-key"),
            InitializationType.TokenCredential => builder.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", credentials),
            InitializationType.ClientInline => builder.AddAzureOpenAIAudioToText("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.AddAzureOpenAIAudioToText("deployment-name"),
            InitializationType.ApiVersion => builder.AddAzureOpenAIAudioToText("deployment-name", "https://endpoint", "api-key", apiVersion: "2024-10-01-preview"),
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
        ApiVersion
    }
}
