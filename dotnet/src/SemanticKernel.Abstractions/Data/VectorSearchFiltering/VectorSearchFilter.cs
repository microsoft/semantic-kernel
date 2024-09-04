// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains configuration for doing basic vector search filtering.
/// All options are combined with and.
/// </summary>
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
    /// Add an equals clause to the filter options.
    /// </summary>
    /// <param name="field">Name of the field.</param>
    /// <param name="value">Value of the field</param>
    /// <returns><see cref="VectorSearchFilter"/> instance to allow fluent configuration.</returns>
    public VectorSearchFilter Equality(string field, object value)
    {
        this._filterClauses.Add(new EqualityFilterClause(field, value));
        return this;
    }

    /// <summary>
    /// Add a contains clause to the filter options.
    /// </summary>
    /// <param name="field">Name of the field consisting of a list of values.</param>
    /// <param name="value">Value that the list should contain.</param>
    /// <returns><see cref="VectorSearchFilter"/> instance to allow fluent configuration.</returns>
    public VectorSearchFilter TagListContains(string field, string value)
    {
        this._filterClauses.Add(new TagListContainsFilterClause(field, value));
        return this;
    }
}
