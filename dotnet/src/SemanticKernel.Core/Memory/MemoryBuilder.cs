// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A builder for Memory plugin.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class MemoryBuilder
{
    /// <summary>The collection of services to be available through the <see cref="Kernel"/>.</summary>
    private IServiceCollection? _services;

    /// <summary>Gets the collection of services to be built into the <see cref="Kernel"/>.</summary>
    public IServiceCollection Services => this._services ??= new ServiceCollection();

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryBuilder"/> class.
    /// </summary>
    public MemoryBuilder()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryBuilder"/> class with the specified services.
    /// </summary>
    /// <param name="services">The collection of services.</param>
    public MemoryBuilder(IServiceCollection services)
    {
        Verify.NotNull(services);

        this._services = services;
    }

    /// <summary>
    /// Build a new instance of <see cref="ISemanticTextMemory"/> using the settings passed so far.
    /// </summary>
    /// <returns>Instance of <see cref="ISemanticTextMemory"/>.</returns>
    public ISemanticTextMemory Build()
    {
        var serviceProvider = this.Services.BuildServiceProvider();

        var memoryStore = serviceProvider.GetService<IMemoryStore>() ??
            throw new KernelException($"{nameof(IMemoryStore)} dependency was not provided. Use {nameof(WithMemoryStore)} method.");

        var embeddingGeneration = serviceProvider.GetService<ITextEmbeddingGenerationService>() ??
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
        this.Services.AddSingleton(loggerFactory);
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
        this.Services.AddSingleton(httpClient);
        return this;
    }

    /// <summary>
    /// Add memory store.
    /// </summary>
    /// <param name="store">Store to add.</param>
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including the memory store.</returns>
    public MemoryBuilder WithMemoryStore(IMemoryStore store, string? serviceId = null)
    {
        Verify.NotNull(store);
        this.Services.AddKeyedSingleton(serviceId, store);
        return this;
    }

    /// <summary>
    /// Add text embedding generation.
    /// </summary>
    /// <param name="textEmbeddingGeneration">The text embedding generation.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>Updated Memory builder including the text embedding generation.</returns>
    public MemoryBuilder WithTextEmbeddingGeneration(ITextEmbeddingGenerationService textEmbeddingGeneration, string? serviceId = null)
    {
        Verify.NotNull(textEmbeddingGeneration);
        this.Services.AddKeyedSingleton(serviceId, textEmbeddingGeneration);
        return this;
    }
}
