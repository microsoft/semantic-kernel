// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for vector search via <see cref="VectorStoreCollection{TKey, TRecord}.SearchAsync{TInput}(TInput, int, VectorSearchOptions{TRecord}, CancellationToken)"/>.
/// </summary>
public class VectorSearchOptions<TRecord>
{
    private int _skip = 0;

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    [Obsolete("Use Filter instead")]
    public VectorSearchFilter? OldFilter { get; set; }

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    public Expression<Func<TRecord, bool>>? Filter { get; set; }

    /// <summary>
    /// Gets or sets the vector property to search on.
    /// Only needs to be set when the collection has multiple vector properties.
    /// </summary>
    /// <remarks>
    /// If this property isn't set provided, <see cref="VectorStoreCollection{TKey, TRecord}.SearchAsync{TInput}(TInput, int, VectorSearchOptions{TRecord}, CancellationToken)"/> checks if there is a vector property to use by default, and
    /// throws an exception if either none or multiple exist.
    /// </remarks>
    public Expression<Func<TRecord, object?>>? VectorProperty { get; set; }

    /// <summary>
    /// Gets or sets the number of results to skip before returning results, that is, the index of the first result to return.
    /// </summary>
    /// <exception cref="ArgumentOutOfRangeException">The value is less than 0.</exception>
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
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; set; }
}
