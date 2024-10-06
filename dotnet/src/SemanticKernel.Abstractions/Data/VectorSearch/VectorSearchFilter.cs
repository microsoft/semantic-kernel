// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Used to provide filtering when doing vector searches.
/// Contains configuration for doing basic vector search filtering.
/// </summary>
/// <remarks>
/// A filter has a collection of <see cref="FilterClause"/>s that can be used
/// to request that the underlying service filter the search results.
/// All clauses are combined with and.
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class VectorSearchFilter
{
    /// <summary>The filter clauses to and together.</summary>
    private readonly List<FilterClause> _filterClauses = [];

    /// <summary>Gets the default search filter.</summary>
    public static VectorSearchFilter Default { get; } = new VectorSearchFilter();

    /// <summary>
    /// The filter clauses to and together.
    /// </summary>
    public IEnumerable<FilterClause> FilterClauses => this._filterClauses;

    /// <summary>
    /// Create an instance of <see cref="VectorSearchFilter"/>
    /// </summary>
    public VectorSearchFilter()
    {
    }

    /// <summary>
    /// Create an instance of <see cref="VectorSearchFilter"/> with the provided <see cref="FilterClause"/>s.
    /// <param name="filterClauses">The <see cref="FilterClause"/> instances to use</param>
    /// </summary>
    internal VectorSearchFilter(IEnumerable<FilterClause> filterClauses)
    {
        Verify.NotNull(filterClauses, nameof(filterClauses));

        this._filterClauses.AddRange(filterClauses);
    }

    /// <summary>
    /// Add an equal to clause to the filter options.
    /// </summary>
    /// <param name="propertyName">Name of the property to check against. Use the name of the property from your data model or as provided in the record definition.</param>
    /// <param name="value">Value that the property should match.</param>
    /// <returns><see cref="VectorSearchFilter"/> instance to allow fluent configuration.</returns>
    /// <remarks>
    /// This clause will check if a property is equal to a specific value.
    /// </remarks>
    public VectorSearchFilter EqualTo(string propertyName, object value)
    {
        this._filterClauses.Add(new EqualToFilterClause(propertyName, value));
        return this;
    }

    /// <summary>
    /// Add an any tag equal to clause to the filter options.
    /// </summary>
    /// <param name="propertyName">Name of the property consisting of a list of values to check against. Use the name of the property from your data model or as provided in the record definition.</param>
    /// <param name="value">Value that the list should contain.</param>
    /// <returns><see cref="VectorSearchFilter"/> instance to allow fluent configuration.</returns>
    /// <remarks>
    /// This clause will check if a property consisting of a list of values contains a specific value.
    /// </remarks>
    public VectorSearchFilter AnyTagEqualTo(string propertyName, string value)
    {
        this._filterClauses.Add(new AnyTagEqualToFilterClause(propertyName, value));
        return this;
    }
}
