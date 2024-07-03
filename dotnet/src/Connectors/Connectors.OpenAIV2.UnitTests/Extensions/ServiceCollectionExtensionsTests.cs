// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AudioToText;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TextToAudio;
using Microsoft.SemanticKernel.TextToImage;
using OpenAI;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Extensions;

public class ServiceCollectionExtensionsTests
{
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
        var service = sut.AddOpenAITextToImage("model", "key")
            .BuildServiceProvider()
            .GetRequiredService<ITextToImageService>();

        // Assert
        Assert.Equal("model", service.Attributes[AIServiceExtensions.ModelIdKey]);
    }

    [Fact]
    public void ItCanAddImageToTextServiceWithOpenAIClient()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextToImage("model", new OpenAIClient("key"))
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
    public void ItCanAddTextToAudioServiceWithOpenAIClient()
    {
        // Arrange
        var sut = new ServiceCollection();

        // Act
        var service = sut.AddOpenAITextToAudio("model", new OpenAIClient("key"))
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
}
