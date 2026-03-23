// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a read-only view of a vector property on a vector store record.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public interface IVectorPropertyModel : IPropertyModel
{
    /// <summary>
    /// Gets the number of dimensions that the vector has.
    /// </summary>
    int Dimensions { get; }

    /// <summary>
    /// Gets the kind of index to use.
    /// </summary>
    string? IndexKind { get; }

    /// <summary>
    /// Gets the distance function to use when comparing vectors.
    /// </summary>
    string? DistanceFunction { get; }

    /// <summary>
    /// Gets the type representing the embedding stored in the database.
    /// </summary>
    /// <remarks>
    /// This is guaranteed to be non-null after model building completes.
    /// If <see cref="EmbeddingGenerator"/> is set, this is the output embedding type;
    /// otherwise it is identical to <see cref="IPropertyModel.Type"/>.
    /// </remarks>
    Type EmbeddingType { get; }

    /// <summary>
    /// Gets the embedding generator to use for this property.
    /// </summary>
    IEmbeddingGenerator? EmbeddingGenerator { get; }

    /// <summary>
    /// Gets the <see cref="ProviderServices.EmbeddingGenerationDispatcher"/> that was resolved for this property during model building.
    /// </summary>
    EmbeddingGenerationDispatcher? EmbeddingGenerationDispatcher { get; }

    /// <summary>
    /// Generates embeddings for the given <paramref name="values"/>, using the configured <see cref="EmbeddingGenerationDispatcher"/>.
    /// </summary>
    Task<IReadOnlyList<Embedding>> GenerateEmbeddingsAsync(IEnumerable<object?> values, CancellationToken cancellationToken);

    /// <summary>
    /// Generates a single embedding for the given <paramref name="value"/>, using the configured <see cref="EmbeddingGenerationDispatcher"/>.
    /// </summary>
    Task<Embedding> GenerateEmbeddingAsync(object? value, CancellationToken cancellationToken);
}
