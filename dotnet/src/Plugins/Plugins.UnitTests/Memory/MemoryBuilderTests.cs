// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
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
        var exception = Assert.Throws<SKException>(() => builder.Build());

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
        var exception = Assert.Throws<SKException>(() => builder.Build());

        // Assert
        Assert.Equal("ITextEmbeddingGeneration dependency was not provided. Use WithTextEmbeddingGeneration method.", exception.Message);
    }

    [Fact]
    public void ItInitializesMemoryWhenRequiredDependenciesAreProvided()
    {
        // Arrange
        var builder = new MemoryBuilder()
            .WithMemoryStore(Mock.Of<IMemoryStore>())
            .WithTextEmbeddingGeneration(Mock.Of<ITextEmbeddingGeneration>());

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
            .WithTextEmbeddingGeneration((loggerFactory, httpHandlerFactory) =>
            {
                Assert.Same(loggerFactoryUsed, loggerFactory);
                Assert.NotSame(loggerFactoryUnused, loggerFactory);

                return Mock.Of<ITextEmbeddingGeneration>();
            })
            .Build();
    }

    [Fact]
    public void ItUsesProvidedHttpHandlerFactory()
    {
        // Arrange
        var httpHandlerFactoryUsed = Mock.Of<IDelegatingHandlerFactory>();
        var httpHandlerFactoryUnused = Mock.Of<IDelegatingHandlerFactory>();

        // Act & Assert
        var builder = new MemoryBuilder()
            .WithHttpHandlerFactory(httpHandlerFactoryUsed)
            .WithMemoryStore((loggerFactory, httpHandlerFactory) =>
            {
                Assert.Same(httpHandlerFactoryUsed, httpHandlerFactory);
                Assert.NotSame(httpHandlerFactoryUnused, httpHandlerFactory);

                return Mock.Of<IMemoryStore>();
            })
            .WithTextEmbeddingGeneration((loggerFactory, httpHandlerFactory) =>
            {
                Assert.Same(httpHandlerFactoryUsed, httpHandlerFactory);
                Assert.NotSame(httpHandlerFactoryUnused, httpHandlerFactory);

                return Mock.Of<ITextEmbeddingGeneration>();
            })
            .Build();
    }
}
