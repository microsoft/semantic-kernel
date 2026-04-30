// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a supported embedding type for a vector store provider.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
/// <remarks>
/// Each instance encapsulates both build-time embedding type resolution and runtime embedding generation
/// for a specific <see cref="Embedding"/> subtype.
/// </remarks>
[Experimental("MEVD9001")]
public abstract class EmbeddingGenerationDispatcher
{
    /// <summary>
    /// Gets the <see cref="Embedding"/> type that this instance supports.
    /// </summary>
    public abstract Type EmbeddingType { get; }

    /// <summary>
    /// Attempts to resolve the embedding type for the given <paramref name="vectorProperty"/>, using the given <paramref name="embeddingGenerator"/>.
    /// </summary>
    /// <returns>The resolved embedding type, or <see langword="null"/> if the generator does not support this embedding type.</returns>
    public abstract Type? ResolveEmbeddingType(VectorPropertyModel vectorProperty, IEmbeddingGenerator embeddingGenerator, Type? userRequestedEmbeddingType);

    /// <summary>
    /// Generates embeddings of this type from the given <paramref name="values"/>, using the embedding generator configured on the <paramref name="vectorProperty"/>.
    /// </summary>
    public abstract Task<IReadOnlyList<Embedding>> GenerateEmbeddingsAsync(VectorPropertyModel vectorProperty, IEnumerable<object?> values, CancellationToken cancellationToken);

    /// <summary>
    /// Generates a single embedding of this type from the given <paramref name="value"/>, using the embedding generator configured on the <paramref name="vectorProperty"/>.
    /// </summary>
    public abstract Task<Embedding> GenerateEmbeddingAsync(VectorPropertyModel vectorProperty, object? value, CancellationToken cancellationToken);

    /// <summary>
    /// Checks whether the given <paramref name="embeddingGenerator"/> can produce embeddings of this type for any of the input types
    /// supported by the given <paramref name="vectorProperty"/>.
    /// This is used for native vector property types (e.g., <see cref="ReadOnlyMemory{T}"/> of <see langword="float"/>), where embedding generation
    /// is only needed for search and the input type is not known at model-build time.
    /// </summary>
    public abstract bool CanGenerateEmbedding(VectorPropertyModel vectorProperty, IEmbeddingGenerator embeddingGenerator);

    /// <summary>
    /// Creates a new <see cref="EmbeddingGenerationDispatcher"/> for the given <typeparamref name="TEmbedding"/> type.
    /// </summary>
    public static EmbeddingGenerationDispatcher Create<TEmbedding>()
        where TEmbedding : Embedding
        => new EmbeddingGenerationDispatcher<TEmbedding>();
}

/// <summary>
/// A <see cref="EmbeddingGenerationDispatcher"/> implementation for a specific <typeparamref name="TEmbedding"/> type.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public sealed class EmbeddingGenerationDispatcher<TEmbedding> : EmbeddingGenerationDispatcher
    where TEmbedding : Embedding
{
    /// <inheritdoc />
    public override Type EmbeddingType => typeof(TEmbedding);

    /// <inheritdoc />
    public override Type? ResolveEmbeddingType(VectorPropertyModel vectorProperty, IEmbeddingGenerator embeddingGenerator, Type? userRequestedEmbeddingType)
        => vectorProperty.ResolveEmbeddingType<TEmbedding>(embeddingGenerator, userRequestedEmbeddingType);

    /// <inheritdoc />
    public override bool CanGenerateEmbedding(VectorPropertyModel vectorProperty, IEmbeddingGenerator embeddingGenerator)
        => vectorProperty.CanGenerateEmbedding<TEmbedding>(embeddingGenerator);

    /// <inheritdoc />
    public override Task<IReadOnlyList<Embedding>> GenerateEmbeddingsAsync(VectorPropertyModel vectorProperty, IEnumerable<object?> values, CancellationToken cancellationToken)
        => vectorProperty.GenerateEmbeddingsCoreAsync<TEmbedding>(values, cancellationToken);

    /// <inheritdoc />
    public override Task<Embedding> GenerateEmbeddingAsync(VectorPropertyModel vectorProperty, object? value, CancellationToken cancellationToken)
        => vectorProperty.GenerateEmbeddingCoreAsync<TEmbedding>(value, cancellationToken);
}
