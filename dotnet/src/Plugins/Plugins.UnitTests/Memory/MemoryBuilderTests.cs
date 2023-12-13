// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Memory;

/// <summary>
/// Unit tests for <see cref="MemoryBuilder"/> class.
/// </summary>
public sealed class MemoryBuilderTests
{
    [Fact]
    public void ItThrowsExceptionWhenMemoryStoreIsNotProvided()
    {
        // Arrange
        var builder = new MemoryBuilder();

        // Act
        var exception = Assert.Throws<KernelException>(() => builder.Build());

        // Assert
        Assert.Equal("IMemoryStore dependency was not provided. Use WithMemoryStore method.", exception.Message);
    }

    [Fact]
    public void ItThrowsExceptionWhenEmbeddingGenerationIsNotProvided()
    {
        // Arrange
        var builder = new MemoryBuilder()
            .WithMemoryStore(Mock.Of<IMemoryStore>());

        // Act
        var exception = Assert.Throws<KernelException>(() => builder.Build());

        // Assert
        Assert.Equal("ITextEmbeddingGenerationService dependency was not provided. Use WithTextEmbeddingGeneration method.", exception.Message);
    }

    [Fact]
    public void ItInitializesMemoryWhenRequiredDependenciesAreProvided()
    {
        // Arrange
        var builder = new MemoryBuilder()
            .WithMemoryStore(Mock.Of<IMemoryStore>())
            .WithTextEmbeddingGeneration(Mock.Of<ITextEmbeddingGenerationService>());

        // Act
        var memory = builder.Build();

        // Assert
        Assert.NotNull(memory);
    }

    [Fact]
    public void ItUsesProvidedLoggerFactory()
    {
        // Arrange
        var loggerFactoryUsed = Mock.Of<ILoggerFactory>();
        var loggerFactoryUnused = Mock.Of<ILoggerFactory>();

        // Act & Assert
        var builder = new MemoryBuilder()
            .WithLoggerFactory(loggerFactoryUsed)
            .WithMemoryStore((loggerFactory) =>
            {
                Assert.Same(loggerFactoryUsed, loggerFactory);
                Assert.NotSame(loggerFactoryUnused, loggerFactory);

                return Mock.Of<IMemoryStore>();
            })
            .WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            {
                Assert.Same(loggerFactoryUsed, loggerFactory);
                Assert.NotSame(loggerFactoryUnused, loggerFactory);

                return Mock.Of<ITextEmbeddingGenerationService>();
            })
            .Build();
    }

    [Fact]
    public void ItUsesProvidedHttpClientFactory()
    {
        // Arrange
        using var httpClientUsed = new HttpClient();
        using var httpClientUnused = new HttpClient();

        // Act & Assert
        var builder = new MemoryBuilder()
            .WithHttpClient(httpClientUsed)
            .WithMemoryStore((loggerFactory, httpClient) =>
            {
                Assert.Same(httpClientUsed, httpClient);
                Assert.NotSame(httpClientUnused, httpClient);

                return Mock.Of<IMemoryStore>();
            })
            .WithTextEmbeddingGeneration((loggerFactory, httpClient) =>
            {
                Assert.Same(httpClientUsed, httpClient);
                Assert.NotSame(httpClientUnused, httpClient);

                return Mock.Of<ITextEmbeddingGenerationService>();
            })
            .Build();
    }
}
