// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for filter search.
/// </summary>
/// <typeparam name="TRecord">Type of the record.</typeparam>
public sealed class FilterOptions<TRecord>
{
    private int _skip = 0;

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
    public SortDefinition Sort { get; } = new();

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;

    /// <summary>
    /// A builder for sorting.
    /// </summary>
    // This type does not derive any collection in order to avoid Intellisense suggesting LINQ methods.
    public sealed class SortDefinition
    {
        private readonly List<KeyValuePair<Expression<Func<TRecord, object?>>, bool>> _values = new();

        /// <summary>
        /// Gets the expressions to sort by.
        /// </summary>
        public IReadOnlyList<KeyValuePair<Expression<Func<TRecord, object?>>, bool>> Values => this._values;

        /// <summary>
        /// Creates an ascending sort.
        /// </summary>
        public SortDefinition Ascending(Expression<Func<TRecord, object?>> propertySelector)
        {
            if (propertySelector is null)
            {
                throw new ArgumentNullException(nameof(propertySelector));
            }

            this._values.Add(new(propertySelector, true));
            return this;
        }

        /// <summary>
        /// Creates a descending sort.
        /// </summary>
        public SortDefinition Descending(Expression<Func<TRecord, object?>> propertySelector)
        {
            if (propertySelector is null)
            {
                throw new ArgumentNullException(nameof(propertySelector));
            }

            this._values.Add(new(propertySelector, false));
            return this;
        }
    }
}
