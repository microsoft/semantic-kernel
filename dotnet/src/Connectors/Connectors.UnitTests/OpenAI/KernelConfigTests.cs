// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// Unit tests of <see cref="KernelConfig"/>.
/// </summary>
public class KernelConfigTests
{
    private readonly Mock<IKernel> _kernel;

    public KernelConfigTests()
    {
        var kernelConfig = new KernelConfig();
        this._kernel = new Mock<IKernel>();
        this._kernel.SetupGet(x => x.Log).Returns(NullLogger.Instance);
        this._kernel.SetupGet(x => x.Config).Returns(kernelConfig);
    }

    [Fact]
    public void ItFailsWhenAddingTextCompletionServicesWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAITextCompletion("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidServiceConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItFailsWhenAddingEmbeddingGenerationServicesWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAIEmbeddingGeneration("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAIEmbeddingGeneration("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidServiceConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItSucceedsWhenAddingDifferentServiceTypeWithSameId()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("azure", "depl", "https://url", "key");
        target.AddAzureOpenAIEmbeddingGeneration("azure", "depl2", "https://url", "key");

        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingGenerationServices.ContainsKey("azure"));
    }

    [Fact]
    public void ItTellsIfAServiceIsAvailable()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("azure", "depl", "https://url", "key");
        target.AddOpenAITextCompletion("oai", "model", "apikey");
        target.AddAzureOpenAIEmbeddingGeneration("azure", "depl2", "https://url2", "key");
        target.AddOpenAIEmbeddingGeneration("oai2", "model2", "apikey2");

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
        target.AddAzureOpenAITextCompletion("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAITextCompletion("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAITextCompletion("one", "model", "key", overwrite: true);
        target.AddOpenAITextCompletion("one", "model", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingGeneration("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingGeneration("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAIEmbeddingGeneration("one", "model", "key", overwrite: true);
        target.AddOpenAIEmbeddingGeneration("one", "model", "key", overwrite: true);
    }

    [Fact]
    public void ItCanRemoveAllServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletion("3", "model", "key");
        target.AddOpenAITextCompletion("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGeneration("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("7", "model", "key");
        target.AddOpenAIEmbeddingGeneration("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Empty(target.AllTextEmbeddingGenerationServices);
        Assert.Empty(target.AllTextCompletionServices);
    }

    [Fact]
    public void ItCanRemoveAllTextCompletionServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletion("3", "model", "key");
        target.AddOpenAITextCompletion("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGeneration("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("7", "model", "key");
        target.AddOpenAIEmbeddingGeneration("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();

        // Assert
        Assert.Equal(4, target.AllTextEmbeddingGenerationServices.Count());
        Assert.Empty(target.AllTextCompletionServices);
    }

    [Fact]
    public void ItCanRemoveAllTextEmbeddingGenerationServices()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletion("3", "model", "key");
        target.AddOpenAITextCompletion("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGeneration("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("7", "model", "key");
        target.AddOpenAIEmbeddingGeneration("8", "model", "key");

        // Act
        target.RemoveAllTextEmbeddingGenerationServices();

        // Assert
        Assert.Equal(4, target.AllTextCompletionServices.Count());
        Assert.Empty(target.AllTextEmbeddingGenerationServices);
    }

    [Fact]
    public void ItCanRemoveOneCompletionService()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAITextCompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAITextCompletion("3", "model", "key");
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
        target.AddAzureOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("3", "model", "key");
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
        target.AddOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.SetDefaultTextEmbeddingGeneration("2");

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
        target.AddOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.SetDefaultTextEmbeddingGeneration("2");

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
        target.AddOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.SetDefaultTextEmbeddingGeneration("2");

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
        target.AddOpenAITextCompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletion("2");

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
        target.AddOpenAITextCompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletion("2");

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
        target.AddOpenAITextCompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAITextCompletion("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletion("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault();

        // Assert
        Assert.Equal("2", result);
    }
}
