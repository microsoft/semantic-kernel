// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Enum representing the types of filter clause.
/// </summary>
[Experimental("SKEXP0001")]
public enum FilterClauseType
{
    /// <summary>
    /// The filter clause is an equality clause.
    /// </summary>
    Equality,
}
