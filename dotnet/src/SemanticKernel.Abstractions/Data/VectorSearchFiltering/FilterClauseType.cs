// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Enum representing the type of filter clause.
/// </summary>
[Experimental("SKEXP0001")]
public enum FilterClauseType
{
    /// <summary>
    /// The filter clause is an equality clause.
    /// </summary>
    Equality,

    /// <summary>
    /// The filter clause that checks if a list of values contains a specific value.
    /// </summary>
    TagListContains
}
