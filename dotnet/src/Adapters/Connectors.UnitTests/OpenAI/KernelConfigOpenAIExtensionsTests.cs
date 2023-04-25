// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="KernelConfigOpenAIExtensions"/>.
/// </summary>
public class KernelConfigOpenAIExtensionsTests
{
    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("azure", "depl", "https://url", "key");
        target.AddAzureTextEmbeddingGenerationService("azure", "depl2", "https://url", "key");

        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("azure", "depl", "https://url", "key");
        target.AddOpenAITextCompletionService("oai", "model", "apikey");
        target.AddAzureTextEmbeddingGenerationService("azure", "depl2", "https://url2", "key");
        target.AddOpenAITextEmbeddingGenerationService("oai2", "model2", "apikey2");

        // Assert
        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextCompletionServices.ContainsKey("oai"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("oai2"));

        Assert.False(target.TextCompletionServices.ContainsKey("azure2"));
        Assert.False(target.TextCompletionServices.ContainsKey("oai2"));
        Assert.False(target.TextEmbeddingGenerationServices.ContainsKey("azure1"));
        Assert.False(target.TextEmbeddingGenerationServices.ContainsKey("oai"));
    }

    [Fact]
    public void ItCanOverwriteServices()
    {
        // Arrange
        var target = new KernelConfig();

        // Act - Assert no exception occurs
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("one", "model", "key");
        target.AddOpenAITextCompletionService("one", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("one", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("one", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("one", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("one", "model", "key");
    }

    [Fact]
    public void ItCanRemoveAllServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Empty(target.AllTextEmbeddingGenerationServiceIds);
        Assert.Empty(target.AllTextCompletionServiceIds);
    }

    [Fact]
    public void ItCanRemoveAllTextCompletionServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();

        // Assert
        Assert.Equal(4, target.AllTextEmbeddingGenerationServiceIds.Count());
        Assert.Empty(target.AllTextCompletionServiceIds);
    }

    [Fact]
    public void ItCanRemoveAllTextEmbeddingGenerationServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureTextEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAITextEmbeddingGenerationService("8", "model", "key");

        // Act
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Equal(4, target.AllTextCompletionServiceIds.Count());
        Assert.Empty(target.AllTextEmbeddingGenerationServiceIds);
    }

    [Fact]
    public void ItCanRemoveOneCompletionService()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("1", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        Assert.Equal("1", target.DefaultTextCompletionServiceId);

        // Act - Assert
        target.RemoveTextCompletionService("1");
        Assert.Equal("2", target.DefaultTextCompletionServiceId);
        target.RemoveTextCompletionService("2");
        Assert.Equal("3", target.DefaultTextCompletionServiceId);
        target.RemoveTextCompletionService("3");
        Assert.Null(target.DefaultTextCompletionServiceId);
    }

    [Fact]
    public void ItCanRemoveOneTextEmbeddingGenerationService()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("3", "model", "key");
        Assert.Equal("1", target.DefaultTextEmbeddingGenerationServiceId);

        // Act - Assert
        target.RemoveTextEmbeddingGenerationService("1");
        Assert.Equal("2", target.DefaultTextEmbeddingGenerationServiceId);
        target.RemoveTextEmbeddingGenerationService("2");
        Assert.Equal("3", target.DefaultTextEmbeddingGenerationServiceId);
        target.RemoveTextEmbeddingGenerationService("3");
        Assert.Null(target.DefaultTextEmbeddingGenerationServiceId);
    }

    [Fact]
    public void GetTextEmbeddingGenerationServiceItReturnsDefaultWhenNonExistingIdIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddOpenAITextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextEmbeddingGenerationService("2");

        // Act
        var result = target.GetTextEmbeddingGenerationServiceIdOrDefault("test");

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void GetEmbeddingServiceReturnsSpecificWhenExistingIdIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAITextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextEmbeddingGenerationService("2");

        // Act
        var result = target.GetTextEmbeddingGenerationServiceIdOrDefault("1");

        // Assert
        Assert.Equal("1", result);
    }

    [Fact]
    public void GetEmbeddingServiceReturnsDefaultWhenNoIdIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAITextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextEmbeddingGenerationService("2");

        // Act
        var result = target.GetTextEmbeddingGenerationServiceIdOrDefault();

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void GetTextCompletionServiceReturnsDefaultWhenNonExistingIdIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAITextCompletionService("1", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault("345");

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void GetTextCompletionServiceReturnsSpecificWhenExistingIdIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAITextCompletionService("1", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault("1");

        // Assert
        Assert.Equal("1", result);
    }

    [Fact]
    public void GetTextCompletionServiceItReturnsDefaultWhenNoIdIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAITextCompletionService("1", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault();

        // Assert
        Assert.Equal("2", result);
    }
}
