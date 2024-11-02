﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Embeddings;

/// <summary>
/// Provides a collection of static methods for operating on <see cref="IEmbeddingGenerationService{TValue,TEmbedding}"/> objects.
/// </summary>
[Experimental("SKEXP0001")]
public static class EmbeddingGenerationExtensions
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="value"/>.
    /// </summary>
    /// <typeparam name="TValue">The type from which embeddings will be generated.</typeparam>
    /// <typeparam name="TEmbedding">The numeric type of the embedding data.</typeparam>
    /// <param name="generator">The embedding generator.</param>
    /// <param name="value">A value from which an embedding will be generated.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>A list of embedding structs representing the input <paramref name="value"/>.</returns>
    public static async Task<ReadOnlyMemory<TEmbedding>> GenerateEmbeddingAsync<TValue, TEmbedding>(
        this IEmbeddingGenerationService<TValue, TEmbedding> generator,
        TValue value,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator);
        return (await generator.GenerateEmbeddingsAsync([value], kernel, cancellationToken).ConfigureAwait(false)).FirstOrDefault();
    }

    /// <summary>Creates an <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> for the specified <see cref="IEmbeddingGenerationService{TValue, TEmbedding}"/>.</summary>
    /// <param name="service">The embedding generation service to be represented as an embedding generator.</param>
    /// <returns>
    /// The <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/>. If the <paramref name="service"/> is an <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/>,
    /// the <paramref name="service"/> will be returned. Otherwise, a new <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> will be created that wraps the <paramref name="service"/>.
    /// </returns>
    public static IEmbeddingGenerator<TValue, Embedding<TEmbedding>> AsEmbeddingGenerator<TValue, TEmbedding>(
        this IEmbeddingGenerationService<TValue, TEmbedding> service)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(service);

        return service is IEmbeddingGenerator<TValue, Embedding<TEmbedding>> embeddingGenerator ?
            embeddingGenerator :
            new EmbeddingGenerationServiceEmbeddingGenerator<TValue, TEmbedding>(service);
    }

    /// <summary>Creates an <see cref="IEmbeddingGenerationService{TInput, TEmbedding}"/> for the specified <see cref="IEmbeddingGenerator{TValue, TEmbedding}"/>.</summary>
    /// <param name="generator">The embedding generator to be represented as an embedding generation service.</param>
    /// <param name="serviceProvider">An optional <see cref="IServiceProvider"/> that can be used to resolve services to use in the instance.</param>
    /// <returns>
    /// The <see cref="IEmbeddingGenerationService{TInput, TEmbedding}"/>. If the <paramref name="generator"/> is an <see cref="IEmbeddingGenerationService{TInput, TEmbedding}"/>,
    /// the <paramref name="generator"/> will be returned. Otherwise, a new <see cref="IEmbeddingGenerationService{TValue, TEmbedding}"/> will be created that wraps the <paramref name="generator"/>.
    /// </returns>
    public static IEmbeddingGenerationService<TValue, TEmbedding> AsEmbeddingGenerationService<TValue, TEmbedding>(
        this IEmbeddingGenerator<TValue, Embedding<TEmbedding>> generator,
        IServiceProvider? serviceProvider = null)
        where TEmbedding : unmanaged
    {
        Verify.NotNull(generator);

        return generator is IEmbeddingGenerationService<TValue, TEmbedding> service ?
            service :
            new EmbeddingGeneratorEmbeddingGenerationService<TValue, TEmbedding>(generator, serviceProvider);
    }

    /// <summary>Provides an implementation of <see cref="IEmbeddingGenerator{TInput, TEmbedding}"/> around an <see cref="IEmbeddingGenerationService{TValue, TEmbedding}"/>.</summary>
    private sealed class EmbeddingGenerationServiceEmbeddingGenerator<TValue, TEmbedding> : IEmbeddingGenerator<TValue, Embedding<TEmbedding>>
        where TEmbedding : unmanaged
    {
        /// <summary>The wrapped <see cref="IEmbeddingGenerationService{TValue, TEmbedding}"/></summary>
        private readonly IEmbeddingGenerationService<TValue, TEmbedding> _service;

        /// <summary>Initializes the <see cref="EmbeddingGenerationServiceEmbeddingGenerator{TValue, TEmbedding}"/> for <paramref name="service"/>.</summary>
        public EmbeddingGenerationServiceEmbeddingGenerator(IEmbeddingGenerationService<TValue, TEmbedding> service)
        {
            this._service = service;
            this.Metadata = new EmbeddingGeneratorMetadata(
                service.GetType().Name,
                service.GetEndpoint() is string endpoint ? new Uri(endpoint) : null,
                service.GetModelId());
        }

        /// <inheritdoc />
        public EmbeddingGeneratorMetadata Metadata { get; }

        /// <inheritdoc />
        public void Dispose()
        {
            (this._service as IDisposable)?.Dispose();
        }

        /// <inheritdoc />
        public async Task<GeneratedEmbeddings<Embedding<TEmbedding>>> GenerateAsync(IEnumerable<TValue> values, EmbeddingGenerationOptions? options = null, CancellationToken cancellationToken = default)
        {
            IList<ReadOnlyMemory<TEmbedding>> result = await this._service.GenerateEmbeddingsAsync(values.ToList(), kernel: null, cancellationToken).ConfigureAwait(false);
            return new(result.Select(e => new Embedding<TEmbedding>(e)));
        }

        /// <inheritdoc />
        public TService? GetService<TService>(object? key = null) where TService : class
        {
            return
                typeof(TService) == typeof(IEmbeddingGenerator<TValue, Embedding<TEmbedding>>) ? (TService)(object)this :
                this._service as TService;
        }
    }

    /// <summary>Provides an implementation of <see cref="IEmbeddingGenerationService{TInput, TEmbedding}"/> around an <see cref="EmbeddingGeneratorEmbeddingGenerationService{TValue, TEmbedding}"/>.</summary>
    private sealed class EmbeddingGeneratorEmbeddingGenerationService<TValue, TEmbedding> : IEmbeddingGenerationService<TValue, TEmbedding>
        where TEmbedding : unmanaged
    {
        /// <summary>The wrapped <see cref="IEmbeddingGenerator{TValue, TEmbedding}"/></summary>
        private readonly IEmbeddingGenerator<TValue, Embedding<TEmbedding>> _generator;

        /// <summary>Initializes the <see cref="EmbeddingGeneratorEmbeddingGenerationService{TValue, TEmbedding}"/> for <paramref name="generator"/>.</summary>
        public EmbeddingGeneratorEmbeddingGenerationService(
            IEmbeddingGenerator<TValue, Embedding<TEmbedding>> generator, IServiceProvider? serviceProvider)
        {
            // Store the generator.
            this._generator = generator;

            // Initialize the attributes.
            var attrs = new Dictionary<string, object?>();
            this.Attributes = new ReadOnlyDictionary<string, object?>(attrs);

            var metadata = generator.Metadata;
            if (metadata.ProviderUri is not null)
            {
                attrs[AIServiceExtensions.EndpointKey] = metadata.ProviderUri.ToString();
            }
            if (metadata.ModelId is not null)
            {
                attrs[AIServiceExtensions.ModelIdKey] = metadata.ModelId;
            }
        }

        /// <inheritdoc />
        public IReadOnlyDictionary<string, object?> Attributes { get; }

        /// <inheritdoc />
        public async Task<IList<ReadOnlyMemory<TEmbedding>>> GenerateEmbeddingsAsync(IList<TValue> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            Verify.NotNull(data);

            var embeddings = await this._generator.GenerateAsync(data, cancellationToken: cancellationToken).ConfigureAwait(false);

            return embeddings.Select(e => e.Vector).ToList();
        }
    }
}
