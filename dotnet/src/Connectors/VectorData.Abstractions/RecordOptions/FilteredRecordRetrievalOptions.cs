// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for calling <see cref="VectorStoreCollection{TKey, TRecord}.GetAsync(Expression{Func{TRecord, bool}}, int, FilteredRecordRetrievalOptions{TRecord}, CancellationToken)"/>.
/// </summary>
/// <typeparam name="TRecord">Type of the record.</typeparam>
public sealed class FilteredRecordRetrievalOptions<TRecord>
{
    private int _skip = 0;

    /// <summary>
    /// Gets or sets the number of results to skip before returning results, that is, the index of the first result to return.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when the value is less than 0.</exception>
    public int Skip
    {
        get => this._skip;
        set
        {
            if (value < 0)
            {
                throw new ArgumentOutOfRangeException(nameof(value), "Skip must be greater than or equal to 0.");
            }

            this._skip = value;
        }
    }

    /// <summary>
    /// Gets or sets the data property to order by.
    /// </summary>
    /// <value>
    /// If not provided, the order of returned results is non-deterministic.
    /// </value>
    public Func<OrderByDefinition<TRecord>, OrderByDefinition<TRecord>>? OrderBy { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; set; }
}
