// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextGeneration;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public class KernelBuilderExtensionsTests
{
    [Fact]
    public void ItCanAddTextEmbeddingGenerationService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAITextEmbeddingGeneration("model", "key")
            .Build()
            .GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddTextEmbeddingGenerationServiceWithOpenAIClient()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAITextEmbeddingGeneration("model", new OpenAIClient(new ApiKeyCredential("key")))
            .Build()
            .GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddTextToImageService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAITextToImage("key", modelId: "model")
            .Build()
            .GetRequiredService<ITextToImageService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddTextToAudioService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAITextToAudio("model", "key")
            .Build()
            .GetRequiredService<ITextToAudioService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddAudioToTextService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAIAudioToText("model", "key")
            .Build()
            .GetRequiredService<IAudioToTextService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddAudioToTextServiceWithOpenAIClient()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAIAudioToText("model", new OpenAIClient(new ApiKeyCredential("key")))
            .Build()
            .GetRequiredService<IAudioToTextService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    [Obsolete("This test is deprecated and will be removed in a future version.")]
    public void ItCanAddFileService()
    {
        // Arrange
        var sut = Kernel.CreateBuilder();

        // Act
        var service = sut.AddOpenAIFiles("key").Build()
            .GetRequiredService<OpenAIFileService>();
    }

    #region Chat completion

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.OpenAIClientInline)]
    [InlineData(InitializationType.OpenAIClientInServiceProvider)]
    public void KernelBuilderAddOpenAIChatCompletionAddsValidService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient(new ApiKeyCredential("key"));
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        builder = type switch
        {
            InitializationType.ApiKey => builder.AddOpenAIChatCompletion("model-id", "api-key"),
            InitializationType.OpenAIClientInline => builder.AddOpenAIChatCompletion("model-id", client),
            InitializationType.OpenAIClientInServiceProvider => builder.AddOpenAIChatCompletion("model-id"),
            _ => builder
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService is OpenAIChatCompletionService);

        var textGenerationService = builder.Build().GetRequiredService<ITextGenerationService>();
        Assert.True(textGenerationService is OpenAIChatCompletionService);
    }

    #endregion

    public enum InitializationType
    {
        ApiKey,
        OpenAIClientInline,
        OpenAIClientInServiceProvider,
        OpenAIClientEndpoint,
    }
}
