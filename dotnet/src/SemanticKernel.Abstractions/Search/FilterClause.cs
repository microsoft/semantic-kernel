// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Base class for filter clauses.
/// </summary>
/// <remarks>
/// The <see cref="FilterClause"/> is used to request that the underlying search service should
/// filter search results based on the specified criteria.
/// </remarks>
[Experimental("SKEXP0001")]
public class FilterClause
{
    /// <summary>
    /// The type of FilterClause.
    /// </summary>
    public FilterClauseType Type { get; private set; }

    /// <summary>
    /// Construct an instance of <see cref="FilterClause"/>
    /// </summary>
    /// <param name="type">The type of filter clause.</param>
    protected internal FilterClause(FilterClauseType type)
    {
        this.Type = type;
    }
}
