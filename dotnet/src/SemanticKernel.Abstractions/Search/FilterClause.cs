// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Base class for filter clauses.
/// </summary>
public class FilterClause
{
    /// <summary>
    /// The type of FilterClause
    /// </summary>
    public FilterClauseType Type { get; private set; }

    /// <summary>
    /// Construct an instance of <see cref="FilterClause"/>
    /// </summary>
    /// <param name="type"></param>
    protected FilterClause(FilterClauseType type)
    {
        this.Type = type;
    }
}
