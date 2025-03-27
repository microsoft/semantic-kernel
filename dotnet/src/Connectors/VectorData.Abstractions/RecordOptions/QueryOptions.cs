// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for filter search.
/// </summary>
/// <typeparam name="TRecord">Type of the record.</typeparam>
// TRecord is not used as of today, but in the future we may use it to provide OrderBy property.
public sealed class QueryOptions<TRecord>
{
    private int _top = 0, _skip = 0;
    private bool _sortAscending = true;

    /// <summary>
    /// Gets or sets the mandatory search filter.
    /// </summary>
    public required Expression<Func<TRecord, bool>> Filter { get; init; }

    /// <summary>
    /// Gets or sets the maximum number of results to return.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when the value is less than 1.</exception>
    public required int Top
    {
        get => this._top;
        init
        {
            if (value < 1)
            {
                throw new ArgumentOutOfRangeException(nameof(value), "Top must be greater than or equal to 1.");
            }

            this._top = value;
        }
    }

    /// <summary>
    /// Gets or sets the number of results to skip before returning results, that is, the index of the first result to return.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">Thrown when the value is less than 0.</exception>
    public int Skip
    {
        get => this._skip;
        init
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
    /// If not provided the order of returned results can be non-deterministic.
    /// </value>
    public Expression<Func<TRecord, object?>>? OrderBy { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether to sort the results in ascending order.
    /// </summary>
    public bool SortAscending
    {
        get => this._sortAscending;
        init
        {
            if (this.OrderBy is null)
            {
                throw new InvalidOperationException("OrderBy must be set to sort the results.");
            }

            this._sortAscending = value;
        }
    }

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;
}
