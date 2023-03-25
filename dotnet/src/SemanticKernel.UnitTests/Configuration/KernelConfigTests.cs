// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Reliability;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Configuration;

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
    public void HttpRetryHandlerFactoryIsSet()
    {
        // Arrange
        var retry = new NullHttpRetryHandlerFactory();
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(retry);

        // Assert
        Assert.Equal(retry, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetWithCustomImplementation()
    {
        // Arrange
        var retry = new Mock<IDelegatingHandlerFactory>();
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(retry.Object);

        // Assert
        Assert.Equal(retry.Object, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetToDefaultHttpRetryHandlerFactoryIfNull()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(null);

        // Assert
        Assert.IsType<DefaultHttpRetryHandlerFactory>(config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetToDefaultHttpRetryHandlerFactoryIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        // Assert
        Assert.IsType<DefaultHttpRetryHandlerFactory>(config.HttpHandlerFactory);
    }

    [Fact]
    public void ItFailsWhenAddingCompletionBackendsWithSameLabel()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("azure", "depl", "https://url", "key");

        var exception = Assert.Throws<KernelException>(() =>
        {
            target.AddAzureOpenAICompletion("azure", "depl2", "https://url", "key");
        });
        Assert.Equal(KernelException.ErrorCodes.InvalidServiceConfiguration, exception.ErrorCode);
    }

    [Fact]
    public void ItFailsWhenAddingEmbeddingsBackendsWithSameLabel()
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
    public void ItSucceedsWhenAddingDifferentBackendTypeWithSameLabel()
    {
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("azure", "depl", "https://url", "key");
        target.AddAzureOpenAIEmbeddingGeneration("azure", "depl2", "https://url", "key");

        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingServices.ContainsKey("azure"));
    }

    [Fact]
    public void ItFailsWhenSetNonExistentCompletionBackend()
    {
        var target = new KernelConfig();
        var exception = Assert.Throws<KernelException>(() =>
        {
            target.SetDefaultTextCompletionService("azure");
        });
        Assert.Equal(KernelException.ErrorCodes.ServiceNotFound, exception.ErrorCode);
    }

    [Fact]
    public void ItFailsWhenSetNonExistentEmbeddingBackend()
    {
        var target = new KernelConfig();
        var exception = Assert.Throws<KernelException>(() =>
        {
            target.SetDefaultEmbeddingService("azure");
        });
        Assert.Equal(KernelException.ErrorCodes.ServiceNotFound, exception.ErrorCode);
    }

    [Fact]
    public void ItTellsIfABackendIsAvailable()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("azure", "depl", "https://url", "key");
        target.AddOpenAICompletion("oai", "model", "apikey");
        target.AddAzureOpenAIEmbeddingGeneration("azure", "depl2", "https://url2", "key");
        target.AddOpenAIEmbeddingGeneration("oai2", "model2", "apikey2");

        // Assert
        Assert.True(target.TextCompletionServices.ContainsKey("azure"));
        Assert.True(target.TextCompletionServices.ContainsKey("oai"));
        Assert.True(target.TextEmbeddingServices.ContainsKey("azure"));
        Assert.True(target.TextEmbeddingServices.ContainsKey("oai2"));

        Assert.False(target.TextCompletionServices.ContainsKey("azure2"));
        Assert.False(target.TextCompletionServices.ContainsKey("oai2"));
        Assert.False(target.TextEmbeddingServices.ContainsKey("azure1"));
        Assert.False(target.TextEmbeddingServices.ContainsKey("oai"));
    }

    [Fact]
    public void ItCanOverwriteBackends()
    {
        // Arrange
        var target = new KernelConfig();

        // Act - Assert no exception occurs
        target.AddAzureOpenAICompletion("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAICompletion("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAICompletion("one", "model", "key", overwrite: true);
        target.AddOpenAICompletion("one", "model", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingGeneration("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddAzureOpenAIEmbeddingGeneration("one", "dep", "https://localhost", "key", overwrite: true);
        target.AddOpenAIEmbeddingGeneration("one", "model", "key", overwrite: true);
        target.AddOpenAIEmbeddingGeneration("one", "model", "key", overwrite: true);
    }

    [Fact]
    public void ItCanRemoveAllBackends()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletion("3", "model", "key");
        target.AddOpenAICompletion("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGeneration("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("7", "model", "key");
        target.AddOpenAIEmbeddingGeneration("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();
        target.RemoveAllTextEmbeddingServices();

        // Assert
        Assert.Empty(target.AllTextEmbeddingServices);
        Assert.Empty(target.AllTextCompletionServices);
    }

    [Fact]
    public void ItCanRemoveAllCompletionBackends()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletion("3", "model", "key");
        target.AddOpenAICompletion("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGeneration("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("7", "model", "key");
        target.AddOpenAIEmbeddingGeneration("8", "model", "key");

        // Act
        target.RemoveAllTextCompletionServices();

        // Assert
        Assert.Equal(4, target.AllTextEmbeddingServices.Count());
        Assert.Empty(target.AllTextCompletionServices);
    }

    [Fact]
    public void ItCanRemoveAllEmbeddingsBackends()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("one", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletion("3", "model", "key");
        target.AddOpenAICompletion("4", "model", "key");
        target.AddAzureOpenAIEmbeddingGeneration("5", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("6", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("7", "model", "key");
        target.AddOpenAIEmbeddingGeneration("8", "model", "key");

        // Act
        target.RemoveAllTextEmbeddingServices();

        // Assert
        Assert.Equal(4, target.AllTextCompletionServices.Count());
        Assert.Empty(target.AllTextEmbeddingServices);
    }

    [Fact]
    public void ItCanRemoveOneCompletionBackend()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAICompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.AddOpenAICompletion("3", "model", "key");
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
    public void ItCanRemoveOneEmbeddingsBackend()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddAzureOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.AddOpenAIEmbeddingGeneration("3", "model", "key");
        Assert.Equal("1", target.DefaultTextEmbeddingServiceId);

        // Act - Assert
        target.RemoveTextEmbeddingService("1");
        Assert.Equal("2", target.DefaultTextEmbeddingServiceId);
        target.RemoveTextEmbeddingService("2");
        Assert.Equal("3", target.DefaultTextEmbeddingServiceId);
        target.RemoveTextEmbeddingService("3");
        Assert.Null(target.DefaultTextEmbeddingServiceId);
    }

    [Fact]
    public void GetEmbeddingsBackendItReturnsDefaultWhenNonExistingLabelIsProvided()
    {
        // Arrange
        var target = new KernelConfig();
        target.AddOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.SetDefaultEmbeddingService("2");

        // Act
        var result = target.GetTextEmbeddingServiceIdOrDefault("test");

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void GetEmbeddingsBackendReturnsSpecificWhenExistingLabelIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.SetDefaultEmbeddingService("2");

        // Act
        var result = target.GetTextEmbeddingServiceIdOrDefault("1");

        // Assert
        Assert.Equal("1", result);
    }

    [Fact]
    public void GetEmbeddingsBackendReturnsDefaultWhenNoLabelIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAIEmbeddingGeneration("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAIEmbeddingGeneration("2", "dep", "https://localhost", "key");
        target.SetDefaultEmbeddingService("2");

        // Act
        var result = target.GetTextEmbeddingServiceIdOrDefault();

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void GetCompletionBackendReturnsDefaultWhenNonExistingLabelIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAICompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault("345");

        // Assert
        Assert.Equal("2", result);
    }

    [Fact]
    public void GetCompletionBackendReturnsSpecificWhenExistingLabelIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAICompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault("1");

        // Assert
        Assert.Equal("1", result);
    }

    [Fact]
    public void GetCompletionBackendItReturnsDefaultWhenNoLabelIsProvided()
    {
        // Arrange
        var kernel = new Mock<IKernel>();
        var target = new KernelConfig();
        target.AddOpenAICompletion("1", "dep", "https://localhost", "key");
        target.AddAzureOpenAICompletion("2", "dep", "https://localhost", "key");
        target.SetDefaultTextCompletionService("2");

        // Act
        var result = target.GetTextCompletionServiceIdOrDefault();

        // Assert
        Assert.Equal("2", result);
    }
}
