// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel;
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

        Assert.Contains("azure", target.GetTextCompletionServiceIds());
        Assert.Contains("azure", target.GetTextEmbeddingServiceIds());
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
        var completionServices = target.GetTextCompletionServiceIds();
        Assert.Contains("azure", completionServices);
        Assert.Contains("oai", completionServices);
        Assert.DoesNotContain("azure2", completionServices);
        Assert.DoesNotContain("oai2", completionServices);

        var embeddingServices = target.GetTextEmbeddingServiceIds();
        Assert.Contains("azure", embeddingServices);
        Assert.Contains("oai2", embeddingServices);
        Assert.DoesNotContain("azure1", embeddingServices);
        Assert.DoesNotContain("oai", embeddingServices);
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
        target.RemoveAllTextEmbeddingServices();

        // Assert
        Assert.Empty(target.GetTextEmbeddingServiceIds());
        Assert.Empty(target.GetTextCompletionServiceIds());
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
        Assert.Equal(4, target.GetTextEmbeddingServiceIds().Count());
        Assert.Empty(target.GetTextCompletionServiceIds());
    }

    [Fact]
    public void ItCanRemoveAllTextEmbeddingServices()
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
        target.RemoveAllTextEmbeddingServices();

        // Assert
        Assert.Equal(4, target.GetTextCompletionServiceIds().Count());
        Assert.Empty(target.GetTextEmbeddingServiceIds());
    }

    [Fact]
    public void ItCanRemoveOneCompletionService()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextCompletionService("1", "dep", "https://localhost", "key");
        target.AddAzureTextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        Assert.Equal("1", target.GetDefaultTextCompletionServiceId());

        // Act - Assert
        Assert.True(target.TryRemoveTextCompletionService("1"));
        Assert.Equal("2", target.GetDefaultTextCompletionServiceId());
        Assert.True(target.TryRemoveTextCompletionService("2"));
        Assert.Equal("3", target.GetDefaultTextCompletionServiceId());
        Assert.True(target.TryRemoveTextCompletionService("3"));
        Assert.Null(target.GetDefaultTextCompletionServiceId());
    }

    [Fact]
    public void ItCanRemoveOneTextEmbeddingService()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureTextEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureTextEmbeddingGenerationService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextEmbeddingGenerationService("3", "model", "key");
        Assert.Equal("1", target.GetDefaultTextEmbeddingServiceId());

        // Act - Assert
        Assert.True(target.TryRemoveTextEmbeddingService("1"));
        Assert.Equal("2", target.GetDefaultTextEmbeddingServiceId());
        Assert.True(target.TryRemoveTextEmbeddingService("2"));
        Assert.Equal("3", target.GetDefaultTextEmbeddingServiceId());
        Assert.True(target.TryRemoveTextEmbeddingService("3"));
        Assert.Null(target.GetDefaultTextEmbeddingServiceId());
    }
}
