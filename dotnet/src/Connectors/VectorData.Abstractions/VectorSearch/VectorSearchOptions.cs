// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for vector search.
/// </summary>
public class VectorSearchOptions<TRecord>
{
    private int _skip = 0;

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    [Obsolete("Use Filter instead")]
    public VectorSearchFilter? OldFilter { get; init; }

    /// <summary>
    /// Gets or sets a search filter to use before doing the vector search.
    /// </summary>
    public Expression<Func<TRecord, bool>>? Filter { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector property to search on.
    /// Use the name of the vector property from your data model or as provided in the record definition.
    /// </summary>
    /// <value>
    /// If not provided will check if there is a vector property to use by default, and
    /// will throw if either none or multiple exist.
    /// </value>
    [Obsolete("Use VectorProperty instead")]
    public string? VectorPropertyName { get; init; }

    /// <summary>
    /// Gets or sets the vector property to search on.
    /// Only needs to be set when the collection has multiple vector properties.
    /// </summary>
    /// <value>
    /// If not provided will check if there is a vector property to use by default, and
    /// will throw if either none or multiple exist.
    /// </value>
    public Expression<Func<TRecord, object?>>? VectorProperty { get; init; }

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
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;

    /// <summary>
    /// Gets or sets a value indicating whether the total count should be included in the results.
    /// </summary>
    /// <value>
    /// The default value is false.
    /// </value>
    /// <remarks>
    /// Not all vector search implementations support this option, in which case the total
    /// count will be null even if requested via this option.
    /// </remarks>
    [Obsolete("Total count is no longer included in the results.", error: true)]
    public bool IncludeTotalCount { get; init; } = false;
}
