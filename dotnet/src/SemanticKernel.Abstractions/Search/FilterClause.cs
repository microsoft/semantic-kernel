// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Base class for filter clauses.
/// </summary>
public class FilterClause
{
    /// <summary>
    /// The type of FilterClause.
    /// </summary>
    /// <remarks>
    /// The <see cref="FilterClause"/> is used to request that the underlying search service should
    /// filter search results based on the specified criteria.
    /// </remarks>
    public FilterClauseType Type { get; private set; }

    /// <summary>
    /// Construct an instance of <see cref="FilterClause"/>
    /// </summary>
    /// <param name="type">The type of filter clause.</param>
    protected FilterClause(FilterClauseType type)
    {
        this.Type = type;
    }
}
