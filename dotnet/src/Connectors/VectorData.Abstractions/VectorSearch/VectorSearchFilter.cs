// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Provides filtering when doing vector searches.
/// Contains configuration for doing basic vector search filtering.
/// </summary>
/// <remarks>
/// A filter has a collection of <see cref="FilterClause"/> instances that can be used
/// to request that the underlying service filter the search results.
/// All clauses are combined with 'and'.
/// </remarks>
[Obsolete("Use VectorSearchOptions.Filter instead of VectorSearchOptions.OldFilter")]
public sealed class VectorSearchFilter
{
    /// <summary>The filter clauses to 'and' together.</summary>
    private readonly List<FilterClause> _filterClauses = [];

    /// <summary>Gets the default search filter.</summary>
    public static VectorSearchFilter Default { get; } = new VectorSearchFilter();

    /// <summary>
    /// The filter clauses to 'and' together.
    /// </summary>
    public IEnumerable<FilterClause> FilterClauses => this._filterClauses;

    /// <summary>
    /// Creates a new instance of <see cref="VectorSearchFilter"/>
    /// </summary>
    public VectorSearchFilter()
    {
    }

    /// <summary>
    /// Creates a new instance of <see cref="VectorSearchFilter"/> with the provided <see cref="FilterClause"/> instances.
    /// </summary>
    /// <param name="filterClauses">The <see cref="FilterClause"/> instances to use.</param>
    public VectorSearchFilter(IEnumerable<FilterClause> filterClauses)
    {
        if (filterClauses == null)
        {
            throw new ArgumentNullException(nameof(filterClauses));
        }

        this._filterClauses.AddRange(filterClauses);
    }

    /// <summary>
    /// Adds an 'equal to' clause to the filter options.
    /// </summary>
    /// <param name="propertyName">The name of the property to check against. Use the name of the property from your data model or as provided in the record definition.</param>
    /// <param name="value">The value that the property should match.</param>
    /// <returns>A <see cref="VectorSearchFilter"/> instance to allow fluent configuration.</returns>
    /// <remarks>
    /// This clause checks if a property is equal to a specific value.
    /// </remarks>
    public VectorSearchFilter EqualTo(string propertyName, object value)
    {
        this._filterClauses.Add(new EqualToFilterClause(propertyName, value));
        return this;
    }

    /// <summary>
    /// Adds an 'any tag equal to' clause to the filter options.
    /// </summary>
    /// <param name="propertyName">The name of the property consisting of a list of values to check against. Use the name of the property from your data model or as provided in the record definition.</param>
    /// <param name="value">The value that the list should contain.</param>
    /// <returns>A <see cref="VectorSearchFilter"/> instance to allow fluent configuration.</returns>
    /// <remarks>
    /// This clause checks if a property consisting of a list of values contains a specific value.
    /// </remarks>
    public VectorSearchFilter AnyTagEqualTo(string propertyName, string value)
    {
        this._filterClauses.Add(new AnyTagEqualToFilterClause(propertyName, value));
        return this;
    }
}
