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
    public void ItFailsWhenAddingTextCompletionServicesWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletionService("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAITextCompletionService("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidServiceConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItFailsWhenAddingEmbeddingGenerationServicesWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAIEmbeddingGenerationService("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAIEmbeddingGenerationService("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidServiceConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletionService("azure", "depl", "https://url", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("azure", "depl2", "https://url", "key");

        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletionService("azure", "depl", "https://url", "key");
        target.AddOpenAITextCompletionService("oai", "model", "apikey");
        target.AddAzureOpenAIEmbeddingGenerationService("azure", "depl2", "https://url2", "key");
        target.AddOpenAIEmbeddingGenerationService("oai2", "model2", "apikey2");

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
        target.AddAzureOpenAITextCompletionService("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAITextCompletionService("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAITextCompletionService("one", "model", "key", overwrite: true);
        target.AddOpenAITextCompletionService("one", "model", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingGenerationService("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingGenerationService("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAIEmbeddingGenerationService("one", "model", "key", overwrite: true);
        target.AddOpenAIEmbeddingGenerationService("one", "model", "key", overwrite: true);
    }

    [Fact]
    public void ItCanRemoveAllServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAIEmbeddingGenerationService("8", "model", "key");

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
        target.AddAzureOpenAITextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAIEmbeddingGenerationService("8", "model", "key");

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
        target.AddAzureOpenAITextCompletionService("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletionService("3", "model", "key");
        target.AddOpenAITextCompletionService("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGenerationService("7", "model", "key");
        target.AddOpenAIEmbeddingGenerationService("8", "model", "key");

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
        target.AddAzureOpenAITextCompletionService("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
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
        target.AddAzureOpenAIEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("2", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGenerationService("3", "model", "key");
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
        target.AddOpenAIEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("2", "dep", "https://localhost", "key");
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
        target.AddOpenAIEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("2", "dep", "https://localhost", "key");
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
        target.AddOpenAIEmbeddingGenerationService("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGenerationService("2", "dep", "https://localhost", "key");
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
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
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
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
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
        target.AddAzureOpenAITextCompletionService("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault();

        // Assert
        Assert.Equal("2", result);
    }
}
