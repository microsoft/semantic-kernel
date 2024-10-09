// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A single search result from a vector search.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
[Experimental("SKEXP0001")]
public sealed class VectorSearchResult<TRecord>
    where TRecord : class
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorSearchResult{TRecord}"/> class.
    /// </summary>
    /// <param name="record">The record that was found by the search.</param>
    /// <param name="score">The score of this result in relation to the search query.</param>
    public VectorSearchResult(TRecord record, double? score)
    {
        this.Record = record;
        this.Score = score;
    }

    /// <summary>
    /// The record that was found by the search.
    /// </summary>
    public TRecord Record { get; }

    /// <summary>
    /// The score of this result in relation to the search query.
    /// </summary>
    public double? Score { get; }
}
