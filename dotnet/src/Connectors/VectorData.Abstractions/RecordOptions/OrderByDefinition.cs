// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq.Expressions;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A builder for sorting.
/// </summary>
// This type does not derive any collection in order to avoid Intellisense suggesting LINQ methods.
public sealed class OrderByDefinition<TRecord>
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
    public OrderByDefinition<TRecord> Ascending(Expression<Func<TRecord, object?>> propertySelector)
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
    public OrderByDefinition<TRecord> Descending(Expression<Func<TRecord, object?>> propertySelector)
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
