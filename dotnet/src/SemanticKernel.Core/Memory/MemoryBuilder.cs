// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A builder for Memory plugin.
/// </summary>
[Experimental("SKEXP0001")]
[ExcludeFromCodeCoverage]
public sealed class MemoryBuilder
{
    private Func<IMemoryStore>? _memoryStoreFactory = null;
    private Func<ITextEmbeddingGenerationService>? _embeddingGenerationFactory = null;
    private HttpClient? _httpClient;
    private ILoggerFactory _loggerFactory = NullLoggerFactory.Instance;

    /// <summary>
    /// Build a new instance of <see cref="ISemanticTextMemory"/> using the settings passed so far.
    /// </summary>
    /// <returns>Instance of <see cref="ISemanticTextMemory"/>.</returns>
    public ISemanticTextMemory Build()
    {
        var memoryStore = this._memoryStoreFactory?.Invoke() ??
            throw new KernelException($"{nameof(IMemoryStore)} dependency was not provided. Use {nameof(WithMemoryStore)} method.");

        var embeddingGeneration = this._embeddingGenerationFactory?.Invoke() ??
            throw new KernelException($"{nameof(ITextEmbeddingGenerationService)} dependency was not provided. Use {nameof(WithTextEmbeddingGeneration)} method.");

        return new SemanticTextMemory(memoryStore, embeddingGeneration);
    }

    /// <summary>
    /// Add a logger factory.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>Updated Memory builder including the logger factory.</returns>
    public MemoryBuilder WithLoggerFactory(ILoggerFactory loggerFactory)
    {
        Verify.NotNull(loggerFactory);
        this._loggerFactory = loggerFactory;
        return this;
    }

    /// <summary>
    /// Add an HttpClient.
    /// </summary>
    /// <param name="httpClient"><see cref="HttpClient"/> to add.</param>
    /// <returns>Updated Memory builder including the client.</returns>
    public MemoryBuilder WithHttpClient(HttpClient httpClient)
    {
        Verify.NotNull(httpClient);
        this._httpClient = httpClient;
        return this;
    }

    /// <summary>
    /// Add memory store.
    /// </summary>
    /// <param name="store">Store to add.</param>
    /// <returns>Updated Memory builder including the memory store.</returns>
    public MemoryBuilder WithMemoryStore(IMemoryStore store)
    {
        Verify.NotNull(store);
        this._memoryStoreFactory = () => store;
        return this;
    }

    /// <summary>
    /// Add memory store factory.
    /// </summary>
    /// <param name="factory">The store factory.</param>
    /// <returns>Updated Memory builder including the memory store.</returns>
    public MemoryBuilder WithMemoryStore<TStore>(Func<ILoggerFactory, TStore> factory) where TStore : IMemoryStore
    {
        Verify.NotNull(factory);
        this._memoryStoreFactory = () => factory(this._loggerFactory);
        return this;
    }

    /// <summary>
    /// Add memory store factory.
    /// </summary>
    /// <param name="factory">The store factory.</param>
    /// <returns>Updated Memory builder including the memory store.</returns>
    public MemoryBuilder WithMemoryStore<TStore>(Func<ILoggerFactory, HttpClient?, TStore> factory) where TStore : IMemoryStore
    {
        Verify.NotNull(factory);
        this._memoryStoreFactory = () => factory(this._loggerFactory, this._httpClient);
        return this;
    }

    /// <summary>
    /// Add text embedding generation.
    /// </summary>
    /// <param name="textEmbeddingGeneration">The text embedding generation.</param>
    /// <returns>Updated Memory builder including the text embedding generation.</returns>
    public MemoryBuilder WithTextEmbeddingGeneration(ITextEmbeddingGenerationService textEmbeddingGeneration)
    {
        Verify.NotNull(textEmbeddingGeneration);
        this._embeddingGenerationFactory = () => textEmbeddingGeneration;
        return this;
    }

    /// <summary>
    /// Add text embedding generation.
    /// </summary>
    /// <param name="factory">The text embedding generation factory.</param>
    /// <returns>Updated Memory builder including the text embedding generation.</returns>
    public MemoryBuilder WithTextEmbeddingGeneration<TEmbeddingGeneration>(
        Func<ILoggerFactory, HttpClient?, TEmbeddingGeneration> factory) where TEmbeddingGeneration : ITextEmbeddingGenerationService
    {
        Verify.NotNull(factory);
        this._embeddingGenerationFactory = () => factory(this._loggerFactory, this._httpClient);
        return this;
    }
}
