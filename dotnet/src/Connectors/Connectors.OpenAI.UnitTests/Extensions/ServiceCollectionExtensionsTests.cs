﻿// Copyright (c) Microsoft. All rights reserved.

using System;
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

public class ServiceCollectionExtensionsTests
{
    #region Chat completion

    [Theory]
    [InlineData(InitializationType.ApiKey)]
    [InlineData(InitializationType.ClientInline)]
    [InlineData(InitializationType.ClientInServiceProvider)]
    public void ItCanAddChatCompletionService(InitializationType type)
    {
        // Arrange
        var client = new OpenAIClient("key");
        var builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(client);

        // Act
        IServiceCollection collection = type switch
        {
            InitializationType.ApiKey => builder.Services.AddOpenAIChatCompletion("deployment-name", "https://endpoint", "api-key"),
            InitializationType.ClientInline => builder.Services.AddOpenAIChatCompletion("deployment-name", client),
            InitializationType.ClientInServiceProvider => builder.Services.AddOpenAIChatCompletion("deployment-name"),
            _ => builder.Services
        };

        // Assert
        var chatCompletionService = builder.Build().GetRequiredService<IChatCompletionService>();
        Assert.True(chatCompletionService is OpenAIChatCompletionService);

        var textGenerationService = builder.Build().GetRequiredService<ITextGenerationService>();
        Assert.True(textGenerationService is OpenAIChatCompletionService);
    }

    #endregion

    [Fact]
    public void ItCanAddTextEmbeddingGenerationService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextEmbeddingGeneration("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddTextEmbeddingGenerationServiceWithOpenAIClient()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextEmbeddingGeneration("model", new OpenAIClient("key"))
            .BuildServiceProvider()
            .GetRequiredService<ITextEmbeddingGenerationService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddImageToTextService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextToImage("key", modelId: "model")
            .BuildServiceProvider()
            .GetRequiredService<ITextToImageService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddTextToAudioService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextToAudio("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<ITextToAudioService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddAudioToTextService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAIAudioToText("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<IAudioToTextService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddAudioToTextServiceWithOpenAIClient()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAIAudioToText("model", new OpenAIClient("key"))
            .BuildServiceProvider()
            .GetRequiredService<IAudioToTextService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    [Obsolete("This test is deprecated and will be removed in a future version.")]
    public void ItCanAddFileService()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAIFiles("key")
            .BuildServiceProvider()
            .GetRequiredService<OpenAIFileService>();
    }

    public enum InitializationType
    {
        ApiKey,
        ClientInline,
        ClientInServiceProvider,
        ClientEndpoint,
    }
}
