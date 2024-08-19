// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains query information to use when searching a vector store using a vector.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class VectorizedSearchQuery<TVector> : VectorSearchQuery
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorizedSearchQuery{TVector}"/> class.
    /// </summary>
    /// <param name="vector">The vector to search the vector store with.</param>
    /// <param name="searchOptions">Options that control the behavior of the search.</param>
    /// <exception cref="ArgumentException">Thrown when <paramref name="vector"/> is not provided.</exception>
    internal VectorizedSearchQuery(TVector vector, VectorSearchOptions? searchOptions)
        : base(VectorSearchQueryType.VectorizedSearchQuery, searchOptions)
    {
        Verify.NotNull(vector);

        this.Vector = vector;
        this.SearchOptions = searchOptions;
    }

    /// <summary>
    /// Gets the vector to use when searching the vector store.
    /// </summary>
    public TVector Vector { get; }

    /// <summary>
    /// Gets the options that control the behavior of the search.
    /// </summary>
    public new VectorSearchOptions? SearchOptions { get; }
}
