// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Represents a single search result from a vector search.
/// </summary>
/// <typeparam name="TRecord">The record data model to use for retrieving data from the store.</typeparam>
public sealed class VectorSearchResult<TRecord>
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
    /// Gets the record that was found by the search.
    /// </summary>
    public TRecord Record { get; }

    /// <summary>
    /// Gets the score of this result in relation to the search query.
    /// </summary>
    public double? Score { get; }
}
