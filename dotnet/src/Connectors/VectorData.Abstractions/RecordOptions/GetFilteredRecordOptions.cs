// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines options for filter search.
/// </summary>
/// <typeparam name="TRecord">Type of the record.</typeparam>
public sealed class GetFilteredRecordOptions<TRecord>
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
    /// If not provided, the order of returned results is non-deterministic.
    /// </value>
    public OrderByDefinition OrderBy { get; } = new();

    /// <summary>
    /// Gets or sets a value indicating whether to include vectors in the retrieval result.
    /// </summary>
    public bool IncludeVectors { get; init; } = false;

    /// <summary>
    /// A builder for sorting.
    /// </summary>
    // This type does not derive any collection in order to avoid Intellisense suggesting LINQ methods.
    public sealed class OrderByDefinition
    {
        private readonly List<SortInfo> _values = new();

        /// <summary>
        /// Gets the expressions to sort by.
        /// </summary>
        /// <remarks>This property is intended to be consumed by the connectors to retrieve the configuration.</remarks>
        public IReadOnlyList<SortInfo> Values => this._values;

        /// <summary>
        /// Creates an ascending sort.
        /// </summary>
        public OrderByDefinition Ascending(Expression<Func<TRecord, object?>> propertySelector)
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
        public OrderByDefinition Descending(Expression<Func<TRecord, object?>> propertySelector)
        {
            if (propertySelector is null)
            {
                throw new ArgumentNullException(nameof(propertySelector));
            }

            this._values.Add(new(propertySelector, false));
            return this;
        }

        /// <summary>
        /// Provides a way to define property ordering.
        /// </summary>
        /// <remarks>This class is intended to be consumed by the connectors to retrieve the configuration.</remarks>
        public sealed class SortInfo
        {
            internal SortInfo(Expression<Func<TRecord, object?>> propertySelector, bool isAscending)
            {
                this.PropertySelector = propertySelector;
                this.Ascending = isAscending;
            }

            /// <summary>
            /// The expression to select the property to sort by.
            /// </summary>
            public Expression<Func<TRecord, object?>> PropertySelector { get; }

            /// <summary>
            /// True if the sort is ascending; otherwise, false.
            /// </summary>
            public bool Ascending { get; }
        }
    }
}
