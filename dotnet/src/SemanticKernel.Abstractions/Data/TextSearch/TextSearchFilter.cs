﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Used to provide filtering when using <see cref="ITextSearch"/>.
/// </summary>
/// <remarks>
/// A filter has a collection of <see cref="FilterClause"/>s that can be used by
/// an <see cref="ITextSearch"/> implementation to request that the underlying search
/// service filter the search results.
/// </remarks>
[Experimental("SKEXP0001")]
public sealed class TextSearchFilter
{
    /// <summary>
    /// The clauses to apply to the <see cref="TextSearchFilter" />
    /// </summary>
    public IEnumerable<FilterClause> FilterClauses => this._filterClauses;

    /// <summary>
    /// Add a equality clause to the filter options.
    /// </summary>
    /// <param name="fieldName">Name of the field.</param>
    /// <param name="value">Value of the field.</param>
    /// <returns>FilterOptions instance to allow fluent configuration.</returns>
    public TextSearchFilter Equality(string fieldName, object value)
    {
        this._filterClauses.Add(new EqualToFilterClause(fieldName, value));
        return this;
    }

    #region private
    private readonly List<FilterClause> _filterClauses = [];
    #endregion
}
