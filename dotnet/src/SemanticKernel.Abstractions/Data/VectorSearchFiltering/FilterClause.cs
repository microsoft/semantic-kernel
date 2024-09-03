// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Base class for filter clauses.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class FilterClause
{
    /// <summary>
    /// The type of FilterClause
    /// </summary>
    public FilterClauseType Type { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FilterClause"/> class.
    /// </summary>
    /// <param name="type">The type of filter clause.</param>
    internal FilterClause(FilterClauseType type)
    {
        this.Type = type;
    }
}
